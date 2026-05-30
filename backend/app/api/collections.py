"""Collections endpoints for JobCopilot API.

Provides read-only access to job collections, their metadata,
and paginated job listings within each collection.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.database.connection import get_database
from app.models.schemas import (
    CollectionDetail,
    CollectionSummary,
    PaginatedJobsResponse,
    JobResponse,
)
from app.services.collection_engine import CollectionEngine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/collections")
def get_collections() -> list[CollectionSummary]:
    """Return all collections with their job counts."""
    try:
        db = get_database()
        engine = CollectionEngine(db)
        results = engine.get_all_collections()
        return [CollectionSummary(**item) for item in results]
    except Exception as e:
        logger.error("Error fetching collections: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch collections")


@router.get("/collections/{name}")
def get_collection(name: str) -> CollectionDetail:
    """Return collection metadata (name, keywords, job_count) or 404."""
    try:
        db = get_database()
        engine = CollectionEngine(db)
        result = engine.get_collection(name)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{name}' not found",
            )
        return CollectionDetail(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching collection '%s': %s", name, e)
        raise HTTPException(status_code=500, detail="Failed to fetch collection")


@router.get("/collections/{name}/jobs")
def get_collection_jobs(
    name: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> PaginatedJobsResponse:
    """Return paginated jobs belonging to the specified collection."""
    try:
        db = get_database()
        engine = CollectionEngine(db)
        result = engine.get_collection_jobs(name, page=page, page_size=page_size)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{name}' not found",
            )
        jobs = [
            JobResponse(
                title=job.title,
                company=job.company,
                location=job.location,
                source=job.source,
                source_type=job.source_type,
                source_platform=job.source_platform,
                job_url=job.job_url,
                description=job.description,
                job_type=job.job_type,
                salary=job.salary,
                date_posted=job.date_posted,
                search_term=job.search_term,
                created_at=job.created_at,
                updated_at=job.updated_at,
            )
            for job in result.jobs
        ]
        return PaginatedJobsResponse(
            jobs=jobs,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching jobs for collection '%s': %s", name, e)
        raise HTTPException(status_code=500, detail="Failed to fetch collection jobs")
