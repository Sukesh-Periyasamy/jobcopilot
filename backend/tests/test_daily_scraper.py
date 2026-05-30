"""Unit tests for the daily scraper orchestrator (daily_scraper.py).

Tests the _run_jobspy, _run_jobhive wrapper functions and the _run_workflow
orchestrator logic, verifying partial failure handling and merged result behavior.

Requirements: 2.5, 2.6
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.models.job import BulkInsertResult, JobRecord, ScrapeHistoryEntry, ScrapeResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_job(title: str, source_type: str = "jobspy", platform: str = "linkedin") -> JobRecord:
    """Create a minimal JobRecord for testing."""
    return JobRecord(
        title=title,
        company="TestCo",
        location="Remote",
        source=platform,
        job_url=f"https://example.com/{title.replace(' ', '-').lower()}",
        source_type=source_type,
        source_platform=platform,
    )


def _make_settings():
    """Create a mock Settings instance."""
    from app.config.settings import Settings

    return Settings(
        mongodb_uri="mongodb://localhost:27017",
        database_name="testdb",
        search_terms=["Engineer"],
        locations=["Remote"],
        job_sources=["linkedin"],
        schedule_time="08:00",
    )


# ---------------------------------------------------------------------------
# Tests for _run_jobhive wrapper
# ---------------------------------------------------------------------------


class TestRunJobhive:
    """Tests for the _run_jobhive wrapper function."""

    @patch("daily_scraper.scrape_jobhive")
    def test_returns_scrape_result_on_success(self, mock_scrape):
        """When scrape_jobhive succeeds, _run_jobhive returns its result."""
        from daily_scraper import _run_jobhive

        expected = ScrapeResult(
            jobs=[_make_job("JobHive Job", "jobhive", "greenhouse")],
            errors=[],
        )
        mock_scrape.return_value = expected
        settings = _make_settings()

        result = _run_jobhive(settings)

        assert result is expected
        mock_scrape.assert_called_once_with(settings)

    @patch("daily_scraper.scrape_jobhive")
    def test_returns_empty_result_on_exception(self, mock_scrape):
        """When scrape_jobhive raises an exception, _run_jobhive returns empty ScrapeResult with error."""
        from daily_scraper import _run_jobhive

        mock_scrape.side_effect = RuntimeError("JobHive API timeout")
        settings = _make_settings()

        result = _run_jobhive(settings)

        assert isinstance(result, ScrapeResult)
        assert result.jobs == []
        assert len(result.errors) == 1
        assert "JobHive scraper failed" in result.errors[0]
        assert "JobHive API timeout" in result.errors[0]


# ---------------------------------------------------------------------------
# Tests for _run_jobspy wrapper
# ---------------------------------------------------------------------------


class TestRunJobspy:
    """Tests for the _run_jobspy wrapper function."""

    @patch("daily_scraper.scrape_all")
    def test_returns_scrape_result_on_success(self, mock_scrape):
        """When scrape_all succeeds, _run_jobspy returns its result."""
        from daily_scraper import _run_jobspy

        expected = ScrapeResult(
            jobs=[_make_job("JobSpy Job", "jobspy", "linkedin")],
            errors=[],
        )
        mock_scrape.return_value = expected
        settings = _make_settings()

        result = _run_jobspy(settings)

        assert result is expected
        mock_scrape.assert_called_once_with(settings)

    @patch("daily_scraper.scrape_all")
    def test_returns_empty_result_on_exception(self, mock_scrape):
        """When scrape_all raises an exception, _run_jobspy returns empty ScrapeResult with error."""
        from daily_scraper import _run_jobspy

        mock_scrape.side_effect = ConnectionError("Network unreachable")
        settings = _make_settings()

        result = _run_jobspy(settings)

        assert isinstance(result, ScrapeResult)
        assert result.jobs == []
        assert len(result.errors) == 1
        assert "JobSpy scraper failed" in result.errors[0]
        assert "Network unreachable" in result.errors[0]


# ---------------------------------------------------------------------------
# Tests for _run_workflow orchestrator
# ---------------------------------------------------------------------------


class TestRunWorkflow:
    """Tests for the _run_workflow orchestrator function."""

    @patch("daily_scraper.TelegramNotifier")
    @patch("daily_scraper.JobsRepository")
    @patch("daily_scraper.Settings.load")
    @patch("daily_scraper.scrape_jobhive")
    @patch("daily_scraper.scrape_all")
    def test_jobhive_fails_jobspy_succeeds(
        self, mock_jobspy, mock_jobhive, mock_settings_load, mock_repo_cls, mock_notifier_cls
    ):
        """When JobHive raises exception, workflow proceeds with JobSpy results alone (Req 2.5)."""
        from daily_scraper import _run_workflow

        # Setup
        settings = _make_settings()
        mock_settings_load.return_value = settings

        jobspy_jobs = [_make_job("JobSpy Job 1"), _make_job("JobSpy Job 2")]
        mock_jobspy.return_value = ScrapeResult(jobs=jobspy_jobs, errors=[])
        mock_jobhive.side_effect = RuntimeError("JobHive API down")

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.bulk_insert.return_value = BulkInsertResult(
            inserted_count=2, duplicates_skipped=0, new_jobs=jobspy_jobs
        )
        mock_repo.get_watchlist.return_value = []

        mock_notifier = MagicMock()
        mock_notifier_cls.return_value = mock_notifier

        # Execute
        _run_workflow()

        # Verify: bulk_insert called with only JobSpy jobs
        bulk_insert_call = mock_repo.bulk_insert.call_args[0][0]
        assert len(bulk_insert_call) == 2
        assert all(j.source_type == "jobspy" for j in bulk_insert_call)

        # Verify: scrape history records the combined count (2 jobs from jobspy + 0 from jobhive)
        history_call = mock_repo.record_scrape_history.call_args[0][0]
        assert isinstance(history_call, ScrapeHistoryEntry)
        assert history_call.jobs_found == 2
        # Errors should include the JobHive failure
        assert any("JobHive" in e for e in history_call.errors)

    @patch("daily_scraper.TelegramNotifier")
    @patch("daily_scraper.JobsRepository")
    @patch("daily_scraper.Settings.load")
    @patch("daily_scraper.scrape_jobhive")
    @patch("daily_scraper.scrape_all")
    def test_jobspy_fails_jobhive_succeeds(
        self, mock_jobspy, mock_jobhive, mock_settings_load, mock_repo_cls, mock_notifier_cls
    ):
        """When JobSpy raises exception, workflow proceeds with JobHive results alone (Req 2.6)."""
        from daily_scraper import _run_workflow

        # Setup
        settings = _make_settings()
        mock_settings_load.return_value = settings

        mock_jobspy.side_effect = ConnectionError("JobSpy network error")

        jobhive_jobs = [_make_job("JobHive Job 1", "jobhive", "greenhouse")]
        mock_jobhive.return_value = ScrapeResult(jobs=jobhive_jobs, errors=[])

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.bulk_insert.return_value = BulkInsertResult(
            inserted_count=1, duplicates_skipped=0, new_jobs=jobhive_jobs
        )
        mock_repo.get_watchlist.return_value = []

        mock_notifier = MagicMock()
        mock_notifier_cls.return_value = mock_notifier

        # Execute
        _run_workflow()

        # Verify: bulk_insert called with only JobHive jobs
        bulk_insert_call = mock_repo.bulk_insert.call_args[0][0]
        assert len(bulk_insert_call) == 1
        assert bulk_insert_call[0].source_type == "jobhive"

        # Verify: scrape history records the combined count
        history_call = mock_repo.record_scrape_history.call_args[0][0]
        assert history_call.jobs_found == 1
        # Errors should include the JobSpy failure
        assert any("JobSpy" in e for e in history_call.errors)

    @patch("daily_scraper.TelegramNotifier")
    @patch("daily_scraper.JobsRepository")
    @patch("daily_scraper.Settings.load")
    @patch("daily_scraper.scrape_jobhive")
    @patch("daily_scraper.scrape_all")
    def test_both_scrapers_succeed(
        self, mock_jobspy, mock_jobhive, mock_settings_load, mock_repo_cls, mock_notifier_cls
    ):
        """When both scrapers succeed, merged result has combined jobs and errors."""
        from daily_scraper import _run_workflow

        # Setup
        settings = _make_settings()
        mock_settings_load.return_value = settings

        jobspy_jobs = [_make_job("JobSpy Job 1"), _make_job("JobSpy Job 2")]
        jobhive_jobs = [
            _make_job("JobHive Job 1", "jobhive", "greenhouse"),
            _make_job("JobHive Job 2", "jobhive", "lever"),
            _make_job("JobHive Job 3", "jobhive", "workday"),
        ]
        mock_jobspy.return_value = ScrapeResult(
            jobs=jobspy_jobs, errors=["minor jobspy warning"]
        )
        mock_jobhive.return_value = ScrapeResult(
            jobs=jobhive_jobs, errors=["minor jobhive warning"]
        )

        all_jobs = jobspy_jobs + jobhive_jobs
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.bulk_insert.return_value = BulkInsertResult(
            inserted_count=5, duplicates_skipped=0, new_jobs=all_jobs
        )
        mock_repo.get_watchlist.return_value = []

        mock_notifier = MagicMock()
        mock_notifier_cls.return_value = mock_notifier

        # Execute
        _run_workflow()

        # Verify: bulk_insert called with all 5 jobs (2 jobspy + 3 jobhive)
        bulk_insert_call = mock_repo.bulk_insert.call_args[0][0]
        assert len(bulk_insert_call) == 5

        # Verify: merged errors from both scrapers
        history_call = mock_repo.record_scrape_history.call_args[0][0]
        assert history_call.jobs_found == 5
        assert "minor jobspy warning" in history_call.errors
        assert "minor jobhive warning" in history_call.errors

    @patch("daily_scraper.TelegramNotifier")
    @patch("daily_scraper.JobsRepository")
    @patch("daily_scraper.Settings.load")
    @patch("daily_scraper.scrape_jobhive")
    @patch("daily_scraper.scrape_all")
    def test_scrape_history_records_combined_counts(
        self, mock_jobspy, mock_jobhive, mock_settings_load, mock_repo_cls, mock_notifier_cls
    ):
        """Scrape history entry has combined job count from both scrapers (Req 2.4)."""
        from daily_scraper import _run_workflow

        # Setup
        settings = _make_settings()
        mock_settings_load.return_value = settings

        jobspy_jobs = [_make_job(f"JS Job {i}") for i in range(3)]
        jobhive_jobs = [_make_job(f"JH Job {i}", "jobhive", "lever") for i in range(4)]
        mock_jobspy.return_value = ScrapeResult(jobs=jobspy_jobs, errors=["err1"])
        mock_jobhive.return_value = ScrapeResult(jobs=jobhive_jobs, errors=["err2", "err3"])

        all_jobs = jobspy_jobs + jobhive_jobs
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.bulk_insert.return_value = BulkInsertResult(
            inserted_count=5, duplicates_skipped=2, new_jobs=all_jobs[:5]
        )
        mock_repo.get_watchlist.return_value = []

        mock_notifier = MagicMock()
        mock_notifier_cls.return_value = mock_notifier

        # Execute
        _run_workflow()

        # Verify: scrape history has combined counts
        history_call = mock_repo.record_scrape_history.call_args[0][0]
        assert isinstance(history_call, ScrapeHistoryEntry)
        # jobs_found = total merged jobs (3 + 4 = 7)
        assert history_call.jobs_found == 7
        # duplicates_skipped comes from bulk_insert result
        assert history_call.duplicates_skipped == 2
        # errors = combined from both scrapers (3 total)
        assert len(history_call.errors) == 3
        assert "err1" in history_call.errors
        assert "err2" in history_call.errors
        assert "err3" in history_call.errors
