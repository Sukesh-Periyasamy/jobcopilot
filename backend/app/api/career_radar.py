"""Career Radar endpoint for JobCopilot API.

Provides personalized job scoring and ranking based on the user's
career profile weights.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.services.career_radar import CareerRadarService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/career-radar")
def get_career_radar() -> dict:
    """Return personalized career radar with scored and ranked jobs.

    Returns categorized matches: top_matches, research_matches,
    internships, watchlist_matches, remote_matches, and stats.
    """
    try:
        service = CareerRadarService()
        return service.get_career_radar()
    except Exception as e:
        logger.error("Error computing career radar: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute career radar")
