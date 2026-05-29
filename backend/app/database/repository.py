"""MongoDB repository for JobCopilot Engine.

Handles all CRUD operations for jobs, saved_jobs, applied_jobs,
company_watchlist, and scrape_history collections.
"""

from __future__ import annotations

import logging
import math
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from pymongo import ASCENDING, TEXT, IndexModel
from pymongo.errors import BulkWriteError

from app.database.connection import get_database
from app.models.job import (
    BulkInsertResult,
    FilterCriteria,
    JobRecord,
    PaginatedResult,
    ScrapeHistoryEntry,
)
from app.services.filter_engine import build_query

logger = logging.getLogger(__name__)

DEFAULT_WATCHLIST = [
    "Siemens Healthineers",
    "GE HealthCare",
    "Philips",
    "Medtronic",
    "Abbott",
    "Dozee",
]


class JobsRepository:
    """Repository class handling all MongoDB operations for JobCopilot."""

    def __init__(self) -> None:
        """Connect to MongoDB and ensure indexes exist."""
        self._db = get_database()
        self._jobs = self._db["jobs"]
        self._saved_jobs = self._db["saved_jobs"]
        self._applied_jobs = self._db["applied_jobs"]
        self._watchlist = self._db["company_watchlist"]
        self._scrape_history = self._db["scrape_history"]

        self.ensure_indexes()
        self._seed_default_watchlist()

    def ensure_indexes(self) -> None:
        """Create indexes on the jobs collection if they do not already exist.

        Indexes:
        - job_url: unique
        - date_posted: ascending
        - source: ascending
        - company: ascending
        - text index on title and description for full-text search
        """
        self._jobs.create_indexes([
            IndexModel([("job_url", ASCENDING)], unique=True),
            IndexModel([("date_posted", ASCENDING)]),
            IndexModel([("source", ASCENDING)]),
            IndexModel([("company", ASCENDING)]),
            IndexModel([("title", TEXT), ("description", TEXT)]),
        ])

        # Unique index on saved_jobs.job_url
        self._saved_jobs.create_index("job_url", unique=True)

        # Unique index on applied_jobs.job_url
        self._applied_jobs.create_index("job_url", unique=True)

        # Unique index on watchlist company_name
        self._watchlist.create_index("company_name", unique=True)

        logger.info("Database indexes ensured.")

    def _seed_default_watchlist(self) -> None:
        """Seed the default watchlist companies if the collection is empty."""
        if self._watchlist.count_documents({}) == 0:
            docs = [{"company_name": name} for name in DEFAULT_WATCHLIST]
            self._watchlist.insert_many(docs, ordered=False)
            logger.info("Seeded default watchlist with %d companies.", len(docs))

    def bulk_insert(self, records: list[JobRecord]) -> BulkInsertResult:
        """Insert job records with ordered=False, skipping duplicates.

        Args:
            records: List of JobRecord instances to insert.

        Returns:
            BulkInsertResult with inserted_count, duplicates_skipped, and new_jobs.
        """
        if not records:
            return BulkInsertResult()

        documents = [asdict(r) for r in records]
        inserted_count = 0
        duplicates_skipped = 0

        try:
            result = self._jobs.insert_many(documents, ordered=False)
            inserted_count = len(result.inserted_ids)
        except BulkWriteError as e:
            inserted_count = e.details.get("nInserted", 0)
            write_errors = e.details.get("writeErrors", [])
            # Duplicate key errors have code 11000
            duplicates_skipped = sum(
                1 for err in write_errors if err.get("code") == 11000
            )

        # The new jobs are those that were successfully inserted
        new_jobs = records[:inserted_count] if inserted_count > 0 else []

        logger.info(
            "Bulk insert complete: %d inserted, %d duplicates skipped.",
            inserted_count,
            duplicates_skipped,
        )

        return BulkInsertResult(
            inserted_count=inserted_count,
            duplicates_skipped=duplicates_skipped,
            new_jobs=new_jobs,
        )

    def record_scrape_history(self, entry: ScrapeHistoryEntry) -> None:
        """Write a scrape run record to the scrape_history collection.

        Args:
            entry: ScrapeHistoryEntry with timestamp, jobs_found,
                   duplicates_skipped, and errors.
        """
        self._scrape_history.insert_one(asdict(entry))
        logger.info("Recorded scrape history: %d found, %d duplicates.",
                    entry.jobs_found, entry.duplicates_skipped)

    def get_jobs(
        self, filters: FilterCriteria, page: int = 1, page_size: int = 50
    ) -> PaginatedResult:
        """Query jobs with filters and pagination.

        Args:
            filters: FilterCriteria with optional filter fields.
            page: Page number (1-indexed).
            page_size: Number of records per page.

        Returns:
            PaginatedResult with jobs, total, page, page_size, total_pages.
        """
        query = build_query(filters)
        total = self._jobs.count_documents(query)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        skip = (page - 1) * page_size
        cursor = (
            self._jobs.find(query)
            .sort("date_posted", -1)
            .skip(skip)
            .limit(page_size)
        )

        jobs = [self._doc_to_job_record(doc) for doc in cursor]

        return PaginatedResult(
            jobs=jobs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_recent_jobs(self, limit: int = 10) -> list[JobRecord]:
        """Return most recently posted jobs, ordered by date_posted desc.

        Args:
            limit: Maximum number of jobs to return.

        Returns:
            List of JobRecord instances.
        """
        cursor = self._jobs.find().sort("date_posted", -1).limit(limit)
        return [self._doc_to_job_record(doc) for doc in cursor]

    def search_jobs(
        self, query: str, page: int = 1, page_size: int = 50
    ) -> PaginatedResult:
        """Full-text search across title and description fields.

        Args:
            query: Search query string.
            page: Page number (1-indexed).
            page_size: Number of records per page.

        Returns:
            PaginatedResult with matching jobs.
        """
        search_filter = {"$text": {"$search": query}}
        total = self._jobs.count_documents(search_filter)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        skip = (page - 1) * page_size
        cursor = (
            self._jobs.find(search_filter)
            .sort("date_posted", -1)
            .skip(skip)
            .limit(page_size)
        )

        jobs = [self._doc_to_job_record(doc) for doc in cursor]

        return PaginatedResult(
            jobs=jobs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_jobs_by_company(self, company: str) -> list[JobRecord]:
        """Return all jobs from a specific company (case-insensitive).

        Args:
            company: Company name to search for.

        Returns:
            List of JobRecord instances.
        """
        query = {"company": {"$regex": f"^{company}$", "$options": "i"}}
        cursor = self._jobs.find(query).sort("date_posted", -1)
        return [self._doc_to_job_record(doc) for doc in cursor]

    def save_job(self, job_data: dict) -> bool:
        """Store a job in the saved_jobs collection.

        Args:
            job_data: Dictionary with job fields (job_url, title, company,
                      location, source, date_posted).

        Returns:
            True if saved successfully, False if already saved.
        """
        job_data["date_saved"] = datetime.now(timezone.utc).isoformat()
        try:
            self._saved_jobs.insert_one(job_data)
            logger.info("Job saved: %s", job_data.get("job_url"))
            return True
        except Exception:
            logger.info("Job already saved: %s", job_data.get("job_url"))
            return False

    def get_saved_jobs(self) -> list[dict]:
        """Return all saved jobs from the saved_jobs collection.

        Returns:
            List of saved job dictionaries.
        """
        cursor = self._saved_jobs.find({}, {"_id": 0}).sort("date_saved", -1)
        return list(cursor)

    def remove_saved_job(self, job_url: str) -> bool:
        """Remove a job from the saved_jobs collection.

        Args:
            job_url: URL of the job to remove.

        Returns:
            True if removed, False if not found.
        """
        result = self._saved_jobs.delete_one({"job_url": job_url})
        removed = result.deleted_count > 0
        if removed:
            logger.info("Removed saved job: %s", job_url)
        return removed

    def add_applied_job(self, job_data: dict, status: str = "Interested") -> None:
        """Add a job to the applied_jobs collection with initial status.

        Args:
            job_data: Dictionary with job fields (job_url, title, company, location).
            status: Initial application status (default: "Interested").
        """
        now = datetime.now(timezone.utc).isoformat()
        job_data["status"] = status
        job_data["date_applied"] = now
        job_data["updated_at"] = now

        try:
            self._applied_jobs.insert_one(job_data)
            logger.info("Applied job added: %s with status %s",
                        job_data.get("job_url"), status)
        except Exception:
            logger.info("Job already in applied list: %s", job_data.get("job_url"))

    def get_applied_jobs(self) -> list[dict]:
        """Return all applied jobs from the applied_jobs collection.

        Returns:
            List of applied job dictionaries.
        """
        cursor = self._applied_jobs.find({}, {"_id": 0}).sort("date_applied", -1)
        return list(cursor)

    def update_application_status(self, job_url: str, status: str) -> None:
        """Update the status of an applied job.

        Args:
            job_url: URL of the job to update.
            status: New application status.
        """
        self._applied_jobs.update_one(
            {"job_url": job_url},
            {"$set": {
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        logger.info("Updated application status for %s to %s", job_url, status)

    def get_watchlist(self) -> list[str]:
        """Return all company names from the company_watchlist collection.

        Returns:
            List of company name strings.
        """
        docs = self._watchlist.find({}, {"company_name": 1, "_id": 0})
        return [doc["company_name"] for doc in docs]

    def add_to_watchlist(self, company: str) -> bool:
        """Add a company to the watchlist.

        Validates:
        - Company name must be 1–100 characters.
        - Watchlist must have fewer than 50 entries.

        Args:
            company: Company name to add.

        Returns:
            True if added successfully, False if validation fails or duplicate.
        """
        # Validate name length
        if not company or len(company) > 100:
            logger.warning("Watchlist add rejected: name length invalid (%d chars).",
                           len(company) if company else 0)
            return False

        # Validate max entries
        current_count = self._watchlist.count_documents({})
        if current_count >= 50:
            logger.warning("Watchlist add rejected: max 50 entries reached.")
            return False

        try:
            self._watchlist.insert_one({"company_name": company})
            logger.info("Added to watchlist: %s", company)
            return True
        except Exception:
            logger.info("Company already in watchlist: %s", company)
            return False

    def remove_from_watchlist(self, company: str) -> bool:
        """Remove a company from the watchlist.

        Args:
            company: Company name to remove.

        Returns:
            True if removed, False if not found.
        """
        result = self._watchlist.delete_one({"company_name": company})
        removed = result.deleted_count > 0
        if removed:
            logger.info("Removed from watchlist: %s", company)
        return removed

    def get_stats(self) -> dict:
        """Return dashboard summary metrics.

        Returns:
            Dictionary with total_jobs, jobs_today, jobs_this_week,
            saved_jobs, applied_jobs, companies_tracked.
        """
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")

        # Calculate start of current week (Monday)
        days_since_monday = now.weekday()
        week_start = (now - timedelta(days=days_since_monday)).strftime("%Y-%m-%d")

        total_jobs = self._jobs.count_documents({})
        jobs_today = self._jobs.count_documents({"date_posted": today_str})
        jobs_this_week = self._jobs.count_documents(
            {"date_posted": {"$gte": week_start}}
        )
        saved_jobs = self._saved_jobs.count_documents({})
        applied_jobs = self._applied_jobs.count_documents({})
        companies_tracked = self._watchlist.count_documents({})

        return {
            "total_jobs": total_jobs,
            "jobs_today": jobs_today,
            "jobs_this_week": jobs_this_week,
            "saved_jobs": saved_jobs,
            "applied_jobs": applied_jobs,
            "companies_tracked": companies_tracked,
        }

    @staticmethod
    def _doc_to_job_record(doc: dict) -> JobRecord:
        """Convert a MongoDB document to a JobRecord instance.

        Args:
            doc: MongoDB document dictionary.

        Returns:
            JobRecord instance.
        """
        return JobRecord(
            title=doc.get("title", ""),
            company=doc.get("company", ""),
            location=doc.get("location", ""),
            source=doc.get("source", ""),
            job_url=doc.get("job_url", ""),
            description=doc.get("description", ""),
            job_type=doc.get("job_type", ""),
            salary=doc.get("salary", ""),
            date_posted=doc.get("date_posted", ""),
            search_term=doc.get("search_term", ""),
            created_at=doc.get("created_at", ""),
            updated_at=doc.get("updated_at", ""),
        )
