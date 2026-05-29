"""Telegram notification service for JobCopilot Engine.

Sends daily job summaries and watchlist alerts via Telegram Bot API.
Gracefully degrades to no-ops when credentials are not configured.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import requests

from app.database.connection import get_database
from app.utils.retry import retry_with_backoff

if TYPE_CHECKING:
    from app.models.job import JobRecord

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramNotifier:
    """Sends Telegram notifications for new jobs and watchlist matches.

    If bot_token or chat_id is missing, all send operations become
    no-ops with a warning log. Uses retry_with_backoff for API calls.
    """

    MAX_MESSAGE_LENGTH = 4096

    def __init__(self, bot_token: str | None, chat_id: str | None) -> None:
        """Initialize the notifier.

        Args:
            bot_token: Telegram Bot API token. If None or empty, notifications are disabled.
            chat_id: Telegram chat ID to send messages to. If None or empty, notifications are disabled.
        """
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._enabled = bool(bot_token and chat_id)

        if not self._enabled:
            missing = []
            if not bot_token:
                missing.append("TELEGRAM_BOT_TOKEN")
            if not chat_id:
                missing.append("TELEGRAM_CHAT_ID")
            logger.warning(
                "Telegram notifications disabled. Missing: %s",
                ", ".join(missing),
            )

    def notify_new_jobs(self, jobs: list[JobRecord]) -> None:
        """Send a summary of new jobs via Telegram.

        Formats each job entry with title, company, location, and job_url.
        Splits into multiple messages if content exceeds 4096 characters.

        Args:
            jobs: List of new JobRecord instances to notify about.
        """
        if not self._enabled:
            logger.warning("Skipping new jobs notification: Telegram not configured.")
            return

        if not jobs:
            logger.info("No new jobs to notify.")
            return

        header = f"🆕 *{len(jobs)} New Job(s) Found*\n\n"
        entries = [self._format_job_entry(job) for job in jobs]

        messages = self._split_messages(header, entries)

        for message in messages:
            self._send_message(message)

        logger.info("Sent %d notification message(s) for %d new jobs.",
                    len(messages), len(jobs))

    def notify_watchlist_match(self, job: JobRecord) -> None:
        """Send a separate alert for a watchlist company match.

        Args:
            job: JobRecord that matched a watchlist company.
        """
        if not self._enabled:
            logger.warning("Skipping watchlist notification: Telegram not configured.")
            return

        message = (
            f"⭐ *Watchlist Alert*\n\n"
            f"A job from a watched company was found:\n\n"
            f"📌 *{job.title}*\n"
            f"🏢 {job.company}\n"
            f"📍 {job.location}\n"
            f"🔗 {job.job_url}"
        )

        self._send_message(message)
        logger.info("Sent watchlist alert for %s at %s.", job.title, job.company)

    def mark_notified(self, job_urls: list[str]) -> None:
        """Track which jobs have been notified to avoid re-sending.

        Records job URLs in the notifications collection and updates
        the notified field in the jobs collection.

        Args:
            job_urls: List of job URLs that have been notified.
        """
        if not job_urls:
            return

        db = get_database()
        notifications = db["notifications"]
        jobs_collection = db["jobs"]

        now = datetime.now(timezone.utc).isoformat()

        # Insert into notifications collection (skip duplicates)
        docs = [{"job_url": url, "notified_at": now} for url in job_urls]
        try:
            notifications.insert_many(docs, ordered=False)
        except Exception:
            # Some may already exist (duplicates), that's fine
            pass

        # Update notified field in jobs collection
        jobs_collection.update_many(
            {"job_url": {"$in": job_urls}},
            {"$set": {"notified": True}},
        )

        logger.info("Marked %d job(s) as notified.", len(job_urls))

    def _format_job_entry(self, job: JobRecord) -> str:
        """Format a single job entry for the notification message.

        Args:
            job: JobRecord to format.

        Returns:
            Formatted string with job details.
        """
        return (
            f"📌 *{job.title}*\n"
            f"🏢 {job.company}\n"
            f"📍 {job.location}\n"
            f"🔗 {job.job_url}\n"
        )

    def _split_messages(self, header: str, entries: list[str]) -> list[str]:
        """Split job entries into messages that fit within Telegram's limit.

        Each message starts with the header (for the first message) or a
        continuation indicator. No single job entry is split across messages.

        Args:
            header: Header text for the first message.
            entries: List of formatted job entry strings.

        Returns:
            List of message strings, each ≤ 4096 characters.
        """
        messages: list[str] = []
        current_message = header

        for entry in entries:
            # Check if adding this entry would exceed the limit
            if len(current_message) + len(entry) + 1 > self.MAX_MESSAGE_LENGTH:
                # Save current message and start a new one
                if current_message.strip():
                    messages.append(current_message.strip())
                current_message = f"📋 *Continued...*\n\n{entry}"
            else:
                current_message += entry + "\n"

        # Add the last message if it has content
        if current_message.strip():
            messages.append(current_message.strip())

        return messages

    def _send_message(self, text: str) -> None:
        """Send a message via Telegram Bot API with retry logic.

        Uses retry_with_backoff with 3 retries and 1s initial backoff.

        Args:
            text: Message text to send (supports Markdown).
        """
        url = TELEGRAM_API_URL.format(token=self._bot_token)
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }

        def _do_send() -> None:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

        try:
            retry_with_backoff(fn=_do_send, max_retries=3, initial_backoff=1.0)
        except Exception as e:
            logger.error(
                "Failed to send Telegram message after retries: %s", e
            )
