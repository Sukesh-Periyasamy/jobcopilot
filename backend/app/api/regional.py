"""Regional Radar endpoints for South India Fresher jobs.

Provides location-based job filtering for Tamil Nadu, Bangalore,
with fresher scoring and district-level granularity.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.services.regional_radar import RegionalRadarService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/regional/tamilnadu")
def get_tamil_nadu() -> dict:
    """Return jobs in Tamil Nadu with fresher scoring and district breakdown."""
    try:
        service = RegionalRadarService()
        return service.get_tamil_nadu()
    except Exception as e:
        logger.error("Error fetching Tamil Nadu jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch regional jobs")


@router.get("/regional/bangalore")
def get_bangalore() -> dict:
    """Return jobs in Bangalore/Karnataka with fresher scoring."""
    try:
        service = RegionalRadarService()
        return service.get_bangalore()
    except Exception as e:
        logger.error("Error fetching Bangalore jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch regional jobs")


@router.get("/regional/freshers")
def get_freshers() -> dict:
    """Return fresher-friendly jobs across South India."""
    try:
        service = RegionalRadarService()
        return service.get_freshers()
    except Exception as e:
        logger.error("Error fetching fresher jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch fresher jobs")


@router.get("/regional/research")
def get_regional_research() -> dict:
    """Return research positions in South India."""
    try:
        service = RegionalRadarService()
        return service.get_research()
    except Exception as e:
        logger.error("Error fetching research jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch research jobs")


@router.get("/regional/internships")
def get_regional_internships() -> dict:
    """Return internships in South India."""
    try:
        service = RegionalRadarService()
        return service.get_internships()
    except Exception as e:
        logger.error("Error fetching internships: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch internships")


@router.get("/regional/core-engineering")
def get_core_engineering() -> dict:
    """Return core engineering jobs in South India."""
    try:
        service = RegionalRadarService()
        return service.get_core_engineering()
    except Exception as e:
        logger.error("Error fetching core engineering jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch engineering jobs")


@router.get("/regional/district/{district}")
def get_district(district: str) -> dict:
    """Return jobs in a specific district/city."""
    try:
        service = RegionalRadarService()
        return service.get_district(district)
    except Exception as e:
        logger.error("Error fetching district jobs for '%s': %s", district, e)
        raise HTTPException(status_code=500, detail="Failed to fetch district jobs")


@router.get("/freshers/bangalore")
def get_freshers_bangalore() -> dict:
    """Return fresher jobs specifically in Bangalore."""
    try:
        service = RegionalRadarService()
        result = service.get_bangalore()
        # Filter to only fresher-friendly
        fresher_jobs = [j for j in result.get("jobs", []) if j.get("fresher_score", 0) >= 10]
        return {
            "jobs": fresher_jobs,
            "stats": {"count": len(fresher_jobs), "region": "Bangalore"},
        }
    except Exception as e:
        logger.error("Error fetching Bangalore freshers: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch fresher jobs")


@router.get("/freshers/tamilnadu")
def get_freshers_tamilnadu() -> dict:
    """Return fresher jobs specifically in Tamil Nadu."""
    try:
        service = RegionalRadarService()
        result = service.get_tamil_nadu()
        fresher_jobs = [j for j in result.get("jobs", []) if j.get("fresher_score", 0) >= 10]
        return {
            "jobs": fresher_jobs,
            "stats": {"count": len(fresher_jobs), "region": "Tamil Nadu"},
        }
    except Exception as e:
        logger.error("Error fetching Tamil Nadu freshers: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch fresher jobs")


@router.get("/freshers/medical-tech")
def get_freshers_medical_tech() -> dict:
    """Return fresher medical technology jobs in India."""
    try:
        import re
        from app.database.connection import get_database
        from app.services.constants import COLLECTIONS

        db = get_database()
        jobs_col = db["jobs"]

        # Medical tech keywords
        medtech_keywords = []
        for c in COLLECTIONS:
            if c.name in ("Medical Technology", "Medical Devices", "Biomedical Engineering", "Diagnostics and Biosensors", "Healthcare AI"):
                medtech_keywords.extend(c.keywords)

        # Build query: medtech keywords + India location
        keyword_conditions = []
        for kw in medtech_keywords:
            keyword_conditions.append({"title": {"$regex": re.escape(kw), "$options": "i"}})
            keyword_conditions.append({"description": {"$regex": re.escape(kw), "$options": "i"}})

        india_locations = ["india", "bangalore", "bengaluru", "chennai", "hyderabad", "pune", "mumbai", "delhi", "gurgaon", "remote"]
        loc_conditions = [{"location": {"$regex": re.escape(loc), "$options": "i"}} for loc in india_locations]

        query = {"$and": [{"$or": keyword_conditions}, {"$or": loc_conditions}]}
        cursor = jobs_col.find(query, {"_id": 0}).sort("date_posted", -1).limit(50)
        jobs = list(cursor)

        # Score for freshers
        service = RegionalRadarService()
        scored = []
        for job in jobs:
            score = service._fresher_score(job)
            scored.append({
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "job_url": job.get("job_url", ""),
                "date_posted": job.get("date_posted", ""),
                "source_platform": job.get("source_platform", ""),
                "fresher_score": score,
            })

        scored.sort(key=lambda j: j["fresher_score"], reverse=True)

        return {
            "jobs": scored,
            "stats": {"count": len(scored), "category": "Medical Technology Freshers India"},
        }
    except Exception as e:
        logger.error("Error fetching medical tech freshers: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch medical tech fresher jobs")


@router.get("/freshers/research")
def get_freshers_research() -> dict:
    """Return fresher research positions (JRF/SRF/RA) in India."""
    try:
        import re
        from app.database.connection import get_database

        db = get_database()
        jobs_col = db["jobs"]

        research_keywords = ["jrf", "srf", "project associate", "project assistant",
                           "research associate", "research assistant", "research fellow",
                           "young professional"]

        conditions = [{"title": {"$regex": re.escape(kw), "$options": "i"}} for kw in research_keywords]

        india_locations = ["india", "bangalore", "bengaluru", "chennai", "hyderabad", "pune", "mumbai", "delhi", "remote"]
        loc_conditions = [{"location": {"$regex": re.escape(loc), "$options": "i"}} for loc in india_locations]

        query = {"$and": [{"$or": conditions}, {"$or": loc_conditions}]}
        cursor = jobs_col.find(query, {"_id": 0}).sort("date_posted", -1).limit(50)
        jobs = list(cursor)

        service = RegionalRadarService()
        scored = []
        for job in jobs:
            score = service._fresher_score(job)
            scored.append({
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "job_url": job.get("job_url", ""),
                "date_posted": job.get("date_posted", ""),
                "source_platform": job.get("source_platform", ""),
                "fresher_score": score,
            })

        scored.sort(key=lambda j: j["fresher_score"], reverse=True)

        return {
            "jobs": scored,
            "stats": {"count": len(scored), "category": "Research Freshers India"},
        }
    except Exception as e:
        logger.error("Error fetching research freshers: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch research fresher jobs")


@router.get("/freshers/today")
def get_freshers_today() -> dict:
    """Return fresh fresher jobs posted in the last 72 hours, India only.

    Rules: posted <= 3 days, India location, fresher_score >= 15, not applied.
    This is the daily action feed for freshers.
    """
    try:
        from datetime import datetime, timedelta, timezone

        from app.database.connection import get_database
        from app.database.repository import JobsRepository

        db = get_database()
        jobs_col = db["jobs"]

        # Last 72 hours
        three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")

        # India locations
        india_locations = [
            "india", "bangalore", "bengaluru", "chennai", "coimbatore",
            "hyderabad", "pune", "mumbai", "delhi", "noida", "gurgaon",
            "gurugram", "remote",
        ]
        loc_conditions = [
            {"location": {"$regex": loc, "$options": "i"}}
            for loc in india_locations
        ]

        query = {
            "$and": [
                {"date_posted": {"$gte": three_days_ago}},
                {"$or": loc_conditions},
            ]
        }

        cursor = jobs_col.find(query, {"_id": 0}).sort("date_posted", -1).limit(100)
        jobs = list(cursor)

        # Get applied URLs to exclude
        repo = JobsRepository()
        applied_urls = {j.get("job_url") for j in repo.get_applied_jobs()}

        # Score and filter
        service = RegionalRadarService()
        results = []
        for job in jobs:
            if job.get("job_url") in applied_urls:
                continue

            score = service._fresher_score(job)
            if score >= 15:
                results.append({
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "job_url": job.get("job_url", ""),
                    "date_posted": job.get("date_posted", ""),
                    "source_platform": job.get("source_platform", ""),
                    "fresher_score": score,
                })

        results.sort(key=lambda j: j["fresher_score"], reverse=True)

        return {
            "jobs": results[:50],
            "stats": {
                "count": len(results),
                "period": "last 72 hours",
                "location": "India",
            },
        }
    except Exception as e:
        logger.error("Error fetching today's freshers: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch today's fresher jobs")


@router.get("/daily-targets")
def get_daily_targets() -> dict:
    """Return the top 20 daily application targets.

    Rules:
    - India only (or Remote)
    - Posted <= 7 days
    - Career Radar score >= 25
    - Fresher friendly (fresher_score >= 0, no senior penalty)
    - Not already applied
    - Not already saved

    This is the single most useful endpoint — your daily application queue.
    """
    try:
        from datetime import datetime, timedelta, timezone

        from app.database.connection import get_database
        from app.database.repository import JobsRepository
        from app.services.career_radar import CareerRadarService

        db = get_database()
        jobs_col = db["jobs"]

        # Last 7 days
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

        # India locations
        india_locations = [
            "india", "bangalore", "bengaluru", "chennai", "coimbatore",
            "hyderabad", "pune", "mumbai", "delhi", "noida", "gurgaon",
            "gurugram", "remote", "erode", "salem", "madurai", "trichy",
            "hosur", "vellore",
        ]
        loc_conditions = [
            {"location": {"$regex": loc, "$options": "i"}}
            for loc in india_locations
        ]

        query = {
            "$and": [
                {"date_posted": {"$gte": seven_days_ago}},
                {"$or": loc_conditions},
            ]
        }

        cursor = jobs_col.find(query, {"_id": 0}).sort("date_posted", -1).limit(200)
        india_recent_jobs = list(cursor)

        # Get exclusions
        repo = JobsRepository()
        applied_urls = {j.get("job_url") for j in repo.get_applied_jobs()}
        saved_urls = {j.get("job_url") for j in repo.get_saved_jobs()}
        excluded = applied_urls | saved_urls

        # Score with career radar
        radar = CareerRadarService()
        watchlist_companies = radar._get_watchlist_companies()

        # Also get fresher scoring
        service = RegionalRadarService()

        targets = []
        for job in india_recent_jobs:
            if job.get("job_url") in excluded:
                continue

            # Career radar score
            career_score, collections = radar._score_job(job, watchlist_companies)
            if career_score < 25:
                continue

            # Fresher score (bonus, not filter)
            fresher_score = service._fresher_score(job)

            # Combined score
            combined_score = career_score + max(fresher_score, 0)

            targets.append({
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "job_url": job.get("job_url", ""),
                "date_posted": job.get("date_posted", ""),
                "source_platform": job.get("source_platform", ""),
                "career_score": career_score,
                "fresher_score": fresher_score,
                "combined_score": combined_score,
                "collections": collections,
            })

        # Sort by combined score
        targets.sort(key=lambda j: j["combined_score"], reverse=True)

        return {
            "daily_targets": targets[:20],
            "stats": {
                "india_recent_jobs": len(india_recent_jobs),
                "qualified_targets": len(targets),
                "returned": min(len(targets), 20),
                "period": "last 7 days",
                "min_career_score": 25,
            },
        }
    except Exception as e:
        logger.error("Error computing daily targets: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute daily targets")
