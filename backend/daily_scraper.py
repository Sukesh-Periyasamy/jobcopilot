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
from app.models.job import ScrapeHistoryEntry
from app.scraper.scraper import scrape_all
from app.services.notifier import TelegramNotifier
from app.utils.logger import setup_logging
from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


def _run_workflow() -> None:
    """Execute the full scrape-store-notify workflow.

    Steps:
    1. Load settings
    2. Run scrape_all() to collect jobs from all sources
    3. Bulk insert jobs into MongoDB (deduplication via unique index)
    4. Record scrape history
    5. Send Telegram notifications for new un-notified jobs
    6. Send watchlist alerts for jobs matching watchlist companies
    7. Mark notified jobs
    """
    # 1. Load settings
    settings = Settings.load()

    # 2. Run scraper
    logger.info("Starting scrape for all configured search terms and locations.")
    scrape_result = scrape_all(settings)
    logger.info(
        "Scrape completed: %d jobs collected, %d errors.",
        len(scrape_result.jobs),
        len(scrape_result.errors),
    )

    # 3. Bulk insert to MongoDB
    repo = JobsRepository()
    insert_result = repo.bulk_insert(scrape_result.jobs)
    logger.info(
        "Bulk insert: %d new, %d duplicates skipped.",
        insert_result.inserted_count,
        insert_result.duplicates_skipped,
    )

    # 4. Record scrape history
    history_entry = ScrapeHistoryEntry(
        jobs_found=len(scrape_result.jobs),
        duplicates_skipped=insert_result.duplicates_skipped,
        errors=scrape_result.errors,
    )
    repo.record_scrape_history(history_entry)

    # 5. Send Telegram notifications for new un-notified jobs
    notifier = TelegramNotifier(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
    )

    new_jobs = insert_result.new_jobs
    if new_jobs:
        notifier.notify_new_jobs(new_jobs)

        # 6. Send watchlist alerts for matching companies (case-insensitive)
        watchlist = repo.get_watchlist()
        watchlist_lower = [w.lower() for w in watchlist]

        for job in new_jobs:
            if job.company.lower() in watchlist_lower:
                notifier.notify_watchlist_match(job)

        # 7. Mark notified jobs
        notified_urls = [job.job_url for job in new_jobs]
        notifier.mark_notified(notified_urls)
    else:
        logger.info("No new jobs to notify.")


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
