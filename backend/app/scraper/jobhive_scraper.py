"""JobHive scraper module for ATS platform job collection.

Queries jobhive-py for each configured ATS platform (Greenhouse, Lever,
Ashby, Workday, SuccessFactors), normalizes results into JobRecords,
and handles per-platform failures gracefully.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import pandas as pd

from jobhive import ATSType, Client

from app.config.settings import Settings
from app.models.job import JobRecord, ScrapeResult

logger = logging.getLogger(__name__)

# ATS platforms to query via jobhive-py
ATS_PLATFORMS: list[str] = [
    "greenhouse",
    "lever",
    "ashby",
    "workday",
    "successfactors",
]


def _normalize_jobhive_result(
    raw: dict, platform: str, search_term: str
) -> JobRecord | None:
    """Normalize a single jobhive-py result dict into a JobRecord.

    Sets source_type="jobhive", source_platform=platform (lowercase).
    Returns None if required fields (title, job_url) are missing.
    Missing optional fields (description, job_type, salary, date_posted)
    default to empty string.
    """
    title = str(raw.get("title", "") or "").strip()
    job_url = str(raw.get("url", "") or "").strip()

    if not title or not job_url:
        logger.warning(
            "Skipping invalid JobHive record: missing title=%r or job_url=%r",
            title,
            job_url,
        )
        return None

    now_iso = datetime.now(timezone.utc).isoformat()

    # Build salary string from salary fields
    salary = ""
    salary_min = raw.get("salary_min")
    salary_max = raw.get("salary_max")
    salary_currency = raw.get("salary_currency")

    if salary_min is not None and salary_max is not None:
        try:
            if pd.notna(salary_min) and pd.notna(salary_max):
                currency_str = str(salary_currency) if salary_currency and pd.notna(salary_currency) else ""
                salary = f"{currency_str} {salary_min}-{salary_max}".strip()
        except (TypeError, ValueError):
            salary = ""

    # Normalize date_posted from posted_at
    date_posted = ""
    posted_at = raw.get("posted_at")
    if posted_at and (not isinstance(posted_at, float) or pd.notna(posted_at)):
        try:
            if isinstance(posted_at, str):
                # Parse ISO format and extract date
                dt = datetime.fromisoformat(posted_at)
                date_posted = dt.strftime("%Y-%m-%d")
            else:
                date_posted = str(posted_at).strip()
        except (ValueError, TypeError):
            date_posted = ""

    return JobRecord(
        title=title,
        company=str(raw.get("company", "") or "").strip(),
        location=str(raw.get("location", "") or "").strip(),
        source=platform.lower(),
        job_url=job_url,
        description=str(raw.get("description", "") or "").strip(),
        job_type=str(raw.get("employment_type", "") or "").strip(),
        salary=salary,
        date_posted=date_posted,
        search_term=search_term,
        source_type="jobhive",
        source_platform=platform.lower(),
        created_at=now_iso,
        updated_at=now_iso,
    )


def scrape_jobhive(settings: Settings) -> ScrapeResult:
    """Query all configured ATS platforms via jobhive-py.

    Iterates over platforms (greenhouse, lever, ashby, workday, successfactors),
    queries each with configured search terms, normalizes results, and collects
    errors. Continues on per-platform failures.

    Returns:
        ScrapeResult with normalized JobRecords and any error messages.
    """
    all_jobs: list[JobRecord] = []
    all_errors: list[str] = []

    search_terms = settings.search_terms

    logger.info(
        "Starting JobHive scrape: %d search terms across %d ATS platforms",
        len(search_terms),
        len(ATS_PLATFORMS),
    )

    # Load optional company board identifiers from environment
    # Format: JOBHIVE_{PLATFORM}_COMPANIES = "company1,company2"
    platform_companies: dict[str, list[str]] = {}
    for platform in ATS_PLATFORMS:
        env_key = f"JOBHIVE_{platform.upper()}_COMPANIES"
        companies_str = os.environ.get(env_key, "").strip()
        if companies_str:
            platform_companies[platform] = [
                c.strip() for c in companies_str.split(",") if c.strip()
            ]

    try:
        client = Client()
    except Exception as exc:
        error_msg = f"Failed to initialize JobHive client: {exc}"
        logger.error(error_msg)
        all_errors.append(error_msg)
        return ScrapeResult(jobs=all_jobs, errors=all_errors)

    try:
        for platform in ATS_PLATFORMS:
            try:
                platform_jobs = _scrape_platform(
                    client, platform, search_terms, platform_companies.get(platform)
                )
                all_jobs.extend(platform_jobs)
                logger.info(
                    "JobHive platform=%s: collected %d jobs",
                    platform,
                    len(platform_jobs),
                )
            except Exception as exc:
                error_msg = (
                    f"JobHive error for platform={platform!r}: {exc}"
                )
                logger.error(error_msg)
                all_errors.append(error_msg)
    finally:
        try:
            client.close()
        except Exception:
            pass

    logger.info(
        "JobHive scrape complete: %d total jobs collected, %d errors",
        len(all_jobs),
        len(all_errors),
    )

    return ScrapeResult(jobs=all_jobs, errors=all_errors)


def _scrape_platform(
    client: Client,
    platform: str,
    search_terms: list[str],
    companies: list[str] | None,
) -> list[JobRecord]:
    """Scrape a single ATS platform for all search terms.

    If company board identifiers are configured for this platform,
    queries are scoped to those companies. Otherwise, queries the
    platform broadly with each search term.

    Returns a list of normalized JobRecords.
    """
    jobs: list[JobRecord] = []

    for search_term in search_terms:
        try:
            if companies:
                # Query each configured company on this platform
                for company in companies:
                    df = client.search(
                        query=search_term,
                        ats=platform,
                        company=company,
                        limit=15,
                    )
                    jobs.extend(_process_dataframe(df, platform, search_term))
            else:
                # Query the platform broadly
                df = client.search(
                    query=search_term,
                    ats=platform,
                    limit=15,
                )
                jobs.extend(_process_dataframe(df, platform, search_term))

        except Exception as exc:
            logger.warning(
                "JobHive search failed: platform=%s, search_term=%r: %s",
                platform,
                search_term,
                exc,
            )
            # Continue with next search term
            continue

    return jobs


def _process_dataframe(
    df: pd.DataFrame, platform: str, search_term: str
) -> list[JobRecord]:
    """Process a jobhive-py DataFrame into a list of JobRecords."""
    records: list[JobRecord] = []

    if df is None or df.empty:
        return records

    for _, row in df.iterrows():
        raw = row.to_dict()
        record = _normalize_jobhive_result(raw, platform, search_term)
        if record is not None:
            records.append(record)

    return records
