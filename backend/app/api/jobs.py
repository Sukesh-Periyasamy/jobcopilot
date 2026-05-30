"""Jobs endpoints for JobCopilot API.

Provides paginated job listings, recent jobs, full-text search,
and company-specific job queries.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.database.repository import JobsRepository
from app.models.job import FilterCriteria
from app.models.schemas import JobResponse, PaginatedJobsResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _job_record_to_response(record) -> JobResponse:
    """Convert a JobRecord dataclass to a JobResponse Pydantic model."""
    return JobResponse(
        title=record.title,
        company=record.company,
        location=record.location,
        source=record.source,
        source_type=record.source_type,
        source_platform=record.source_platform,
        job_url=record.job_url,
        description=record.description,
        job_type=record.job_type,
        salary=record.salary,
        date_posted=record.date_posted,
        search_term=record.search_term,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/jobs", response_model=PaginatedJobsResponse)
def get_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    source: Optional[str] = Query(None, description="Filter by source"),
    location: Optional[str] = Query(None, description="Filter by location"),
    company: Optional[str] = Query(None, description="Filter by company"),
    keyword: Optional[str] = Query(None, description="Filter by keyword"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    search_term: Optional[str] = Query(None, description="Filter by search term"),
    source_type: Optional[str] = Query(None, description="Filter by source type (jobspy or jobhive)"),
    source_platform: Optional[str] = Query(None, description="Filter by source platform"),
) -> PaginatedJobsResponse:
    """Get paginated jobs with optional filters."""
    try:
        repo = JobsRepository()
        filters = FilterCriteria(
            source=source,
            location=location,
            company=company,
            keyword=keyword,
            job_type=job_type,
            date_from=date_from,
            date_to=date_to,
            search_term=search_term,
            source_type=source_type,
            source_platform=source_platform,
        )
        result = repo.get_jobs(filters, page=page, page_size=page_size)
        jobs = [_job_record_to_response(j) for j in result.jobs]
        return PaginatedJobsResponse(
            jobs=jobs,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
        )
    except Exception as e:
        logger.error("Error fetching jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch jobs")


@router.get("/jobs/recent", response_model=list[JobResponse])
def get_recent_jobs() -> list[JobResponse]:
    """Get the top 10 most recently posted jobs."""
    try:
        repo = JobsRepository()
        records = repo.get_recent_jobs(limit=10)
        return [_job_record_to_response(r) for r in records]
    except Exception as e:
        logger.error("Error fetching recent jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch recent jobs")


@router.get("/jobs/search", response_model=PaginatedJobsResponse)
def search_jobs(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> PaginatedJobsResponse:
    """Full-text search across job title and description."""
    try:
        repo = JobsRepository()
        result = repo.search_jobs(q, page=page, page_size=page_size)
        jobs = [_job_record_to_response(j) for j in result.jobs]
        return PaginatedJobsResponse(
            jobs=jobs,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
        )
    except Exception as e:
        logger.error("Error searching jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to search jobs")


@router.get("/jobs/smart-search")
def smart_search_jobs(
    q: str = Query(..., description="Search query (supports synonyms and weighted scoring)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> dict:
    """Smart search with weighted scoring, synonym expansion, and suggestions.

    Searches across title (10x), company (8x), location (4x), description (3x).
    Expands queries with synonyms (e.g., 'biomedical' also searches 'medical device').
    Returns suggestions when no results found.
    """
    try:
        from app.services.smart_search import SmartSearchService

        service = SmartSearchService()
        return service.search(q, page=page, page_size=page_size)
    except Exception as e:
        logger.error("Error in smart search: %s", e)
        raise HTTPException(status_code=500, detail="Failed to search jobs")


@router.get("/jobs/company/{name}", response_model=list[JobResponse])
def get_jobs_by_company(name: str) -> list[JobResponse]:
    """Get all jobs from a specific company."""
    try:
        repo = JobsRepository()
        records = repo.get_jobs_by_company(name)
        return [_job_record_to_response(r) for r in records]
    except Exception as e:
        logger.error("Error fetching jobs for company '%s': %s", name, e)
        raise HTTPException(status_code=500, detail="Failed to fetch company jobs")


@router.get("/companies/{name}/insights")
def get_company_insights(name: str) -> dict:
    """Get intelligence about a specific company.

    Returns total jobs, India jobs, research jobs, medical device jobs,
    latest posting date, and job type breakdown.
    """
    try:
        import re
        from datetime import datetime, timedelta, timezone

        from app.database.connection import get_database
        from app.services.constants import COLLECTIONS, INTERNSHIP_KEYWORDS, RESEARCH_INSTITUTIONS

        db = get_database()
        jobs_col = db["jobs"]

        # Find all jobs from this company (case-insensitive)
        query = {"company": {"$regex": f"^{re.escape(name)}$", "$options": "i"}}
        all_jobs = list(jobs_col.find(query, {"_id": 0}).sort("date_posted", -1))

        if not all_jobs:
            # Try substring match
            query = {"company": {"$regex": re.escape(name), "$options": "i"}}
            all_jobs = list(jobs_col.find(query, {"_id": 0}).sort("date_posted", -1))

        total = len(all_jobs)

        # India jobs
        india_cities = ["india", "bangalore", "bengaluru", "hyderabad", "chennai", "pune", "mumbai", "delhi", "noida", "gurugram", "gurgaon"]
        india_jobs = [j for j in all_jobs if any(c in j.get("location", "").lower() for c in india_cities)]

        # Research jobs
        research_jobs = [j for j in all_jobs if any(
            inst.lower() in j.get("description", "").lower() or inst.lower() in j.get("title", "").lower()
            for inst in ["research", "scientist", "R&D"]
        )]

        # Medical device jobs
        medtech_keywords = []
        for c in COLLECTIONS:
            if c.name in ("Medical Technology", "Medical Devices", "Biomedical Engineering"):
                medtech_keywords.extend(c.keywords)
        medtech_jobs = [j for j in all_jobs if any(
            kw.lower() in f"{j.get('title', '')} {j.get('description', '')}".lower()
            for kw in medtech_keywords
        )]

        # Internships
        intern_jobs = [j for j in all_jobs if any(
            kw.lower() in j.get("title", "").lower() for kw in INTERNSHIP_KEYWORDS
        )]

        # Latest posting
        latest = all_jobs[0].get("date_posted", "") if all_jobs else ""
        days_since = ""
        if latest:
            try:
                posted = datetime.strptime(latest, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                days = (datetime.now(timezone.utc) - posted).days
                days_since = f"{days} days ago"
            except (ValueError, TypeError):
                pass

        # Recent jobs (last 5)
        recent = [{
            "title": j.get("title", ""),
            "location": j.get("location", ""),
            "date_posted": j.get("date_posted", ""),
            "job_url": j.get("job_url", ""),
        } for j in all_jobs[:5]]

        return {
            "company": name,
            "total_jobs": total,
            "india_jobs": len(india_jobs),
            "research_jobs": len(research_jobs),
            "medtech_jobs": len(medtech_jobs),
            "internships": len(intern_jobs),
            "latest_posting": latest,
            "days_since_latest": days_since,
            "recent_jobs": recent,
        }
    except Exception as e:
        logger.error("Error fetching company insights for '%s': %s", name, e)
        raise HTTPException(status_code=500, detail="Failed to fetch company insights")
