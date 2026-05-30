"""Internships endpoints for JobCopilot API.

Provides paginated internship listings with optional keyword filtering.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.services.internship_tracker import InternshipTracker

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/internships")
def get_internships(
    keyword: str | None = Query(default=None, description="Specific internship keyword to filter by"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=50, ge=1, le=100, description="Number of results per page"),
) -> dict:
    """Return paginated internship listings, optionally filtered by keyword.

    If keyword is provided, only internships matching that specific keyword
    in the title are returned. If omitted, all internship-type positions
    (matching any of the 15 predefined keywords) are returned.
    """
    try:
        tracker = InternshipTracker()
        return tracker.get_internships(keyword=keyword, page=page, page_size=page_size)
    except Exception as e:
        logger.error("Error fetching internships: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch internships")
