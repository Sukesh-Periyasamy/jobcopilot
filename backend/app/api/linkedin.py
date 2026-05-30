"""LinkedIn-focused endpoints for JobCopilot API.

Provides LinkedIn-specific job views, company hiring analytics,
and MedTech-focused LinkedIn radar.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.database.connection import get_database

logger = logging.getLogger(__name__)

router = APIRouter()

# MedTech companies to track
MEDTECH_COMPANIES = [
    "Abbott", "Philips", "GE HealthCare", "Siemens Healthineers",
    "Stryker", "Medtronic", "Roche", "Dexcom", "Clario",
    "Boston Scientific", "Johnson & Johnson", "Becton Dickinson",
    "Fujifilm", "Niramai", "Dozee", "Skanray",
]

# MedTech keywords for filtering
MEDTECH_KEYWORDS = [
    "biomedical", "medical device", "clinical research",
    "research associate", "project associate", "healthcare ai",
    "quality engineer", "regulatory affairs", "diagnostics",
    "biosensor", "validation engineer", "r&d engineer",
]


@router.get("/linkedin/jobs")
def get_linkedin_jobs(
    keyword: str | None = Query(None, description="Filter by keyword in title"),
    location: str | None = Query(None, description="Filter by location"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> dict:
    """Return jobs sourced from LinkedIn with optional filters."""
    try:
        db = get_database()
        jobs_col = db["jobs"]

        # Base query: LinkedIn source
        query_conditions = [
            {"$or": [
                {"source_platform": "linkedin"},
                {"source": {"$regex": "linkedin", "$options": "i"}},
            ]}
        ]

        # Optional keyword filter
        if keyword:
            escaped = re.escape(keyword)
            query_conditions.append({
                "$or": [
                    {"title": {"$regex": escaped, "$options": "i"}},
                    {"description": {"$regex": escaped, "$options": "i"}},
                ]
            })

        # Optional location filter
        if location:
            query_conditions.append(
                {"location": {"$regex": re.escape(location), "$options": "i"}}
            )

        query = {"$and": query_conditions}
        total = jobs_col.count_documents(query)

        skip = (page - 1) * page_size
        cursor = jobs_col.find(query, {"_id": 0}).sort("date_posted", -1).skip(skip).limit(page_size)
        jobs = list(cursor)

        return {
            "jobs": [_format_linkedin_job(j) for j in jobs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "source": "linkedin",
        }
    except Exception as e:
        logger.error("Error fetching LinkedIn jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch LinkedIn jobs")


@router.get("/linkedin/medtech")
def get_linkedin_medtech() -> dict:
    """Return LinkedIn MedTech jobs — Biomedical, Clinical, Research, Devices."""
    try:
        db = get_database()
        jobs_col = db["jobs"]

        # LinkedIn + MedTech keywords
        kw_conditions = []
        for kw in MEDTECH_KEYWORDS:
            kw_conditions.append({"title": {"$regex": re.escape(kw), "$options": "i"}})
            kw_conditions.append({"description": {"$regex": re.escape(kw), "$options": "i"}})

        query = {
            "$and": [
                {"$or": [
                    {"source_platform": "linkedin"},
                    {"source": {"$regex": "linkedin", "$options": "i"}},
                ]},
                {"$or": kw_conditions},
            ]
        }

        cursor = jobs_col.find(query, {"_id": 0}).sort("date_posted", -1).limit(50)
        jobs = list(cursor)

        return {
            "jobs": [_format_linkedin_job(j) for j in jobs],
            "total": len(jobs),
            "category": "LinkedIn MedTech",
        }
    except Exception as e:
        logger.error("Error fetching LinkedIn MedTech jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch LinkedIn MedTech jobs")


@router.get("/linkedin/company/{company}")
def get_linkedin_company_insights(company: str) -> dict:
    """Return hiring analytics for a specific company from LinkedIn data."""
    try:
        db = get_database()
        jobs_col = db["jobs"]

        # All jobs from this company
        query = {"company": {"$regex": re.escape(company), "$options": "i"}}
        all_jobs = list(jobs_col.find(query, {"_id": 0}).sort("date_posted", -1))

        total = len(all_jobs)

        # India jobs
        india_locs = ["india", "bangalore", "bengaluru", "chennai", "hyderabad", "pune", "mumbai", "delhi", "gurgaon", "noida"]
        india_jobs = [j for j in all_jobs if any(loc in j.get("location", "").lower() for loc in india_locs)]

        # Fresher jobs
        fresher_kws = ["associate", "junior", "graduate", "trainee", "intern", "fresher", "entry"]
        fresher_jobs = [j for j in all_jobs if any(kw in j.get("title", "").lower() for kw in fresher_kws)]

        # Research roles
        research_kws = ["research", "scientist", "r&d", "jrf", "srf"]
        research_jobs = [j for j in all_jobs if any(kw in j.get("title", "").lower() for kw in research_kws)]

        # Medical device roles
        medtech_kws = ["medical device", "biomedical", "clinical", "diagnostics", "quality", "regulatory"]
        medtech_jobs = [j for j in all_jobs if any(kw in f"{j.get('title', '')} {j.get('description', '')}".lower() for kw in medtech_kws)]

        # Recent (last 7 days)
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
        recent_jobs = [j for j in all_jobs if j.get("date_posted", "") >= seven_days_ago]

        return {
            "company": company,
            "total_jobs": total,
            "india_jobs": len(india_jobs),
            "fresher_jobs": len(fresher_jobs),
            "research_roles": len(research_jobs),
            "medtech_roles": len(medtech_jobs),
            "recent_jobs_7d": len(recent_jobs),
            "latest_jobs": [_format_linkedin_job(j) for j in all_jobs[:10]],
        }
    except Exception as e:
        logger.error("Error fetching company insights for '%s': %s", company, e)
        raise HTTPException(status_code=500, detail="Failed to fetch company insights")


@router.get("/linkedin/hiring-now")
def get_hiring_now() -> dict:
    """Return companies actively hiring this week from LinkedIn data."""
    try:
        db = get_database()
        jobs_col = db["jobs"]

        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

        # Aggregate companies with recent postings
        pipeline = [
            {"$match": {"date_posted": {"$gte": seven_days_ago}}},
            {"$group": {"_id": "$company", "count": {"$sum": 1}, "latest": {"$max": "$date_posted"}}},
            {"$sort": {"count": -1}},
            {"$limit": 20},
        ]

        results = list(jobs_col.aggregate(pipeline))

        companies = [
            {"company": doc["_id"], "new_jobs": doc["count"], "latest_posting": doc["latest"]}
            for doc in results if doc["_id"]
        ]

        # Check which are MedTech companies
        medtech_lower = [c.lower() for c in MEDTECH_COMPANIES]
        for company in companies:
            company["is_medtech"] = any(mt in company["company"].lower() for mt in medtech_lower)

        return {
            "companies_hiring": companies,
            "total_companies": len(companies),
            "period": "last 7 days",
        }
    except Exception as e:
        logger.error("Error fetching hiring-now data: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch hiring data")


def _format_linkedin_job(job: dict) -> dict:
    """Format a job for LinkedIn-specific response."""
    # Extract skills from description (simple keyword extraction)
    description = job.get("description", "").lower()
    skills = []
    skill_keywords = [
        "python", "java", "matlab", "r", "sql", "machine learning",
        "deep learning", "tensorflow", "pytorch", "medical devices",
        "quality systems", "iso 13485", "fda", "gmp", "biomedical",
        "signal processing", "embedded", "iot", "docker", "aws",
        "clinical trials", "regulatory", "validation", "verification",
    ]
    for skill in skill_keywords:
        if skill in description:
            skills.append(skill.title())

    return {
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("location", ""),
        "job_url": job.get("job_url", ""),
        "date_posted": job.get("date_posted", ""),
        "source_platform": job.get("source_platform", ""),
        "salary": job.get("salary", ""),
        "job_type": job.get("job_type", ""),
        "skills": skills[:8],
        "description_preview": job.get("description", "")[:200],
    }


@router.get("/linkedin/skills/{job_url:path}")
def get_job_skills(job_url: str) -> dict:
    """Extract and return skills for a specific job."""
    try:
        from app.services.job_enrichment import extract_skills, categorize_job

        db = get_database()
        jobs_col = db["jobs"]

        job = jobs_col.find_one({"job_url": job_url}, {"_id": 0})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        description = job.get("description", "")
        title = job.get("title", "")

        skills = extract_skills(description)
        category = categorize_job(title, description)

        return {
            "title": title,
            "company": job.get("company", ""),
            "skills": skills,
            "category": category,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error extracting skills: %s", e)
        raise HTTPException(status_code=500, detail="Failed to extract skills")


@router.get("/linkedin/categories")
def get_job_categories() -> dict:
    """Return job count by category across all LinkedIn jobs."""
    try:
        from app.services.job_enrichment import categorize_job

        db = get_database()
        jobs_col = db["jobs"]

        # Get LinkedIn jobs
        query = {"$or": [
            {"source_platform": "linkedin"},
            {"source": {"$regex": "linkedin", "$options": "i"}},
        ]}
        cursor = jobs_col.find(query, {"_id": 0, "title": 1, "description": 1}).limit(500)

        category_counts: dict[str, int] = {}
        for job in cursor:
            cat = categorize_job(job.get("title", ""), job.get("description", ""))
            category_counts[cat] = category_counts.get(cat, 0) + 1

        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "categories": [{"name": k, "count": v} for k, v in sorted_categories],
            "total": sum(category_counts.values()),
        }
    except Exception as e:
        logger.error("Error computing categories: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute categories")


@router.get("/scraper/status")
def get_scraper_status() -> dict:
    """Return the latest scraper run status."""
    try:
        db = get_database()
        history_col = db["scrape_history"]

        # Get latest run
        latest = history_col.find_one({}, sort=[("timestamp", -1)])

        # Count jobs by source
        jobs_col = db["jobs"]
        total_jobs = jobs_col.count_documents({})
        linkedin_jobs = jobs_col.count_documents({"source_platform": "linkedin"})
        jobhive_jobs = jobs_col.count_documents({"source_type": "jobhive"})
        research_jobs = jobs_col.count_documents({"source_type": "research_scraper"})

        return {
            "total_jobs": total_jobs,
            "by_source": {
                "linkedin": linkedin_jobs,
                "jobhive": jobhive_jobs,
                "research": research_jobs,
                "other": total_jobs - linkedin_jobs - jobhive_jobs - research_jobs,
            },
            "last_run": {
                "jobs_found": latest.get("jobs_found", 0) if latest else 0,
                "duplicates_skipped": latest.get("duplicates_skipped", 0) if latest else 0,
                "timestamp": latest.get("timestamp", "") if latest else "Never",
            },
        }
    except Exception as e:
        logger.error("Error fetching scraper status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch scraper status")
