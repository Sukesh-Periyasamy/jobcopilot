"""Career Radar service for personalized job scoring and ranking.

Scores every job based on collection weights, freshness, location,
and watchlist company matching. Applies negative keyword penalties
and minimum score filtering to reduce noise.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.database.connection import get_database
from app.database.repository import JobsRepository
from app.services.constants import (
    COLLECTIONS,
    INTERNSHIP_KEYWORDS,
    RESEARCH_INSTITUTIONS,
)

logger = logging.getLogger(__name__)

# Career profile weights — higher = more relevant to user
COLLECTION_WEIGHTS: dict[str, int] = {
    "Biomedical Engineering": 10,
    "Medical Devices": 10,
    "Research Engineering": 10,
    "Diagnostics and Biosensors": 10,
    "Medical Technology": 9,
    "Healthcare AI": 8,
    "Embedded Systems": 7,
    "IoT": 7,
    "Python Development": 6,
    "Healthcare Technology": 6,
    "Product Management": 4,
}

# Biomedical research profile — tuned for SERS/biosensor/diagnostics research
BIOMEDICAL_PROFILE_WEIGHTS: dict[str, int] = {
    "Biomedical Engineering": 10,
    "Medical Devices": 10,
    "Research Engineering": 10,
    "Diagnostics and Biosensors": 10,
    "Medical Technology": 8,
    "Healthcare AI": 7,
    "Embedded Systems": 6,
    "IoT": 5,
    "Healthcare Technology": 5,
    "Python Development": 4,
    "Product Management": 2,
}

# Research fellowship keywords
FELLOWSHIP_KEYWORDS: list[str] = [
    "JRF",
    "SRF",
    "Project Associate",
    "Project Assistant",
    "Research Associate",
    "Research Scientist",
    "Research Fellow",
    "Post-Doctoral",
    "Postdoc",
    "RA",
    "Young Professional",
]

# Negative keywords — penalize irrelevant roles
NEGATIVE_KEYWORDS: list[str] = [
    "sales",
    "marketing",
    "account executive",
    "business development",
    "recruiter",
    "talent acquisition",
    "customer success",
    "SDR",
    "BDR",
    "real estate",
    "financial advisor",
    "insurance agent",
    "content writer",
    "social media manager",
    "graphic designer",
    "copywriter",
]
NEGATIVE_PENALTY = 20

# Seniority penalties — too senior for early-career profile
SENIOR_KEYWORDS: list[str] = [
    "director",
    "principal",
    "vp",
    "vice president",
    "head of",
    "chief",
    "cto",
    "ceo",
    "svp",
]
SENIOR_PENALTY = 15

# Early career bonus — roles matching current career stage
EARLY_CAREER_KEYWORDS: list[str] = [
    "associate",
    "junior",
    "entry",
    "graduate",
    "engineer i",
    "research associate",
    "trainee",
    "intern",
    "fresher",
    "early career",
]
EARLY_CAREER_BONUS = 8

# Minimum score to be considered a match
MIN_SCORE = 15

# High priority threshold for /career-radar/top
HIGH_PRIORITY_SCORE = 25
HIGH_PRIORITY_MAX_DAYS = 14

# Action list threshold (broader window)
ACTION_LIST_SCORE = 25
ACTION_LIST_MAX_DAYS = 30

# Freshness bonuses
FRESHNESS_BONUSES = [
    (3, 5),   # 0-3 days: +5
    (7, 3),   # 4-7 days: +3
    (14, 1),  # 8-14 days: +1
]

# Location bonuses
REMOTE_BONUS = 2
INDIA_BONUS = 10  # Strong India preference for current stage

# Watchlist company bonus
WATCHLIST_BONUS = 5

MAX_RESULTS_PER_CATEGORY = 25


class CareerRadarService:
    """Scores and ranks jobs based on a personalized career profile."""

    def get_career_radar(self) -> dict:
        """Score all jobs and return categorized top matches.

        Returns:
            Dict with keys: top_matches, research_matches, internships,
            watchlist_matches, remote_matches, stats.
        """
        scored_jobs, total_count = self._score_all_jobs()

        # Categorize
        top_matches = scored_jobs[:MAX_RESULTS_PER_CATEGORY]

        research_matches = [
            j for j in scored_jobs
            if self._is_research(j)
        ][:MAX_RESULTS_PER_CATEGORY]

        internships = [
            j for j in scored_jobs
            if self._is_internship(j)
        ][:MAX_RESULTS_PER_CATEGORY]

        watchlist_companies = self._get_watchlist_companies()
        watchlist_matches = [
            j for j in scored_jobs
            if j.get("company", "").lower() in watchlist_companies
        ][:MAX_RESULTS_PER_CATEGORY]

        remote_matches = [
            j for j in scored_jobs
            if "remote" in j.get("location", "").lower()
        ][:MAX_RESULTS_PER_CATEGORY]

        return {
            "top_matches": [self._format_job(j) for j in top_matches],
            "research_matches": [self._format_job(j) for j in research_matches],
            "internships": [self._format_job(j) for j in internships],
            "watchlist_matches": [self._format_job(j) for j in watchlist_matches],
            "remote_matches": [self._format_job(j) for j in remote_matches],
            "stats": {
                "total_scored": total_count,
                "matches_found": len(scored_jobs),
            },
        }

    def get_top_priority(self) -> dict:
        """Return only high-priority actionable matches.

        Filters: score >= 25, posted <= 14 days, not already applied/saved.

        Returns:
            Dict with high_priority list and stats.
        """
        scored_jobs, total_count = self._score_all_jobs()
        high_priority = self._filter_actionable(scored_jobs, HIGH_PRIORITY_SCORE, HIGH_PRIORITY_MAX_DAYS)

        return {
            "high_priority": high_priority,
            "stats": {
                "total_scored": total_count,
                "matches_found": len(scored_jobs),
                "high_priority_count": len(high_priority),
            },
        }

    def get_action_list(self) -> dict:
        """Return the daily application queue.

        Filters: score >= 25, posted <= 30 days, not already applied/saved.
        Broader window than top_priority for a fuller action list.

        Returns:
            Dict with action_list and stats.
        """
        scored_jobs, total_count = self._score_all_jobs()
        action_list = self._filter_actionable(scored_jobs, ACTION_LIST_SCORE, ACTION_LIST_MAX_DAYS)

        return {
            "action_list": action_list,
            "stats": {
                "total_scored": total_count,
                "matches_found": len(scored_jobs),
                "action_list_count": len(action_list),
            },
        }

    def _filter_actionable(self, scored_jobs: list[dict], min_score: int, max_days: int) -> list[dict]:
        """Filter jobs by score, freshness, and exclude applied/saved.

        Args:
            scored_jobs: Pre-sorted list of scored jobs.
            min_score: Minimum score threshold.
            max_days: Maximum days since posting.

        Returns:
            List of formatted job dicts meeting all criteria.
        """
        repo = JobsRepository()
        applied_urls = {j.get("job_url") for j in repo.get_applied_jobs()}
        saved_urls = {j.get("job_url") for j in repo.get_saved_jobs()}
        excluded_urls = applied_urls | saved_urls

        now = datetime.now(timezone.utc)
        results = []

        for job in scored_jobs:
            if job.get("_score", 0) < min_score:
                break  # Sorted desc, no more will qualify

            date_posted = job.get("date_posted", "")
            if date_posted:
                try:
                    posted = datetime.strptime(date_posted, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if (now - posted).days > max_days:
                        continue
                except (ValueError, TypeError):
                    continue
            else:
                continue

            if job.get("job_url") in excluded_urls:
                continue

            results.append(self._format_job(job))

            if len(results) >= MAX_RESULTS_PER_CATEGORY:
                break

        return results

    def get_india_feed(self) -> dict:
        """Return India-focused career radar matches.

        Filters for jobs located in India (major cities + remote India).

        Returns:
            Dict with india_matches list and stats.
        """
        scored_jobs, total_count = self._score_all_jobs()

        india_cities = [
            "india", "bangalore", "bengaluru", "hyderabad", "chennai",
            "pune", "mumbai", "delhi", "noida", "gurugram", "gurgaon",
            "kolkata", "ahmedabad", "kochi", "thiruvananthapuram",
        ]

        india_matches = []
        for job in scored_jobs:
            location = job.get("location", "").lower()
            if any(city in location for city in india_cities):
                india_matches.append(self._format_job(job))
                if len(india_matches) >= MAX_RESULTS_PER_CATEGORY:
                    break

        return {
            "india_matches": india_matches,
            "stats": {
                "total_scored": total_count,
                "india_count": len(india_matches),
            },
        }

    def get_research_radar(self) -> dict:
        """Return research fellowship opportunities from Indian institutions.

        Filters for JRF, SRF, Project Associate, Research Associate, etc.
        from research institutions.

        Returns:
            Dict with categorized research fellowship matches.
        """
        db = get_database()
        jobs_collection = db["jobs"]

        # Build query matching fellowship keywords in title
        import re
        conditions = []
        for kw in FELLOWSHIP_KEYWORDS:
            conditions.append({"title": {"$regex": re.escape(kw), "$options": "i"}})

        query = {"$or": conditions}
        cursor = jobs_collection.find(query, {"_id": 0}).sort("date_posted", -1).limit(100)
        all_fellowship_jobs = list(cursor)

        # Also get jobs from research institutions
        inst_conditions = []
        for inst in RESEARCH_INSTITUTIONS:
            inst_conditions.append({"company": {"$regex": re.escape(inst), "$options": "i"}})
            inst_conditions.append({"description": {"$regex": re.escape(inst), "$options": "i"}})

        inst_query = {"$or": inst_conditions}
        inst_cursor = jobs_collection.find(inst_query, {"_id": 0}).sort("date_posted", -1).limit(50)
        institution_jobs = list(inst_cursor)

        # Merge and deduplicate by job_url
        seen_urls = set()
        merged = []
        for job in all_fellowship_jobs + institution_jobs:
            url = job.get("job_url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                merged.append(job)

        # Score with biomedical profile
        watchlist_companies = self._get_watchlist_companies()
        scored = []
        for job in merged:
            score, collections = self._score_job_with_weights(job, watchlist_companies, BIOMEDICAL_PROFILE_WEIGHTS)
            if score > 0:
                job["_score"] = score
                job["_collections"] = collections
                scored.append(job)

        scored.sort(key=lambda j: j["_score"], reverse=True)

        # Categorize
        jrf_srf = [j for j in scored if any(
            kw.lower() in j.get("title", "").lower() for kw in ["jrf", "srf", "research fellow"]
        )][:15]

        project_associate = [j for j in scored if any(
            kw.lower() in j.get("title", "").lower() for kw in ["project associate", "project assistant"]
        )][:15]

        research_associate = [j for j in scored if any(
            kw.lower() in j.get("title", "").lower() for kw in ["research associate", "research scientist"]
        )][:15]

        return {
            "all_fellowships": [self._format_job(j) for j in scored[:25]],
            "jrf_srf": [self._format_job(j) for j in jrf_srf],
            "project_associate": [self._format_job(j) for j in project_associate],
            "research_associate": [self._format_job(j) for j in research_associate],
            "stats": {
                "total_fellowship_jobs": len(merged),
                "scored_matches": len(scored),
            },
        }

    def get_biomedical_profile(self) -> dict:
        """Return career radar scored with biomedical research profile.

        Uses BIOMEDICAL_PROFILE_WEIGHTS instead of default weights.
        Tuned for SERS, biosensors, diagnostics, medical devices research.

        Returns:
            Dict with top_matches and stats.
        """
        db = get_database()
        jobs_collection = db["jobs"]

        cursor = jobs_collection.find({}, {"_id": 0})
        all_jobs = list(cursor)

        watchlist_companies = self._get_watchlist_companies()

        scored_jobs = []
        for job in all_jobs:
            score, collections = self._score_job_with_weights(job, watchlist_companies, BIOMEDICAL_PROFILE_WEIGHTS)
            if score >= MIN_SCORE:
                job["_score"] = score
                job["_collections"] = collections
                scored_jobs.append(job)

        scored_jobs.sort(key=lambda j: j["_score"], reverse=True)

        return {
            "top_matches": [self._format_job(j) for j in scored_jobs[:MAX_RESULTS_PER_CATEGORY]],
            "stats": {
                "total_scored": len(all_jobs),
                "matches_found": len(scored_jobs),
            },
        }

    def _score_job_with_weights(self, job: dict, watchlist_companies: set[str], weights: dict[str, int]) -> tuple[int, list[str]]:
        """Score a job using a specific weight profile.

        Same logic as _score_job but accepts custom weights.
        """
        score = 0
        matched_collections: list[str] = []

        title = job.get("title", "").lower()
        description = job.get("description", "").lower()
        combined = f"{title} {description}"

        # Negative keyword penalty
        for neg_kw in NEGATIVE_KEYWORDS:
            if neg_kw.lower() in title:
                score -= NEGATIVE_PENALTY
                break

        # Seniority penalty
        for senior_kw in SENIOR_KEYWORDS:
            if senior_kw in title:
                score -= SENIOR_PENALTY
                break

        # Early career bonus
        for ec_kw in EARLY_CAREER_KEYWORDS:
            if ec_kw in title:
                score += EARLY_CAREER_BONUS
                break

        # Collection matching with custom weights
        for collection_def in COLLECTIONS:
            weight = weights.get(collection_def.name, 0)
            if weight == 0:
                continue
            for keyword in collection_def.keywords:
                if keyword.lower() in combined:
                    score += weight
                    matched_collections.append(collection_def.name)
                    break

        # Freshness bonus
        date_posted = job.get("date_posted", "")
        if date_posted:
            score += self._freshness_bonus(date_posted)

        # Location bonuses
        location = job.get("location", "").lower()
        if "remote" in location:
            score += REMOTE_BONUS
        if "india" in location or any(
            city in location
            for city in ["bangalore", "hyderabad", "chennai", "pune", "mumbai", "delhi", "noida", "gurugram"]
        ):
            score += INDIA_BONUS

        # Watchlist company bonus
        company = job.get("company", "").lower()
        if company in watchlist_companies:
            score += WATCHLIST_BONUS

        return score, matched_collections

    def get_telegram_summary(self) -> list[dict]:
        """Return top 10 matches formatted for Telegram notification.

        Returns:
            List of top 10 job dicts with score, title, company, location, job_url.
        """
        result = self.get_top_priority()
        return result["high_priority"][:10]

    def _score_all_jobs(self) -> tuple[list[dict], int]:
        """Score all jobs, apply filters, return sorted matches.

        Returns:
            Tuple of (sorted_scored_jobs, total_job_count).
        """
        db = get_database()
        jobs_collection = db["jobs"]

        cursor = jobs_collection.find({}, {"_id": 0})
        all_jobs = list(cursor)

        watchlist_companies = self._get_watchlist_companies()

        scored_jobs = []
        for job in all_jobs:
            score, collections = self._score_job(job, watchlist_companies)
            if score >= MIN_SCORE:
                job["_score"] = score
                job["_collections"] = collections
                scored_jobs.append(job)

        scored_jobs.sort(key=lambda j: j["_score"], reverse=True)
        return scored_jobs, len(all_jobs)

    def _get_watchlist_companies(self) -> set[str]:
        """Get watchlist company names as a lowercase set."""
        repo = JobsRepository()
        watchlist = repo.get_watchlist()
        return {entry["company_name"].lower() for entry in watchlist}

    def _score_job(self, job: dict, watchlist_companies: set[str]) -> tuple[int, list[str]]:
        """Score a single job based on profile weights and bonuses.

        Returns:
            Tuple of (total_score, list_of_matching_collection_names).
        """
        score = 0
        matched_collections: list[str] = []

        title = job.get("title", "").lower()
        description = job.get("description", "").lower()
        combined = f"{title} {description}"

        # Negative keyword penalty (check title only for speed)
        for neg_kw in NEGATIVE_KEYWORDS:
            if neg_kw.lower() in title:
                score -= NEGATIVE_PENALTY
                break  # One penalty is enough

        # Seniority penalty — too senior for early-career profile
        for senior_kw in SENIOR_KEYWORDS:
            if senior_kw in title:
                score -= SENIOR_PENALTY
                break

        # Early career bonus — matches current career stage
        for ec_kw in EARLY_CAREER_KEYWORDS:
            if ec_kw in title:
                score += EARLY_CAREER_BONUS
                break

        # Collection matching
        for collection_def in COLLECTIONS:
            weight = COLLECTION_WEIGHTS.get(collection_def.name, 0)
            if weight == 0:
                continue

            for keyword in collection_def.keywords:
                if keyword.lower() in combined:
                    score += weight
                    matched_collections.append(collection_def.name)
                    break  # Only count each collection once

        # Freshness bonus
        date_posted = job.get("date_posted", "")
        if date_posted:
            score += self._freshness_bonus(date_posted)

        # Location bonuses
        location = job.get("location", "").lower()
        if "remote" in location:
            score += REMOTE_BONUS
        if "india" in location or any(
            city in location
            for city in ["bangalore", "hyderabad", "chennai", "pune", "mumbai", "delhi", "noida", "gurugram"]
        ):
            score += INDIA_BONUS

        # Watchlist company bonus
        company = job.get("company", "").lower()
        if company in watchlist_companies:
            score += WATCHLIST_BONUS

        return score, matched_collections

    def _freshness_bonus(self, date_posted: str) -> int:
        """Calculate freshness bonus based on days since posting."""
        try:
            posted = datetime.strptime(date_posted, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            days_old = (now - posted).days

            for max_days, bonus in FRESHNESS_BONUSES:
                if days_old <= max_days:
                    return bonus
            return 0
        except (ValueError, TypeError):
            return 0

    def _is_research(self, job: dict) -> bool:
        """Check if job is from a research institution."""
        company = job.get("company", "").lower()
        description = job.get("description", "").lower()
        for inst in RESEARCH_INSTITUTIONS:
            if inst.lower() in company or inst.lower() in description:
                return True
        return False

    def _is_internship(self, job: dict) -> bool:
        """Check if job matches internship keywords."""
        title = job.get("title", "").lower()
        for kw in INTERNSHIP_KEYWORDS:
            if kw.lower() in title:
                return True
        return False

    def _format_job(self, job: dict) -> dict:
        """Format a scored job for the API response."""
        return {
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "job_url": job.get("job_url", ""),
            "date_posted": job.get("date_posted", ""),
            "source_platform": job.get("source_platform", ""),
            "score": job.get("_score", 0),
            "collections": job.get("_collections", []),
        }
