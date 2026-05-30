"""Career Radar endpoints for JobCopilot API.

Provides personalized job scoring and ranking based on the user's
career profile weights, with noise filtering and priority levels.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.services.career_radar import CareerRadarService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/career-radar/top")
def get_career_radar_top() -> dict:
    """Return high-priority actionable matches only.

    Filters: score >= 25, posted <= 14 days, not already applied/saved.
    This is the daily action list.
    """
    try:
        service = CareerRadarService()
        return service.get_top_priority()
    except Exception as e:
        logger.error("Error computing career radar top: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute career radar")


@router.get("/career-radar")
def get_career_radar() -> dict:
    """Return personalized career radar with scored and ranked jobs.

    Applies minimum score filtering (>= 15) and negative keyword
    penalties to reduce noise. Returns categorized matches.
    """
    try:
        service = CareerRadarService()
        return service.get_career_radar()
    except Exception as e:
        logger.error("Error computing career radar: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute career radar")
