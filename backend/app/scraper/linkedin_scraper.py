"""LinkedIn Jobs Scraper for JobCopilot.

Uses linkedin-jobs-scraper package to fetch jobs from LinkedIn
with India-focused MedTech search terms. Normalizes results into
JobRecord format for MongoDB storage.

Install: pip install linkedin-jobs-scraper
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.models.job import JobRecord, ScrapeResult

logger = logging.getLogger(__name__)

# India-focused MedTech search queries
LINKEDIN_QUERIES = [
    {"query": "Biomedical Engineer", "location": "India"},
    {"query": "Medical Device Engineer", "location": "India"},
    {"query": "Clinical Research Associate", "location": "India"},
    {"query": "Research Associate", "location": "Bangalore"},
    {"query": "Research Associate", "location": "Chennai"},
    {"query": "Project Associate", "location": "India"},
    {"query": "Healthcare AI", "location": "India"},
    {"query": "Quality Engineer Medical Device", "location": "India"},
    {"query": "Regulatory Affairs", "location": "India"},
    {"query": "R&D Engineer Medical", "location": "India"},
    {"query": "Embedded Systems Engineer", "location": "Bangalore"},
    {"query": "Biomedical Engineer", "location": "Bangalore"},
    {"query": "Biomedical Engineer", "location": "Chennai"},
    {"query": "Diagnostics Engineer", "location": "India"},
    {"query": "Biosensor", "location": "India"},
]

# Maximum results per query
MAX_RESULTS_PER_QUERY = 25


def scrape_linkedin_jobs() -> ScrapeResult:
    """Scrape LinkedIn jobs using linkedin-jobs-scraper.

    Returns:
        ScrapeResult with collected jobs and errors.
    """
    try:
        from linkedin_jobs_scraper import LinkedinScraper
        from linkedin_jobs_scraper.events import Events, EventData
        from linkedin_jobs_scraper.query import Query, QueryOptions, QueryFilters
        from linkedin_jobs_scraper.filters import (
            RelevanceFilters,
            TimeFilters,
            TypeFilters,
            ExperienceLevelFilters,
        )
    except ImportError as e:
        logger.warning("linkedin-jobs-scraper not installed: %s", e)
        return ScrapeResult(
            jobs=[],
            errors=["linkedin-jobs-scraper not installed. Run: pip install linkedin-jobs-scraper"],
        )

    all_jobs: list[JobRecord] = []
    all_errors: list[str] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    def on_data(data: EventData) -> None:
        """Callback for each job found."""
        try:
            job = JobRecord(
                title=data.title or "",
                company=data.company or "",
                location=data.place or "",
                source="linkedin",
                job_url=data.link or "",
                description=data.description or "",
                job_type=data.job_type or "",
                salary=data.salary or "",
                date_posted=_parse_linkedin_date(data.date),
                search_term=data.query or "",
                source_type="linkedin_scraper",
                source_platform="linkedin",
                created_at=now_iso,
                updated_at=now_iso,
            )
            all_jobs.append(job)
        except Exception as exc:
            logger.warning("Error normalizing LinkedIn job: %s", exc)

    def on_error(error: Any) -> None:
        """Callback for scraper errors."""
        error_msg = f"LinkedIn scraper error: {error}"
        logger.error(error_msg)
        all_errors.append(error_msg)

    def on_end() -> None:
        """Callback when scraping completes."""
        logger.info("LinkedIn scraping completed. Total jobs: %d", len(all_jobs))

    # Build queries
    queries = []
    for q in LINKEDIN_QUERIES:
        try:
            query = Query(
                query=q["query"],
                options=QueryOptions(
                    locations=[q["location"]],
                    limit=MAX_RESULTS_PER_QUERY,
                    filters=QueryFilters(
                        relevance=RelevanceFilters.RECENT,
                        time=TimeFilters.WEEK,
                        experience=[ExperienceLevelFilters.ENTRY_LEVEL, ExperienceLevelFilters.ASSOCIATE],
                    ),
                ),
            )
            queries.append(query)
        except Exception as exc:
            logger.warning("Error building query for %s: %s", q, exc)

    # Run scraper
    try:
        scraper = LinkedinScraper(
            chrome_executable_path=None,
            chrome_options=None,
            headless=True,
            max_workers=2,
            slow_mo=1.5,
        )

        scraper.on(Events.DATA, on_data)
        scraper.on(Events.ERROR, on_error)
        scraper.on(Events.END, on_end)

        logger.info("Starting LinkedIn scrape with %d queries", len(queries))
        scraper.run(queries)

    except Exception as exc:
        error_msg = f"LinkedIn scraper failed: {exc}"
        logger.error(error_msg)
        all_errors.append(error_msg)

    logger.info(
        "LinkedIn scrape complete: %d jobs, %d errors",
        len(all_jobs),
        len(all_errors),
    )

    return ScrapeResult(jobs=all_jobs, errors=all_errors)


def _parse_linkedin_date(date_str: str | None) -> str:
    """Parse LinkedIn date string to YYYY-MM-DD format.

    LinkedIn returns dates like "2 days ago", "1 week ago", etc.
    """
    if not date_str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    date_lower = date_str.lower().strip()
    now = datetime.now(timezone.utc)

    try:
        if "today" in date_lower or "just" in date_lower:
            return now.strftime("%Y-%m-%d")
        elif "yesterday" in date_lower or "1 day" in date_lower:
            return (now - __import__("datetime").timedelta(days=1)).strftime("%Y-%m-%d")
        elif "day" in date_lower:
            days = int("".join(filter(str.isdigit, date_lower)) or "1")
            return (now - __import__("datetime").timedelta(days=days)).strftime("%Y-%m-%d")
        elif "week" in date_lower:
            weeks = int("".join(filter(str.isdigit, date_lower)) or "1")
            return (now - __import__("datetime").timedelta(weeks=weeks)).strftime("%Y-%m-%d")
        elif "month" in date_lower:
            months = int("".join(filter(str.isdigit, date_lower)) or "1")
            return (now - __import__("datetime").timedelta(days=months * 30)).strftime("%Y-%m-%d")
        else:
            # Try parsing as date
            return date_str
    except (ValueError, TypeError):
        return now.strftime("%Y-%m-%d")
