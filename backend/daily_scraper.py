"""Daily scraper entry point for Render Cron Job.

Triggered daily at 08:00 AM IST. Executes the full scrape-store-notify
workflow with retry logic (3 retries, 60s initial backoff).
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from app.config.settings import Settings
from app.database.repository import JobsRepository
from app.models.job import JobRecord, ScrapeHistoryEntry, ScrapeResult
from app.scraper.jobhive_scraper import scrape_jobhive
from app.services.notifier import TelegramNotifier
from app.utils.logger import setup_logging
from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


def _run_jobspy(settings: Settings) -> ScrapeResult:
    """Wrapper for scrape_all with error handling.

    Returns empty ScrapeResult on failure so the orchestrator
    can proceed with JobHive results alone.
    """
    try:
        from app.scraper.scraper import scrape_all
        return scrape_all(settings)
    except ImportError as exc:
        logger.warning("JobSpy not available (missing dependency): %s", exc)
        return ScrapeResult(jobs=[], errors=[f"JobSpy not available: {exc}"])
    except Exception as exc:
        logger.error("JobSpy scraper failed entirely: %s", exc)
        return ScrapeResult(jobs=[], errors=[f"JobSpy scraper failed: {exc}"])


def _run_jobhive(settings: Settings) -> ScrapeResult:
    """Wrapper for scrape_jobhive with error handling.

    Returns empty ScrapeResult on failure so the orchestrator
    can proceed with JobSpy results alone.
    """
    try:
        return scrape_jobhive(settings)
    except Exception as exc:
        logger.error("JobHive scraper failed entirely: %s", exc)
        return ScrapeResult(jobs=[], errors=[f"JobHive scraper failed: {exc}"])


def _job_record_to_dict(job: JobRecord) -> dict:
    """Convert a JobRecord to a dict suitable for the intelligence summary.

    Args:
        job: JobRecord instance to convert.

    Returns:
        Dict with keys: title, company, location, job_url, date_posted,
        source_platform, description.
    """
    return {
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "job_url": job.job_url,
        "date_posted": job.date_posted,
        "source_platform": job.source_platform,
        "description": job.description,
    }


def _run_workflow() -> None:
    """Execute the full scrape-store-notify workflow with both scrapers.

    Steps:
    1. Load settings
    2. Run JobSpy scraper (with error handling)
    3. Run JobHive scraper (with error handling)
    4. Merge results from both scrapers
    5. Bulk insert jobs into MongoDB (deduplication via unique index)
    6. Record scrape history
    7. Send Telegram notifications for new un-notified jobs
    8. Send watchlist alerts for jobs matching watchlist companies
    9. Mark notified jobs
    10. Send intelligence summary
    """
    # 1. Load settings
    settings = Settings.load()

    # 2. Run JobSpy scraper
    logger.info("Starting JobSpy scrape for all configured search terms and locations.")
    jobspy_result = _run_jobspy(settings)
    logger.info(
        "JobSpy scrape completed: %d jobs collected, %d errors.",
        len(jobspy_result.jobs),
        len(jobspy_result.errors),
    )

    # 3. Run JobHive scraper
    logger.info("Starting JobHive scrape for all configured ATS platforms.")
    jobhive_result = _run_jobhive(settings)
    logger.info(
        "JobHive scrape completed: %d jobs collected, %d errors.",
        len(jobhive_result.jobs),
        len(jobhive_result.errors),
    )

    # 4. Merge results
    merged_jobs = jobspy_result.jobs + jobhive_result.jobs
    merged_errors = jobspy_result.errors + jobhive_result.errors
    merged_result = ScrapeResult(jobs=merged_jobs, errors=merged_errors)
    logger.info(
        "Merged scrape results: %d total jobs, %d total errors.",
        len(merged_result.jobs),
        len(merged_result.errors),
    )

    # 5. Bulk insert to MongoDB
    repo = JobsRepository()
    insert_result = repo.bulk_insert(merged_result.jobs)
    logger.info(
        "Bulk insert: %d new, %d duplicates skipped.",
        insert_result.inserted_count,
        insert_result.duplicates_skipped,
    )

    # 6. Record scrape history
    history_entry = ScrapeHistoryEntry(
        jobs_found=len(merged_result.jobs),
        duplicates_skipped=insert_result.duplicates_skipped,
        errors=merged_result.errors,
    )
    repo.record_scrape_history(history_entry)

    # 7. Send Telegram notifications for new un-notified jobs
    notifier = TelegramNotifier(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
    )

    new_jobs = insert_result.new_jobs
    if new_jobs:
        notifier.notify_new_jobs(new_jobs)

        # 8. Send watchlist alerts for matching companies (case-insensitive)
        watchlist_entries = repo.get_watchlist()
        watchlist_lower = [entry["company_name"].lower() for entry in watchlist_entries]

        for job in new_jobs:
            if job.company.lower() in watchlist_lower:
                notifier.notify_watchlist_match(job)

        # 9. Mark notified jobs
        notified_urls = [job.job_url for job in new_jobs]
        notifier.mark_notified(notified_urls)
    else:
        logger.info("No new jobs to notify.")

    # 10. Send intelligence summary
    try:
        # Get watchlist entries (may already be loaded above if new_jobs existed)
        if not new_jobs:
            watchlist_entries = repo.get_watchlist()

        # Determine jobs to include in the summary
        if new_jobs:
            summary_jobs = [_job_record_to_dict(job) for job in new_jobs]
        else:
            # No new jobs this cycle — use recent jobs from the database
            recent_jobs = repo.get_recent_jobs(limit=50)
            summary_jobs = [_job_record_to_dict(job) for job in recent_jobs]

        notifier.send_intelligence_summary(summary_jobs, watchlist_entries)
    except Exception as exc:
        logger.error("Intelligence summary failed (non-fatal): %s", exc)


def main() -> None:
    """Entry point for the daily scraper cron job.

    Sets up logging, logs start/end time, and wraps the workflow
    with retry logic (3 retries, 60s initial backoff).
    """
    setup_logging()

    start_time = datetime.now(timezone.utc)
    logger.info("Daily scraper started at %s", start_time.isoformat())

    try:
        retry_with_backoff(
            fn=_run_workflow,
            max_retries=3,
            initial_backoff=60.0,
        )
        end_time = datetime.now(timezone.utc)
        logger.info(
            "Daily scraper completed successfully at %s (duration: %s)",
            end_time.isoformat(),
            str(end_time - start_time),
        )
    except Exception as exc:
        end_time = datetime.now(timezone.utc)
        logger.error(
            "Daily scraper FAILED at %s after all retries (duration: %s). "
            "Last error: %s",
            end_time.isoformat(),
            str(end_time - start_time),
            exc,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
