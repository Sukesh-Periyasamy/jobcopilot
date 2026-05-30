"""Research endpoints for JobCopilot API.

Provides endpoints for browsing research institution job opportunities.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.services.research_tracker import ResearchTracker

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/research/recent")
def get_recent_research() -> list[dict]:
    """Return the 10 most recently posted research opportunities."""
    try:
        tracker = ResearchTracker()
        return tracker.get_recent_research(limit=10)
    except Exception as e:
        logger.error("Error fetching recent research: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch recent research")


@router.get("/research")
def get_research_jobs(
    institution: str | None = Query(default=None),
    page: int = Query(default=1),
    page_size: int = Query(default=50),
) -> dict:
    """Return paginated research jobs, optionally filtered by institution."""
    try:
        tracker = ResearchTracker()
        return tracker.get_research_jobs(institution, page, page_size)
    except Exception as e:
        logger.error("Error fetching research jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch research jobs")
