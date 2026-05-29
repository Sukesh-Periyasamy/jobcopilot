"""Scraper service wrapping JobSpy with normalization and error handling.

Iterates over all search_term × location combinations across configured
sources, normalizes results into JobRecords, and collects errors for
any failed combinations.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import pandas as pd

from jobspy import scrape_jobs

from app.config.settings import Settings
from app.models.job import JobRecord, ScrapeResult

logger = logging.getLogger(__name__)


def _normalize_row(row: pd.Series, search_term: str) -> JobRecord | None:
    """Normalize a single DataFrame row into a JobRecord.

    Returns None if the row is missing required fields (title or job_url).
    Sets missing optional fields to empty string.
    """
    title = str(row.get("title", "") or "").strip()
    job_url = str(row.get("job_url", "") or "").strip()

    if not title or not job_url:
        logger.warning(
            "Skipping invalid record: missing title=%r or job_url=%r",
            title,
            job_url,
        )
        return None

    now_iso = datetime.now(timezone.utc).isoformat()

    # Build salary string from compensation fields
    salary = ""
    min_amount = row.get("min_amount")
    max_amount = row.get("max_amount")
    currency = row.get("currency", "")
    interval = row.get("interval", "")

    if pd.notna(min_amount) and pd.notna(max_amount):
        currency_str = str(currency) if pd.notna(currency) else ""
        interval_str = str(interval) if pd.notna(interval) else ""
        salary = f"{currency_str} {min_amount}-{max_amount}"
        if interval_str:
            salary = f"{salary} ({interval_str})"
        salary = salary.strip()

    # Normalize date_posted
    date_posted_raw = row.get("date_posted")
    if pd.notna(date_posted_raw) and date_posted_raw:
        try:
            if isinstance(date_posted_raw, str):
                date_posted = date_posted_raw.strip()
            else:
                date_posted = pd.Timestamp(date_posted_raw).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            date_posted = ""
    else:
        date_posted = ""

    return JobRecord(
        title=title,
        company=str(row.get("company", "") or "").strip(),
        location=str(row.get("location", "") or "").strip(),
        source=str(row.get("site", "") or "").strip(),
        job_url=job_url,
        description=str(row.get("description", "") or "").strip(),
        job_type=str(row.get("job_type", "") or "").strip(),
        salary=salary,
        date_posted=date_posted,
        search_term=search_term,
        created_at=now_iso,
        updated_at=now_iso,
    )


def _scrape_combination(
    search_term: str, location: str, sources: list[str]
) -> tuple[list[JobRecord], list[str]]:
    """Scrape a single search_term × location combination.

    Returns a tuple of (jobs, errors) for this combination.
    """
    jobs: list[JobRecord] = []
    errors: list[str] = []

    try:
        df: pd.DataFrame = scrape_jobs(
            site_name=sources,
            search_term=search_term,
            location=location,
            results_wanted=15,
            country_indeed="india",
        )

        if df.empty:
            logger.info(
                "No results for search_term=%r, location=%r",
                search_term,
                location,
            )
            return jobs, errors

        for _, row in df.iterrows():
            record = _normalize_row(row, search_term)
            if record is not None:
                jobs.append(record)

        logger.info(
            "Scraped %d jobs for search_term=%r, location=%r",
            len(jobs),
            search_term,
            location,
        )

    except Exception as exc:
        error_msg = (
            f"Error scraping search_term={search_term!r}, "
            f"location={location!r}, sources={sources!r}: {exc}"
        )
        logger.error(error_msg)
        errors.append(error_msg)

    return jobs, errors


def scrape_all(settings: Settings) -> ScrapeResult:
    """Scrape all search_term × location combinations across configured sources.

    Uses ThreadPoolExecutor with max_workers=4 for concurrent scraping.
    Returns a ScrapeResult with all collected jobs and errors.
    """
    all_jobs: list[JobRecord] = []
    all_errors: list[str] = []

    search_terms = settings.search_terms
    locations = settings.locations
    sources = settings.job_sources

    logger.info(
        "Starting scrape: %d search terms × %d locations across sources %s",
        len(search_terms),
        len(locations),
        sources,
    )

    # Build list of all combinations
    combinations = [
        (term, loc) for term in search_terms for loc in locations
    ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_combo = {
            executor.submit(_scrape_combination, term, loc, sources): (term, loc)
            for term, loc in combinations
        }

        for future in as_completed(future_to_combo):
            term, loc = future_to_combo[future]
            try:
                jobs, errors = future.result()
                all_jobs.extend(jobs)
                all_errors.extend(errors)
            except Exception as exc:
                error_msg = (
                    f"Unexpected error for search_term={term!r}, "
                    f"location={loc!r}: {exc}"
                )
                logger.error(error_msg)
                all_errors.append(error_msg)

    logger.info(
        "Scrape complete: %d total jobs collected, %d errors",
        len(all_jobs),
        len(all_errors),
    )

    return ScrapeResult(jobs=all_jobs, errors=all_errors)
