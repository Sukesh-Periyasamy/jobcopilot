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
from app.services.constants import INTERNSHIP_KEYWORDS, RESEARCH_INSTITUTIONS
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

    def send_intelligence_summary(self, jobs: list[dict], watchlist: list[dict]) -> None:
        """Send a categorized daily intelligence summary via Telegram.

        Builds a summary with 5 sections: Top 10 jobs, Top internships (5),
        Top research openings (5), Watchlist companies hiring, and New ATS
        opportunities (5). Splits into multiple messages if content exceeds
        4096 characters.

        Args:
            jobs: List of job dicts with keys: title, company, location,
                  job_url, date_posted, source_platform.
            watchlist: List of watchlist dicts with keys: company_name,
                       ats_platform, tier.
        """
        if not self._enabled:
            return

        if not jobs:
            logger.info("No jobs to include in intelligence summary.")
            return

        sections = self._build_intelligence_sections(jobs, watchlist)
        messages = self._split_intelligence_messages(sections)

        for message in messages:
            self._send_message(message)

        logger.info(
            "Sent %d intelligence summary message(s) covering %d jobs.",
            len(messages),
            len(jobs),
        )

    def _build_intelligence_sections(
        self, jobs: list[dict], watchlist: list[dict]
    ) -> list[str]:
        """Build the 5 intelligence summary sections.

        Returns a list of section strings (header + entries).
        """
        sections: list[str] = []

        # Section 1: Top 10 Jobs (most recent)
        sorted_jobs = sorted(
            jobs,
            key=lambda j: j.get("date_posted", ""),
            reverse=True,
        )
        top_jobs = sorted_jobs[:10]
        if top_jobs:
            section = "🔝 *Top 10 Jobs*\n\n"
            section += self._format_job_list(top_jobs)
            sections.append(section)

        # Section 2: Top Internships (up to 5)
        internship_keywords_lower = [kw.lower() for kw in INTERNSHIP_KEYWORDS]
        internships = [
            j for j in sorted_jobs
            if any(kw in j.get("title", "").lower() for kw in internship_keywords_lower)
        ][:5]
        if internships:
            section = "🎓 *Top Internships*\n\n"
            section += self._format_job_list(internships)
            sections.append(section)

        # Section 3: Top Research Openings (up to 5)
        research_institutions_lower = [inst.lower() for inst in RESEARCH_INSTITUTIONS]
        research_jobs = [
            j for j in sorted_jobs
            if any(
                inst in j.get("company", "").lower()
                or inst in j.get("description", "").lower()
                for inst in research_institutions_lower
            )
        ][:5]
        if research_jobs:
            section = "🔬 *Top Research Openings*\n\n"
            section += self._format_job_list(research_jobs)
            sections.append(section)

        # Section 4: Watchlist Companies Hiring (sorted by tier)
        if watchlist:
            tier_order = {"tier1": 0, "tier2": 1, "tier3": 2}
            sorted_watchlist = sorted(
                watchlist,
                key=lambda w: tier_order.get(w.get("tier", "tier3"), 2),
            )
            watchlist_company_names = {
                w.get("company_name", "").lower() for w in sorted_watchlist
            }
            # Collect jobs from watchlist companies, preserving tier order
            watchlist_jobs: list[dict] = []
            for entry in sorted_watchlist:
                company_lower = entry.get("company_name", "").lower()
                matching = [
                    j for j in sorted_jobs
                    if j.get("company", "").lower() == company_lower
                ]
                watchlist_jobs.extend(matching)
            if watchlist_jobs:
                section = "⭐ *Watchlist Companies Hiring*\n\n"
                section += self._format_job_list(watchlist_jobs)
                sections.append(section)

        # Section 5: New ATS Opportunities (up to 5)
        ats_platforms = {"workday", "greenhouse", "lever", "ashby", "successfactors"}
        ats_jobs = [
            j for j in sorted_jobs
            if j.get("source_platform", "").lower() in ats_platforms
        ][:5]
        if ats_jobs:
            section = "🆕 *New ATS Opportunities*\n\n"
            section += self._format_job_list(ats_jobs)
            sections.append(section)

        return sections

    def _format_job_list(self, jobs: list[dict]) -> str:
        """Format a list of job dicts into a readable string.

        Each entry: • {title} @ {company} | {location}\n  {job_url}
        """
        lines: list[str] = []
        for job in jobs:
            title = job.get("title", "Unknown")
            company = job.get("company", "Unknown")
            location = job.get("location", "Unknown")
            url = job.get("job_url", "")
            lines.append(f"• {title} @ {company} | {location}\n  {url}")
        return "\n".join(lines) + "\n"

    def _split_intelligence_messages(self, sections: list[str]) -> list[str]:
        """Split intelligence sections into messages respecting 4096 char limit.

        Tries to keep sections together. If a single section exceeds the limit,
        it is split at line boundaries.
        """
        messages: list[str] = []
        current_message = ""

        for section in sections:
            # If adding this section fits, append it
            if len(current_message) + len(section) + 1 <= self.MAX_MESSAGE_LENGTH:
                current_message += section + "\n"
            else:
                # Save current message if non-empty
                if current_message.strip():
                    messages.append(current_message.strip())

                # If the section itself fits in a single message, start fresh
                if len(section) <= self.MAX_MESSAGE_LENGTH:
                    current_message = section + "\n"
                else:
                    # Section is too large, split by lines
                    current_message = ""
                    for line in section.split("\n"):
                        if len(current_message) + len(line) + 1 > self.MAX_MESSAGE_LENGTH:
                            if current_message.strip():
                                messages.append(current_message.strip())
                            current_message = line + "\n"
                        else:
                            current_message += line + "\n"

        if current_message.strip():
            messages.append(current_message.strip())

        return messages

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
