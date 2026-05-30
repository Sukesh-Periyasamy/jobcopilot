"""South India Fresher Radar service.

Provides location-based job filtering for Tamil Nadu and Bangalore,
with fresher scoring and district-level granularity.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from app.database.connection import get_database
from app.services.constants import COLLECTIONS, INTERNSHIP_KEYWORDS, RESEARCH_INSTITUTIONS

logger = logging.getLogger(__name__)

# Tamil Nadu districts and cities
TAMIL_NADU_LOCATIONS = [
    "chennai", "coimbatore", "salem", "erode", "madurai", "trichy",
    "tiruchirappalli", "hosur", "vellore", "thanjavur", "tirunelveli",
    "kanchipuram", "pondicherry", "puducherry", "tamil nadu",
]

# Karnataka / Bangalore region
BANGALORE_LOCATIONS = [
    "bangalore", "bengaluru", "mysuru", "mysore", "mangalore",
    "mangaluru", "hubli", "belgaum", "belagavi", "karnataka",
]

# All South India
SOUTH_INDIA_LOCATIONS = TAMIL_NADU_LOCATIONS + BANGALORE_LOCATIONS + [
    "hyderabad", "telangana", "kerala", "kochi", "thiruvananthapuram",
    "andhra pradesh", "visakhapatnam", "vijayawada",
]

# Fresher keywords (positive)
FRESHER_KEYWORDS = [
    "fresher", "graduate", "entry level", "junior", "associate",
    "trainee", "get", "gat", "graduate engineer trainee",
    "apprentice", "intern", "project associate", "jrf",
    "research assistant", "0-2 years", "0-1 years",
    "young professional", "project assistant",
]

# Seniority keywords (negative for freshers)
SENIOR_KEYWORDS_REGIONAL = [
    "senior", "lead", "principal", "manager", "director",
    "head", "vp", "chief", "architect", "staff",
]

# South India research institutions
SOUTH_INDIA_INSTITUTIONS = [
    "IIT Madras", "IISc", "NIMHANS", "C-CAMP", "CSIR-CLRI",
    "SCTIMST", "Anna University", "VIT", "SRM", "BITS Pilani",
    "IIT Hyderabad", "IIIT Hyderabad", "CMC Vellore",
]

# Core engineering keywords
CORE_ENGINEERING_KEYWORDS = [
    "biomedical", "medical device", "embedded", "firmware",
    "electronics", "mechanical", "instrumentation", "vlsi",
    "signal processing", "control systems", "robotics",
    "manufacturing", "quality", "production",
]

MAX_RESULTS = 50


class RegionalRadarService:
    """South India Fresher Radar with location and fresher scoring."""

    def get_tamil_nadu(self) -> dict:
        """Return jobs in Tamil Nadu with fresher scoring."""
        return self._get_regional_jobs(TAMIL_NADU_LOCATIONS, "Tamil Nadu")

    def get_bangalore(self) -> dict:
        """Return jobs in Bangalore/Karnataka with fresher scoring."""
        return self._get_regional_jobs(BANGALORE_LOCATIONS, "Bangalore")

    def get_freshers(self) -> dict:
        """Return fresher-friendly jobs across South India."""
        db = get_database()
        jobs_col = db["jobs"]

        # Get all South India jobs
        location_query = self._build_location_query(SOUTH_INDIA_LOCATIONS)
        cursor = jobs_col.find(location_query, {"_id": 0}).limit(500)
        all_jobs = list(cursor)

        # Score and filter for freshers
        scored = []
        for job in all_jobs:
            score = self._fresher_score(job)
            if score >= 10:  # Only fresher-friendly jobs
                job["_fresher_score"] = score
                scored.append(job)

        scored.sort(key=lambda j: j["_fresher_score"], reverse=True)

        return {
            "freshers": [self._format_job(j) for j in scored[:MAX_RESULTS]],
            "stats": {
                "total_south_india": len(all_jobs),
                "fresher_friendly": len(scored),
            },
        }

    def get_research(self) -> dict:
        """Return research positions in South India."""
        db = get_database()
        jobs_col = db["jobs"]

        # Research keywords in title
        research_keywords = [
            "jrf", "srf", "project associate", "project assistant",
            "research associate", "research scientist", "research fellow",
            "research engineer", "postdoc",
        ]

        conditions = []
        for kw in research_keywords:
            conditions.append({"title": {"$regex": re.escape(kw), "$options": "i"}})

        # Also match South India institutions
        for inst in SOUTH_INDIA_INSTITUTIONS:
            conditions.append({"company": {"$regex": re.escape(inst), "$options": "i"}})
            conditions.append({"description": {"$regex": re.escape(inst), "$options": "i"}})

        query = {"$or": conditions}
        cursor = jobs_col.find(query, {"_id": 0}).sort("date_posted", -1).limit(100)
        jobs = list(cursor)

        # Filter for South India location (optional — some research jobs are remote)
        south_india_jobs = []
        other_jobs = []
        for job in jobs:
            loc = job.get("location", "").lower()
            if any(city in loc for city in SOUTH_INDIA_LOCATIONS) or "india" in loc or "remote" in loc:
                south_india_jobs.append(job)
            else:
                other_jobs.append(job)

        # Score
        scored = []
        for job in south_india_jobs + other_jobs:
            score = self._fresher_score(job)
            job["_fresher_score"] = max(score, 1)
            scored.append(job)

        return {
            "research_jobs": [self._format_job(j) for j in scored[:MAX_RESULTS]],
            "stats": {
                "total_research": len(jobs),
                "south_india_research": len(south_india_jobs),
            },
        }

    def get_internships(self) -> dict:
        """Return internships in South India."""
        db = get_database()
        jobs_col = db["jobs"]

        # Internship keywords
        conditions = []
        for kw in INTERNSHIP_KEYWORDS:
            conditions.append({"title": {"$regex": re.escape(kw), "$options": "i"}})

        # Location filter for South India
        loc_conditions = []
        for loc in SOUTH_INDIA_LOCATIONS + ["india", "remote"]:
            loc_conditions.append({"location": {"$regex": re.escape(loc), "$options": "i"}})

        query = {"$and": [{"$or": conditions}, {"$or": loc_conditions}]}
        cursor = jobs_col.find(query, {"_id": 0}).sort("date_posted", -1).limit(MAX_RESULTS)
        jobs = list(cursor)

        return {
            "internships": [self._format_job(j) for j in jobs],
            "stats": {"count": len(jobs)},
        }

    def get_district(self, district: str) -> dict:
        """Return jobs in a specific district/city."""
        db = get_database()
        jobs_col = db["jobs"]

        query = {"location": {"$regex": re.escape(district), "$options": "i"}}
        cursor = jobs_col.find(query, {"_id": 0}).sort("date_posted", -1).limit(MAX_RESULTS)
        jobs = list(cursor)

        scored = []
        for job in jobs:
            score = self._fresher_score(job)
            job["_fresher_score"] = score
            scored.append(job)

        scored.sort(key=lambda j: j["_fresher_score"], reverse=True)

        return {
            "district": district,
            "jobs": [self._format_job(j) for j in scored],
            "stats": {"count": len(scored)},
        }

    def get_core_engineering(self) -> dict:
        """Return core engineering jobs in South India."""
        db = get_database()
        jobs_col = db["jobs"]

        # Core engineering keywords
        conditions = []
        for kw in CORE_ENGINEERING_KEYWORDS:
            conditions.append({"title": {"$regex": re.escape(kw), "$options": "i"}})
            conditions.append({"description": {"$regex": re.escape(kw), "$options": "i"}})

        # Location filter
        loc_conditions = []
        for loc in SOUTH_INDIA_LOCATIONS + ["india", "remote"]:
            loc_conditions.append({"location": {"$regex": re.escape(loc), "$options": "i"}})

        query = {"$and": [{"$or": conditions}, {"$or": loc_conditions}]}
        cursor = jobs_col.find(query, {"_id": 0}).sort("date_posted", -1).limit(100)
        jobs = list(cursor)

        scored = []
        for job in jobs:
            score = self._fresher_score(job)
            job["_fresher_score"] = score
            scored.append(job)

        scored.sort(key=lambda j: j["_fresher_score"], reverse=True)

        return {
            "core_engineering": [self._format_job(j) for j in scored[:MAX_RESULTS]],
            "stats": {"count": len(scored)},
        }

    def _get_regional_jobs(self, locations: list[str], region_name: str) -> dict:
        """Get jobs for a region with fresher scoring and district breakdown."""
        db = get_database()
        jobs_col = db["jobs"]

        query = self._build_location_query(locations)
        cursor = jobs_col.find(query, {"_id": 0}).sort("date_posted", -1).limit(200)
        all_jobs = list(cursor)

        # Score all
        scored = []
        for job in all_jobs:
            score = self._fresher_score(job)
            job["_fresher_score"] = score
            scored.append(job)

        scored.sort(key=lambda j: j["_fresher_score"], reverse=True)

        # District breakdown
        district_counts: dict[str, int] = {}
        for job in all_jobs:
            loc = job.get("location", "").lower()
            for city in locations:
                if city in loc:
                    district_counts[city.title()] = district_counts.get(city.title(), 0) + 1
                    break

        return {
            "region": region_name,
            "jobs": [self._format_job(j) for j in scored[:MAX_RESULTS]],
            "districts": [
                {"name": k, "count": v}
                for k, v in sorted(district_counts.items(), key=lambda x: x[1], reverse=True)
            ],
            "stats": {
                "total_jobs": len(all_jobs),
                "fresher_friendly": sum(1 for j in scored if j["_fresher_score"] >= 10),
            },
        }

    def _build_location_query(self, locations: list[str]) -> dict:
        """Build MongoDB OR query for multiple locations."""
        conditions = [
            {"location": {"$regex": re.escape(loc), "$options": "i"}}
            for loc in locations
        ]
        return {"$or": conditions}

    def _fresher_score(self, job: dict) -> int:
        """Calculate fresher-friendliness score for a job."""
        score = 0
        title = job.get("title", "").lower()
        description = job.get("description", "").lower()

        # Fresher keywords boost
        for kw in FRESHER_KEYWORDS:
            if kw in title:
                score += 20
                break

        # Seniority penalty
        for kw in SENIOR_KEYWORDS_REGIONAL:
            if kw in title:
                score -= 20
                break

        # Experience check in description
        if "0-2 years" in description or "0-1 years" in description or "freshers" in description:
            score += 15
        elif "5+ years" in description or "7+ years" in description or "10+ years" in description:
            score -= 15

        # Core engineering bonus
        for kw in CORE_ENGINEERING_KEYWORDS:
            if kw in title or kw in description:
                score += 5
                break

        # Freshness
        date_posted = job.get("date_posted", "")
        if date_posted:
            try:
                posted = datetime.strptime(date_posted, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                days = (datetime.now(timezone.utc) - posted).days
                if days <= 3:
                    score += 10
                elif days <= 7:
                    score += 5
            except (ValueError, TypeError):
                pass

        return score

    def _format_job(self, job: dict) -> dict:
        """Format a job for the API response."""
        return {
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "job_url": job.get("job_url", ""),
            "date_posted": job.get("date_posted", ""),
            "source_platform": job.get("source_platform", ""),
            "fresher_score": job.get("_fresher_score", 0),
        }
