"""Stats endpoint for JobCopilot API.

Provides dashboard summary metrics.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.database.repository import JobsRepository
from app.models.schemas import StatsResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
def get_stats() -> StatsResponse:
    """Return dashboard summary metrics."""
    try:
        repo = JobsRepository()
        stats = repo.get_stats()
        return StatsResponse(
            total_jobs=stats["total_jobs"],
            jobs_today=stats["jobs_today"],
            jobs_this_week=stats["jobs_this_week"],
            saved_jobs=stats["saved_jobs"],
            applied_jobs=stats["applied_jobs"],
            companies_tracked=stats["companies_tracked"],
        )
    except Exception as e:
        logger.error("Error fetching stats: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch stats")
