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


@router.get("/career-radar/action-list")
def get_career_radar_action_list() -> dict:
    """Return the daily application queue.

    Filters: score >= 25, posted <= 30 days, not already applied/saved.
    Broader window for a fuller action list.
    """
    try:
        service = CareerRadarService()
        return service.get_action_list()
    except Exception as e:
        logger.error("Error computing career radar action list: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute career radar")


@router.get("/career-radar/india")
def get_career_radar_india() -> dict:
    """Return India-focused career radar matches.

    Filters for jobs in Indian cities and remote India positions.
    """
    try:
        service = CareerRadarService()
        return service.get_india_feed()
    except Exception as e:
        logger.error("Error computing India feed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute India feed")


@router.get("/watchlist-alerts")
def get_watchlist_alerts() -> dict:
    """Return new jobs from watchlist companies posted in the last 7 days.

    Groups results by company with job counts.
    """
    try:
        from datetime import datetime, timedelta, timezone

        from app.database.connection import get_database
        from app.database.repository import JobsRepository

        repo = JobsRepository()
        watchlist = repo.get_watchlist()
        watchlist_companies = {entry["company_name"].lower(): entry for entry in watchlist}

        db = get_database()
        jobs_col = db["jobs"]

        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

        alerts = []
        for company_lower, entry in watchlist_companies.items():
            query = {
                "company": {"$regex": f"^{company_lower}$", "$options": "i"},
                "date_posted": {"$gte": seven_days_ago},
            }
            jobs = list(jobs_col.find(query, {"_id": 0}).sort("date_posted", -1).limit(10))
            if jobs:
                alerts.append({
                    "company": entry["company_name"],
                    "tier": entry.get("tier", "tier3"),
                    "new_jobs_count": len(jobs),
                    "jobs": [
                        {
                            "title": j.get("title", ""),
                            "location": j.get("location", ""),
                            "date_posted": j.get("date_posted", ""),
                            "job_url": j.get("job_url", ""),
                        }
                        for j in jobs
                    ],
                })

        # Sort by tier (tier1 first) then by job count
        tier_order = {"tier1": 0, "tier2": 1, "tier3": 2}
        alerts.sort(key=lambda a: (tier_order.get(a["tier"], 2), -a["new_jobs_count"]))

        return {
            "alerts": alerts,
            "total_companies_hiring": len(alerts),
            "total_new_jobs": sum(a["new_jobs_count"] for a in alerts),
        }
    except Exception as e:
        logger.error("Error computing watchlist alerts: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute watchlist alerts")


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
