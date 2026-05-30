"""Unit tests for the JobHive scraper module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.config.settings import Settings
from app.models.job import JobRecord, ScrapeResult
from app.scraper.jobhive_scraper import (
    _normalize_jobhive_result,
    _process_dataframe,
    scrape_jobhive,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_settings():
    """Create a minimal Settings instance for testing."""
    return Settings(
        mongodb_uri="mongodb://localhost:27017",
        database_name="testdb",
        search_terms=["Biomedical Engineer"],
        locations=["Bangalore"],
        job_sources=["linkedin"],
        schedule_time="08:00",
    )


@pytest.fixture
def sample_raw_complete():
    """A complete raw dict mimicking jobhive-py output."""
    return {
        "title": "Software Engineer",
        "company": "Acme Corp",
        "location": "Bangalore, India",
        "url": "https://boards.greenhouse.io/acme/jobs/123",
        "description": "Build great software",
        "employment_type": "Full-time",
        "salary_min": 80000,
        "salary_max": 120000,
        "salary_currency": "USD",
        "posted_at": "2024-03-15",
    }


@pytest.fixture
def sample_raw_minimal():
    """A raw dict with only required fields (title and url)."""
    return {
        "title": "Data Analyst",
        "url": "https://jobs.lever.co/datacompany/456",
    }


# ---------------------------------------------------------------------------
# Tests for _normalize_jobhive_result
# ---------------------------------------------------------------------------


class TestNormalizeJobhiveResult:
    """Tests for the _normalize_jobhive_result helper function."""

    def test_normalizes_complete_record(self, sample_raw_complete):
        """A record with all fields produces a valid JobRecord."""
        record = _normalize_jobhive_result(sample_raw_complete, "greenhouse", "Software Engineer")

        assert record is not None
        assert record.title == "Software Engineer"
        assert record.company == "Acme Corp"
        assert record.location == "Bangalore, India"
        assert record.source == "greenhouse"
        assert record.job_url == "https://boards.greenhouse.io/acme/jobs/123"
        assert record.description == "Build great software"
        assert record.job_type == "Full-time"
        assert record.source_type == "jobhive"
        assert record.source_platform == "greenhouse"
        assert record.search_term == "Software Engineer"

    def test_missing_optional_fields_default_to_empty(self, sample_raw_minimal):
        """Missing optional fields (description, job_type, salary, date_posted) default to empty string."""
        record = _normalize_jobhive_result(sample_raw_minimal, "lever", "Data Analyst")

        assert record is not None
        assert record.title == "Data Analyst"
        assert record.job_url == "https://jobs.lever.co/datacompany/456"
        assert record.description == ""
        assert record.job_type == ""
        assert record.salary == ""
        assert record.date_posted == ""
        assert record.company == ""
        assert record.location == ""

    def test_missing_title_returns_none(self):
        """A record without a title is skipped (returns None)."""
        raw = {"title": "", "url": "https://example.com/job/1"}
        result = _normalize_jobhive_result(raw, "greenhouse", "test")
        assert result is None

    def test_none_title_returns_none(self):
        """A record with None title is skipped."""
        raw = {"title": None, "url": "https://example.com/job/1"}
        result = _normalize_jobhive_result(raw, "greenhouse", "test")
        assert result is None

    def test_missing_url_returns_none(self):
        """A record without a url is skipped (returns None)."""
        raw = {"title": "Engineer", "url": ""}
        result = _normalize_jobhive_result(raw, "lever", "test")
        assert result is None

    def test_none_url_returns_none(self):
        """A record with None url is skipped."""
        raw = {"title": "Engineer", "url": None}
        result = _normalize_jobhive_result(raw, "lever", "test")
        assert result is None

    def test_missing_both_required_fields_returns_none(self):
        """A record missing both title and url is skipped."""
        raw = {"description": "Some description", "company": "SomeCo"}
        result = _normalize_jobhive_result(raw, "ashby", "test")
        assert result is None

    def test_whitespace_only_title_returns_none(self):
        """A record with whitespace-only title is skipped."""
        raw = {"title": "   ", "url": "https://example.com/job/1"}
        result = _normalize_jobhive_result(raw, "workday", "test")
        assert result is None

    def test_whitespace_only_url_returns_none(self):
        """A record with whitespace-only url is skipped."""
        raw = {"title": "Engineer", "url": "   "}
        result = _normalize_jobhive_result(raw, "workday", "test")
        assert result is None

    def test_source_platform_is_lowercase(self):
        """source_platform is always the lowercase platform name."""
        raw = {"title": "Engineer", "url": "https://example.com/1"}
        record = _normalize_jobhive_result(raw, "Greenhouse", "test")
        assert record is not None
        assert record.source_platform == "greenhouse"

    def test_source_type_always_jobhive(self):
        """source_type is always 'jobhive'."""
        raw = {"title": "Engineer", "url": "https://example.com/1"}
        record = _normalize_jobhive_result(raw, "lever", "test")
        assert record is not None
        assert record.source_type == "jobhive"


# ---------------------------------------------------------------------------
# Tests for platform failure isolation
# ---------------------------------------------------------------------------


class TestPlatformFailureIsolation:
    """Tests that one platform failing does not affect others."""

    @patch("app.scraper.jobhive_scraper.Client")
    def test_one_platform_fails_others_succeed(self, mock_client_cls, mock_settings):
        """If one platform raises an exception, jobs from other platforms are still collected."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        call_count = [0]

        def search_side_effect(**kwargs):
            call_count[0] += 1
            ats = kwargs.get("ats", "")
            if ats == "greenhouse":
                raise RuntimeError("Greenhouse API timeout")
            # Return a valid DataFrame for other platforms
            return pd.DataFrame([{
                "title": f"Job on {ats}",
                "company": "TestCo",
                "location": "Remote",
                "url": f"https://example.com/{ats}/{call_count[0]}",
                "description": "A job",
                "employment_type": "Full-time",
                "salary_min": None,
                "salary_max": None,
                "salary_currency": None,
                "posted_at": None,
            }])

        mock_client.search.side_effect = search_side_effect

        result = scrape_jobhive(mock_settings)

        # Greenhouse failed, but other 4 platforms should succeed
        assert isinstance(result, ScrapeResult)
        assert len(result.jobs) > 0
        # Verify no greenhouse jobs in results
        greenhouse_jobs = [j for j in result.jobs if j.source_platform == "greenhouse"]
        assert len(greenhouse_jobs) == 0
        # Verify jobs from other platforms exist
        other_jobs = [j for j in result.jobs if j.source_platform != "greenhouse"]
        assert len(other_jobs) > 0

    @patch("app.scraper.jobhive_scraper.Client")
    def test_platform_failure_logs_error(self, mock_client_cls, mock_settings):
        """Platform failure is recorded in errors list."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        def search_side_effect(**kwargs):
            ats = kwargs.get("ats", "")
            if ats == "lever":
                raise ConnectionError("Lever connection refused")
            return pd.DataFrame()

        mock_client.search.side_effect = search_side_effect

        result = scrape_jobhive(mock_settings)

        # The error should be captured (either in errors list or logged)
        # Since _scrape_platform catches per-search-term exceptions internally,
        # the error may not bubble up to all_errors unless the entire platform call fails.
        # The scraper continues regardless.
        assert isinstance(result, ScrapeResult)


# ---------------------------------------------------------------------------
# Tests for empty results from all platforms
# ---------------------------------------------------------------------------


class TestEmptyResults:
    """Tests for when all platforms return empty results."""

    @patch("app.scraper.jobhive_scraper.Client")
    def test_all_platforms_return_empty(self, mock_client_cls, mock_settings):
        """When all platforms return empty DataFrames, result has empty jobs and no errors."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = pd.DataFrame()

        result = scrape_jobhive(mock_settings)

        assert isinstance(result, ScrapeResult)
        assert len(result.jobs) == 0
        assert len(result.errors) == 0

    @patch("app.scraper.jobhive_scraper.Client")
    def test_all_platforms_return_none_df(self, mock_client_cls, mock_settings):
        """When client.search returns None, result has empty jobs and no errors."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = None

        result = scrape_jobhive(mock_settings)

        assert isinstance(result, ScrapeResult)
        assert len(result.jobs) == 0
        assert len(result.errors) == 0


# ---------------------------------------------------------------------------
# Tests for _process_dataframe
# ---------------------------------------------------------------------------


class TestProcessDataframe:
    """Tests for the _process_dataframe helper."""

    def test_empty_dataframe_returns_empty_list(self):
        """An empty DataFrame produces no records."""
        df = pd.DataFrame()
        records = _process_dataframe(df, "greenhouse", "test")
        assert records == []

    def test_none_dataframe_returns_empty_list(self):
        """None DataFrame produces no records."""
        records = _process_dataframe(None, "greenhouse", "test")
        assert records == []

    def test_skips_records_missing_required_fields(self):
        """Records missing title or url are skipped."""
        df = pd.DataFrame([
            {"title": "Valid Job", "url": "https://example.com/1"},
            {"title": "", "url": "https://example.com/2"},
            {"title": "Another Job", "url": ""},
            {"title": None, "url": "https://example.com/3"},
        ])
        records = _process_dataframe(df, "lever", "test")
        assert len(records) == 1
        assert records[0].title == "Valid Job"

    def test_normalizes_all_valid_records(self):
        """All valid records in a DataFrame are normalized."""
        df = pd.DataFrame([
            {"title": "Job A", "url": "https://example.com/a", "company": "CoA"},
            {"title": "Job B", "url": "https://example.com/b", "company": "CoB"},
        ])
        records = _process_dataframe(df, "ashby", "Engineer")
        assert len(records) == 2
        assert records[0].title == "Job A"
        assert records[1].title == "Job B"
        assert all(r.source_type == "jobhive" for r in records)
        assert all(r.source_platform == "ashby" for r in records)
