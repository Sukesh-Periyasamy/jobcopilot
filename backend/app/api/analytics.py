"""Analytics endpoint for JobCopilot API.

Provides aggregate statistics computed from the jobs collection
using MongoDB aggregation pipelines.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.services.analytics_engine import AnalyticsEngine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/analytics")
def get_analytics() -> dict:
    """Return all computed analytics metrics.

    Returns a dict with keys: jobs_per_day, jobs_per_company,
    jobs_per_source, jobs_per_platform, jobs_per_location,
    jobs_per_collection, top_hiring_companies, top_locations,
    top_ats_platforms, internship_vs_fulltime, research_vs_industry.
    """
    try:
        engine = AnalyticsEngine()
        return engine.compute_analytics()
    except Exception as e:
        logger.error("Error computing analytics: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute analytics")
