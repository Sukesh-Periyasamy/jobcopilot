"""Collection Engine for Career Opportunity Radar.

Classifies jobs into named collections at query time using MongoDB
regex queries — no data duplication. Each collection is defined by
a set of keywords matched case-insensitively against job title and
description fields.
"""

from __future__ import annotations

import math
import re

from pymongo.database import Database

from app.models.job import JobRecord, PaginatedResult
from app.services.constants import COLLECTIONS, CollectionDefinition


class CollectionEngine:
    """Classifies and retrieves jobs by collection at query time.

    Instantiated with a database reference. Uses the COLLECTIONS
    constant to define available collections and their keywords.
    """

    def __init__(self, db: Database) -> None:
        """Initialize with a MongoDB database reference.

        Args:
            db: A pymongo Database instance.
        """
        self._db = db
        self._jobs = db["jobs"]

    def get_all_collections(self) -> list[dict]:
        """Return all collection names with their job counts.

        Iterates over all defined collections and counts matching
        jobs for each using keyword-based regex queries.

        Returns:
            List of dicts with 'name' and 'job_count' keys.
        """
        results = []
        for collection_def in COLLECTIONS:
            query = self._build_collection_query(collection_def.keywords)
            count = self._jobs.count_documents(query)
            results.append({"name": collection_def.name, "job_count": count})
        return results

    def get_collection(self, name: str) -> dict | None:
        """Return collection metadata by name, or None if not found.

        Args:
            name: The collection name to look up.

        Returns:
            Dict with 'name', 'keywords', and 'job_count' keys,
            or None if no collection matches the given name.
        """
        collection_def = self._find_collection_def(name)
        if collection_def is None:
            return None

        query = self._build_collection_query(collection_def.keywords)
        count = self._jobs.count_documents(query)
        return {
            "name": collection_def.name,
            "keywords": collection_def.keywords,
            "job_count": count,
        }

    def get_collection_jobs(
        self, name: str, page: int = 1, page_size: int = 50
    ) -> PaginatedResult | None:
        """Return paginated jobs matching the collection's keywords.

        Jobs are sorted by date_posted descending.

        Args:
            name: The collection name to query jobs for.
            page: Page number (1-indexed).
            page_size: Number of records per page.

        Returns:
            PaginatedResult with matching jobs, or None if collection not found.
        """
        collection_def = self._find_collection_def(name)
        if collection_def is None:
            return None

        query = self._build_collection_query(collection_def.keywords)
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

    def _build_collection_query(self, keywords: list[str]) -> dict:
        """Build a MongoDB $or query with case-insensitive regex.

        Each keyword generates two conditions: one regex match on
        "title" and one on "description", both case-insensitive.

        Args:
            keywords: List of keywords to match against.

        Returns:
            MongoDB query dict with $or conditions.
        """
        conditions = []
        for keyword in keywords:
            escaped = re.escape(keyword)
            conditions.append({"title": {"$regex": escaped, "$options": "i"}})
            conditions.append({"description": {"$regex": escaped, "$options": "i"}})
        return {"$or": conditions}

    def _find_collection_def(self, name: str) -> CollectionDefinition | None:
        """Find a collection definition by name.

        Args:
            name: The collection name to search for.

        Returns:
            The matching CollectionDefinition, or None if not found.
        """
        for collection_def in COLLECTIONS:
            if collection_def.name == name:
                return collection_def
        return None

    @staticmethod
    def _doc_to_job_record(doc: dict) -> JobRecord:
        """Convert a MongoDB document to a JobRecord instance.

        Handles backward compatibility for legacy documents missing
        source_type and source_platform fields.

        Args:
            doc: MongoDB document dictionary.

        Returns:
            JobRecord instance.
        """
        source_type = doc.get("source_type", "")
        if not source_type:
            source_type = "jobspy"

        source_platform = doc.get("source_platform", "")
        if not source_platform:
            source_platform = doc.get("source", "").strip().lower()

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
            source_type=source_type,
            source_platform=source_platform,
            created_at=doc.get("created_at", ""),
            updated_at=doc.get("updated_at", ""),
        )
