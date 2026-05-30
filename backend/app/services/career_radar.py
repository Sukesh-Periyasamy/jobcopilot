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
    "Medical Technology": 10,
    "Biomedical Engineering": 10,
    "Healthcare AI": 10,
    "Medical Devices": 9,
    "Research Engineering": 9,
    "Embedded Systems": 8,
    "IoT": 8,
    "Python Development": 7,
    "Healthcare Technology": 7,
    "Diagnostics and Biosensors": 7,
    "Product Management": 5,
}

# Negative keywords — penalize irrelevant roles
NEGATIVE_KEYWORDS: list[str] = [
    "sales",
    "account executive",
    "recruiter",
    "customer success",
    "business development representative",
    "SDR",
    "BDR",
    "real estate",
    "financial advisor",
    "insurance agent",
    "content writer",
    "social media manager",
    "graphic designer",
]
NEGATIVE_PENALTY = 15

# Minimum score to be considered a match
MIN_SCORE = 15

# High priority threshold for /career-radar/top
HIGH_PRIORITY_SCORE = 25
HIGH_PRIORITY_MAX_DAYS = 14

# Freshness bonuses
FRESHNESS_BONUSES = [
    (3, 5),   # 0-3 days: +5
    (7, 3),   # 4-7 days: +3
    (14, 1),  # 8-14 days: +1
]

# Location bonuses
REMOTE_BONUS = 2
INDIA_BONUS = 1

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

        # Get applied and saved job URLs to exclude
        repo = JobsRepository()
        applied_urls = {j.get("job_url") for j in repo.get_applied_jobs()}
        saved_urls = {j.get("job_url") for j in repo.get_saved_jobs()}
        excluded_urls = applied_urls | saved_urls

        now = datetime.now(timezone.utc)
        high_priority = []

        for job in scored_jobs:
            # Score threshold
            if job.get("_score", 0) < HIGH_PRIORITY_SCORE:
                break  # Already sorted desc, no more will qualify

            # Freshness threshold
            date_posted = job.get("date_posted", "")
            if date_posted:
                try:
                    posted = datetime.strptime(date_posted, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if (now - posted).days > HIGH_PRIORITY_MAX_DAYS:
                        continue
                except (ValueError, TypeError):
                    continue
            else:
                continue

            # Exclude already applied/saved
            if job.get("job_url") in excluded_urls:
                continue

            high_priority.append(self._format_job(job))

            if len(high_priority) >= MAX_RESULTS_PER_CATEGORY:
                break

        return {
            "high_priority": high_priority,
            "stats": {
                "total_scored": total_count,
                "matches_found": len(scored_jobs),
                "high_priority_count": len(high_priority),
            },
        }

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
