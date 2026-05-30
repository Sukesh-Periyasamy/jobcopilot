"""Opportunities endpoint for JobCopilot API.

Provides a categorized opportunity feed with six categories:
top_companies, new_companies, remote_jobs, internships,
research_roles, healthcare_roles.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.services.opportunity_feed import OpportunityFeedService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/opportunities")
def get_opportunities() -> dict:
    """Return categorized opportunity feed.

    Returns a dict with six keys, each containing up to 10 entries:
    top_companies, new_companies, remote_jobs, internships,
    research_roles, healthcare_roles.
    """
    try:
        service = OpportunityFeedService()
        return service.get_feed()
    except Exception as e:
        logger.error("Error fetching opportunities feed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch opportunities feed")
