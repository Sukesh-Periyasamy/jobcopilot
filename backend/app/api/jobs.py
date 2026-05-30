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
