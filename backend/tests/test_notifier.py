"""Unit tests for the TelegramNotifier service."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from app.models.job import JobRecord
from app.services.notifier import TelegramNotifier


def _make_job(title="Engineer", company="Acme", location="Bangalore", url="https://example.com/job1"):
    """Helper to create a JobRecord for testing."""
    return JobRecord(
        title=title,
        company=company,
        location=location,
        source="linkedin",
        job_url=url,
    )


class TestTelegramNotifierInit:
    """Tests for TelegramNotifier initialization."""

    def test_enabled_when_both_credentials_present(self):
        """Notifier is enabled when both token and chat_id are provided."""
        notifier = TelegramNotifier("token123", "chat456")
        assert notifier._enabled is True

    def test_disabled_when_token_missing(self, caplog):
        """Notifier is disabled and logs warning when token is missing."""
        with caplog.at_level(logging.WARNING):
            notifier = TelegramNotifier(None, "chat456")
        assert notifier._enabled is False
        assert "TELEGRAM_BOT_TOKEN" in caplog.text

    def test_disabled_when_chat_id_missing(self, caplog):
        """Notifier is disabled and logs warning when chat_id is missing."""
        with caplog.at_level(logging.WARNING):
            notifier = TelegramNotifier("token123", None)
        assert notifier._enabled is False
        assert "TELEGRAM_CHAT_ID" in caplog.text

    def test_disabled_when_both_missing(self, caplog):
        """Notifier is disabled and logs warning when both are missing."""
        with caplog.at_level(logging.WARNING):
            notifier = TelegramNotifier(None, None)
        assert notifier._enabled is False
        assert "TELEGRAM_BOT_TOKEN" in caplog.text
        assert "TELEGRAM_CHAT_ID" in caplog.text

    def test_disabled_when_token_empty_string(self, caplog):
        """Notifier is disabled when token is empty string."""
        with caplog.at_level(logging.WARNING):
            notifier = TelegramNotifier("", "chat456")
        assert notifier._enabled is False


class TestNotifyNewJobs:
    """Tests for notify_new_jobs method."""

    @patch("app.services.notifier.requests.post")
    @patch("app.services.notifier.retry_with_backoff")
    def test_sends_message_for_new_jobs(self, mock_retry, mock_post):
        """Sends a formatted message when new jobs are provided."""
        mock_retry.side_effect = lambda fn, **kwargs: fn()
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()

        notifier = TelegramNotifier("token123", "chat456")
        jobs = [_make_job()]

        notifier.notify_new_jobs(jobs)

        mock_retry.assert_called_once()

    def test_noop_when_disabled(self, caplog):
        """Does nothing when notifier is disabled."""
        notifier = TelegramNotifier(None, None)
        with caplog.at_level(logging.WARNING):
            notifier.notify_new_jobs([_make_job()])
        assert "Skipping new jobs notification" in caplog.text

    @patch("app.services.notifier.requests.post")
    @patch("app.services.notifier.retry_with_backoff")
    def test_no_message_for_empty_jobs(self, mock_retry, mock_post):
        """Does not send a message when jobs list is empty."""
        notifier = TelegramNotifier("token123", "chat456")
        notifier.notify_new_jobs([])
        mock_retry.assert_not_called()

    @patch("app.services.notifier.requests.post")
    @patch("app.services.notifier.retry_with_backoff")
    def test_splits_long_messages(self, mock_retry, mock_post):
        """Splits messages when content exceeds 4096 characters."""
        mock_retry.side_effect = lambda fn, **kwargs: fn()
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()

        notifier = TelegramNotifier("token123", "chat456")
        # Create many jobs to exceed 4096 chars
        jobs = [_make_job(title=f"Job Title Number {i} " * 10, url=f"https://example.com/job{i}")
                for i in range(50)]

        notifier.notify_new_jobs(jobs)

        # Should have been called multiple times for split messages
        assert mock_retry.call_count > 1


class TestNotifyWatchlistMatch:
    """Tests for notify_watchlist_match method."""

    @patch("app.services.notifier.requests.post")
    @patch("app.services.notifier.retry_with_backoff")
    def test_sends_watchlist_alert(self, mock_retry, mock_post):
        """Sends a watchlist alert message for a matching job."""
        mock_retry.side_effect = lambda fn, **kwargs: fn()
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()

        notifier = TelegramNotifier("token123", "chat456")
        job = _make_job(company="Siemens Healthineers")

        notifier.notify_watchlist_match(job)

        mock_retry.assert_called_once()

    def test_noop_when_disabled(self, caplog):
        """Does nothing when notifier is disabled."""
        notifier = TelegramNotifier(None, None)
        with caplog.at_level(logging.WARNING):
            notifier.notify_watchlist_match(_make_job())
        assert "Skipping watchlist notification" in caplog.text


class TestMarkNotified:
    """Tests for mark_notified method."""

    @patch("app.services.notifier.get_database")
    def test_marks_jobs_as_notified(self, mock_get_db):
        """Updates notifications collection and jobs collection."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_notifications = MagicMock()
        mock_jobs = MagicMock()
        mock_db.__getitem__ = lambda self, key: {
            "notifications": mock_notifications,
            "jobs": mock_jobs,
        }[key]

        notifier = TelegramNotifier("token123", "chat456")
        urls = ["https://example.com/job1", "https://example.com/job2"]

        notifier.mark_notified(urls)

        mock_notifications.insert_many.assert_called_once()
        mock_jobs.update_many.assert_called_once()

    @patch("app.services.notifier.get_database")
    def test_noop_for_empty_urls(self, mock_get_db):
        """Does nothing when job_urls list is empty."""
        notifier = TelegramNotifier("token123", "chat456")
        notifier.mark_notified([])
        mock_get_db.assert_not_called()


class TestMessageSplitting:
    """Tests for the _split_messages internal method."""

    def test_single_message_within_limit(self):
        """Returns a single message when content fits within 4096 chars."""
        notifier = TelegramNotifier("token", "chat")
        header = "Header\n\n"
        entries = ["Entry 1\n", "Entry 2\n"]

        messages = notifier._split_messages(header, entries)

        assert len(messages) == 1
        assert "Header" in messages[0]
        assert "Entry 1" in messages[0]
        assert "Entry 2" in messages[0]

    def test_splits_when_exceeding_limit(self):
        """Splits into multiple messages when content exceeds limit."""
        notifier = TelegramNotifier("token", "chat")
        header = "H" * 100 + "\n\n"
        # Each entry is ~200 chars, 25 entries = ~5000 chars > 4096
        entries = [f"{'X' * 190}\n" for _ in range(25)]

        messages = notifier._split_messages(header, entries)

        assert len(messages) > 1
        for msg in messages:
            assert len(msg) <= TelegramNotifier.MAX_MESSAGE_LENGTH

    def test_no_job_split_across_messages(self):
        """No single job entry is split across messages."""
        notifier = TelegramNotifier("token", "chat")
        header = "Header\n\n"
        entries = [f"Job {i}: {'A' * 100}\n" for i in range(50)]

        messages = notifier._split_messages(header, entries)

        # Each entry should appear in exactly one message
        for entry in entries:
            entry_stripped = entry.strip()
            containing = [m for m in messages if entry_stripped in m]
            assert len(containing) == 1


class TestSendMessage:
    """Tests for the _send_message internal method."""

    @patch("app.services.notifier.retry_with_backoff")
    def test_uses_retry_with_backoff(self, mock_retry):
        """Uses retry_with_backoff with 3 retries and 1s initial backoff."""
        mock_retry.side_effect = lambda fn, **kwargs: fn()

        with patch("app.services.notifier.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            mock_post.return_value.raise_for_status = MagicMock()

            notifier = TelegramNotifier("mytoken", "mychat")
            notifier._send_message("Hello")

            mock_retry.assert_called_once()
            call_kwargs = mock_retry.call_args
            assert call_kwargs.kwargs["max_retries"] == 3
            assert call_kwargs.kwargs["initial_backoff"] == 1.0

    @patch("app.services.notifier.retry_with_backoff")
    def test_logs_error_on_failure(self, mock_retry, caplog):
        """Logs error when all retries fail."""
        mock_retry.side_effect = Exception("API down")

        notifier = TelegramNotifier("mytoken", "mychat")
        with caplog.at_level(logging.ERROR):
            notifier._send_message("Hello")

        assert "Failed to send Telegram message" in caplog.text
