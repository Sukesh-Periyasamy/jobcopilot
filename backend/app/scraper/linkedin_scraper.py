"""LinkedIn Jobs Scraper for JobCopilot.

Uses linkedin-jobs-scraper package to fetch jobs from LinkedIn.
Loads queries from linkedin_queries.json for easy configuration.
Enriches jobs with skills and categories.

Install: pip install linkedin-jobs-scraper
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.models.job import JobRecord, ScrapeResult
from app.services.job_enrichment import categorize_job, extract_skills

logger = logging.getLogger(__name__)

# Load queries from JSON config
QUERIES_FILE = Path(__file__).parent.parent / "config" / "linkedin_queries.json"

MAX_RESULTS_PER_QUERY = 25


def _load_queries() -> list[dict]:
    """Load LinkedIn queries from JSON config file."""
    if not QUERIES_FILE.exists():
        logger.warning("linkedin_queries.json not found at %s", QUERIES_FILE)
        return []

    with open(QUERIES_FILE) as f:
        config = json.load(f)

    queries = []
    for category, data in config.items():
        for query_text in data.get("queries", []):
            for location in data.get("locations", ["India"]):
                queries.append({
                    "query": query_text,
                    "location": location,
                    "category": category,
                })

    return queries


def scrape_linkedin_jobs() -> ScrapeResult:
    """Scrape LinkedIn jobs using linkedin-jobs-scraper.

    Loads queries from linkedin_queries.json, scrapes LinkedIn,
    enriches with skills/categories, and returns normalized results.

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
    seen_urls: set[str] = set()  # Deduplication
    now_iso = datetime.now(timezone.utc).isoformat()

    def on_data(data: EventData) -> None:
        """Callback for each job found."""
        try:
            url = data.link or ""

            # Deduplicate by URL
            if url in seen_urls:
                return
            seen_urls.add(url)

            # Extract skills and category
            description = data.description or ""
            title = data.title or ""
            skills = extract_skills(description)
            category = categorize_job(title, description)

            job = JobRecord(
                title=title,
                company=data.company or "",
                location=data.place or "",
                source="linkedin",
                job_url=url,
                description=description,
                job_type=getattr(data, "job_type", "") or "",
                salary=getattr(data, "salary", "") or "",
                date_posted=_parse_linkedin_date(getattr(data, "date", None)),
                search_term=getattr(data, "query", "") or "",
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
        logger.info("LinkedIn scraping completed. Total unique jobs: %d", len(all_jobs))

    # Load queries from config
    query_configs = _load_queries()
    if not query_configs:
        return ScrapeResult(jobs=[], errors=["No queries configured in linkedin_queries.json"])

    # Build Query objects
    queries = []
    for qc in query_configs:
        try:
            query = Query(
                query=qc["query"],
                options=QueryOptions(
                    locations=[qc["location"]],
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
            logger.warning("Error building query for %s: %s", qc, exc)

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

        logger.info("Starting LinkedIn scrape with %d queries from config", len(queries))
        scraper.run(queries)

    except Exception as exc:
        error_msg = f"LinkedIn scraper failed: {exc}"
        logger.error(error_msg)
        all_errors.append(error_msg)

    logger.info(
        "LinkedIn scrape complete: %d unique jobs, %d errors, %d duplicates filtered",
        len(all_jobs),
        len(all_errors),
        len(seen_urls) - len(all_jobs),
    )

    return ScrapeResult(jobs=all_jobs, errors=all_errors)


def _parse_linkedin_date(date_str: str | None) -> str:
    """Parse LinkedIn date string to YYYY-MM-DD format."""
    if not date_str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    date_lower = date_str.lower().strip()
    now = datetime.now(timezone.utc)

    try:
        if "today" in date_lower or "just" in date_lower:
            return now.strftime("%Y-%m-%d")
        elif "yesterday" in date_lower or "1 day" in date_lower:
            return (now - timedelta(days=1)).strftime("%Y-%m-%d")
        elif "day" in date_lower:
            days = int("".join(filter(str.isdigit, date_lower)) or "1")
            return (now - timedelta(days=days)).strftime("%Y-%m-%d")
        elif "week" in date_lower:
            weeks = int("".join(filter(str.isdigit, date_lower)) or "1")
            return (now - timedelta(weeks=weeks)).strftime("%Y-%m-%d")
        elif "month" in date_lower:
            months = int("".join(filter(str.isdigit, date_lower)) or "1")
            return (now - timedelta(days=months * 30)).strftime("%Y-%m-%d")
        else:
            return date_str
    except (ValueError, TypeError):
        return now.strftime("%Y-%m-%d")
