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


@router.get("/career-radar/fresh")
def get_career_radar_fresh() -> dict:
    """Return fresh high-scoring jobs posted in the last 3 days.

    Filters: posted <= 3 days, score >= 20, excludes applied/saved.
    This is the instant action feed.
    """
    try:
        service = CareerRadarService()
        return service.get_fresh_radar()
    except Exception as e:
        logger.error("Error computing fresh radar: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute fresh radar")


@router.get("/career-radar/apply-now")
def get_apply_now() -> dict:
    """Return top 10 jobs to apply to right now.

    Rules: India only, posted <= 14 days, score >= 70, not applied.
    This is your daily application queue — the single most actionable endpoint.
    """
    try:
        from datetime import datetime, timedelta, timezone

        from app.database.connection import get_database
        from app.database.repository import JobsRepository

        service = CareerRadarService()
        scored_jobs, total_count = service._score_all_jobs()

        # Get exclusions
        repo = JobsRepository()
        applied_urls = {j.get("job_url") for j in repo.get_applied_jobs()}
        excluded = applied_urls

        now = datetime.now(timezone.utc)
        india_cities = [
            "india", "bangalore", "bengaluru", "chennai", "coimbatore",
            "hyderabad", "pune", "mumbai", "delhi", "noida", "gurgaon",
            "gurugram", "remote",
        ]

        apply_now = []
        for job in scored_jobs:
            if job.get("_score", 0) < 70:
                break  # Sorted desc

            # India only
            location = job.get("location", "").lower()
            if not any(city in location for city in india_cities):
                continue

            # Posted <= 14 days
            date_posted = job.get("date_posted", "")
            if date_posted:
                try:
                    posted = datetime.strptime(date_posted, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if (now - posted).days > 14:
                        continue
                except (ValueError, TypeError):
                    continue

            # Not applied
            if job.get("job_url") in excluded:
                continue

            apply_now.append(service._format_job(job))
            if len(apply_now) >= 10:
                break

        return {
            "apply_now": apply_now,
            "stats": {
                "total_scored": total_count,
                "apply_now_count": len(apply_now),
            },
        }
    except Exception as e:
        logger.error("Error computing apply-now: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute apply-now list")


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


@router.get("/research-radar")
def get_research_radar() -> dict:
    """Return research fellowship opportunities.

    Filters for JRF, SRF, Project Associate, Research Associate
    from Indian research institutions. Scored with biomedical profile.
    """
    try:
        service = CareerRadarService()
        return service.get_research_radar()
    except Exception as e:
        logger.error("Error computing research radar: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute research radar")


@router.get("/career-radar/profile/biomedical")
def get_biomedical_profile() -> dict:
    """Return career radar scored with biomedical research profile.

    Tuned for SERS, biosensors, diagnostics, medical devices research.
    """
    try:
        service = CareerRadarService()
        return service.get_biomedical_profile()
    except Exception as e:
        logger.error("Error computing biomedical profile: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute biomedical profile")
