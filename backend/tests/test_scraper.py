"""Unit tests for the scraper service."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from hypothesis import given, settings as hyp_settings
from hypothesis import strategies as st

from app.config.settings import Settings
from app.models.job import JobRecord, ScrapeResult
from app.scraper.scraper import _normalize_row, _scrape_combination, scrape_all


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_settings():
    """Create a minimal Settings instance for testing."""
    return Settings(
        mongodb_uri="mongodb://localhost:27017",
        database_name="testdb",
        search_terms=["Python Developer", "Backend Engineer"],
        locations=["Bangalore", "Remote"],
        job_sources=["linkedin", "indeed"],
        schedule_time="08:00",
    )


@pytest.fixture
def sample_df():
    """Create a sample DataFrame mimicking JobSpy output."""
    return pd.DataFrame(
        [
            {
                "title": "Software Engineer",
                "company": "Acme Corp",
                "location": "Bangalore, India",
                "site": "linkedin",
                "job_url": "https://linkedin.com/jobs/123",
                "description": "Build great software",
                "job_type": "full-time",
                "min_amount": 1000000,
                "max_amount": 2000000,
                "currency": "INR",
                "interval": "yearly",
                "date_posted": "2024-01-15",
            },
            {
                "title": "Data Analyst",
                "company": "DataCo",
                "location": "Remote",
                "site": "indeed",
                "job_url": "https://indeed.com/jobs/456",
                "description": "Analyze data",
                "job_type": "internship",
                "min_amount": None,
                "max_amount": None,
                "currency": None,
                "interval": None,
                "date_posted": None,
            },
        ]
    )


# ---------------------------------------------------------------------------
# Tests for _normalize_row
# ---------------------------------------------------------------------------


class TestNormalizeRow:
    """Tests for the _normalize_row helper function."""

    def test_normalizes_complete_row(self, sample_df):
        """A row with all fields produces a valid JobRecord."""
        row = sample_df.iloc[0]
        record = _normalize_row(row, "Python Developer")

        assert record is not None
        assert record.title == "Software Engineer"
        assert record.company == "Acme Corp"
        assert record.location == "Bangalore, India"
        assert record.source == "linkedin"
        assert record.job_url == "https://linkedin.com/jobs/123"
        assert record.description == "Build great software"
        assert record.job_type == "full-time"
        assert "INR" in record.salary
        assert "1000000" in record.salary
        assert "2000000" in record.salary
        assert record.date_posted == "2024-01-15"
        assert record.search_term == "Python Developer"
        assert record.source_type == "jobspy"
        assert record.source_platform == "linkedin"
        assert record.created_at != ""
        assert record.updated_at != ""

    def test_source_metadata_fields(self, sample_df):
        """source_type is 'jobspy' and source_platform is lowercase site value."""
        # Row with site="linkedin"
        row0 = sample_df.iloc[0]
        record0 = _normalize_row(row0, "test")
        assert record0 is not None
        assert record0.source_type == "jobspy"
        assert record0.source_platform == "linkedin"

        # Row with site="indeed"
        row1 = sample_df.iloc[1]
        record1 = _normalize_row(row1, "test")
        assert record1 is not None
        assert record1.source_type == "jobspy"
        assert record1.source_platform == "indeed"

    def test_source_platform_lowercased(self):
        """source_platform is always lowercased from the site field."""
        row = pd.Series({
            "title": "Engineer",
            "job_url": "https://example.com/1",
            "site": "LinkedIn",
        })
        record = _normalize_row(row, "test")
        assert record is not None
        assert record.source_type == "jobspy"
        assert record.source_platform == "linkedin"

    def test_source_platform_empty_when_site_missing(self):
        """source_platform defaults to empty string when site is missing."""
        row = pd.Series({
            "title": "Engineer",
            "job_url": "https://example.com/1",
        })
        record = _normalize_row(row, "test")
        assert record is not None
        assert record.source_type == "jobspy"
        assert record.source_platform == ""

    def test_missing_optional_fields_default_to_empty(self, sample_df):
        """Missing optional fields are set to empty string."""
        row = sample_df.iloc[1]
        record = _normalize_row(row, "Data Analyst")

        assert record is not None
        assert record.salary == ""
        assert record.date_posted == ""

    def test_missing_title_returns_none(self):
        """A row without a title is skipped."""
        row = pd.Series({"title": "", "job_url": "https://example.com/1"})
        assert _normalize_row(row, "test") is None

    def test_missing_job_url_returns_none(self):
        """A row without a job_url is skipped."""
        row = pd.Series({"title": "Engineer", "job_url": ""})
        assert _normalize_row(row, "test") is None

    def test_none_title_returns_none(self):
        """A row with None title is skipped."""
        row = pd.Series({"title": None, "job_url": "https://example.com/1"})
        assert _normalize_row(row, "test") is None

    def test_whitespace_only_title_returns_none(self):
        """A row with whitespace-only title is skipped."""
        row = pd.Series({"title": "   ", "job_url": "https://example.com/1"})
        assert _normalize_row(row, "test") is None


# ---------------------------------------------------------------------------
# Tests for _scrape_combination
# ---------------------------------------------------------------------------


class TestScrapeCombination:
    """Tests for the _scrape_combination function."""

    @patch("app.scraper.scraper.scrape_jobs")
    def test_returns_jobs_on_success(self, mock_scrape, sample_df):
        """Successful scrape returns normalized jobs and no errors."""
        mock_scrape.return_value = sample_df

        jobs, errors = _scrape_combination("Python", "Bangalore", ["linkedin"])

        assert len(jobs) == 2
        assert len(errors) == 0
        assert all(isinstance(j, JobRecord) for j in jobs)

    @patch("app.scraper.scraper.scrape_jobs")
    def test_returns_empty_on_empty_df(self, mock_scrape):
        """Empty DataFrame returns no jobs and no errors."""
        mock_scrape.return_value = pd.DataFrame()

        jobs, errors = _scrape_combination("Python", "Bangalore", ["linkedin"])

        assert len(jobs) == 0
        assert len(errors) == 0

    @patch("app.scraper.scraper.scrape_jobs")
    def test_returns_error_on_exception(self, mock_scrape):
        """Exception during scraping returns an error message."""
        mock_scrape.side_effect = RuntimeError("Network timeout")

        jobs, errors = _scrape_combination("Python", "Bangalore", ["linkedin"])

        assert len(jobs) == 0
        assert len(errors) == 1
        assert "Network timeout" in errors[0]
        assert "Python" in errors[0]
        assert "Bangalore" in errors[0]

    @patch("app.scraper.scraper.scrape_jobs")
    def test_skips_invalid_records(self, mock_scrape):
        """Records missing title or job_url are skipped."""
        df = pd.DataFrame(
            [
                {"title": "Valid Job", "job_url": "https://example.com/1", "site": "linkedin"},
                {"title": "", "job_url": "https://example.com/2", "site": "linkedin"},
                {"title": "Another Job", "job_url": "", "site": "indeed"},
            ]
        )
        mock_scrape.return_value = df

        jobs, errors = _scrape_combination("Python", "Remote", ["linkedin"])

        assert len(jobs) == 1
        assert jobs[0].title == "Valid Job"


# ---------------------------------------------------------------------------
# Tests for scrape_all
# ---------------------------------------------------------------------------


class TestScrapeAll:
    """Tests for the scrape_all orchestrator function."""

    @patch("app.scraper.scraper.scrape_jobs")
    def test_iterates_all_combinations(self, mock_scrape, mock_settings):
        """scrape_all calls JobSpy for each search_term × location."""
        mock_scrape.return_value = pd.DataFrame()

        result = scrape_all(mock_settings)

        # 2 search terms × 2 locations = 4 calls
        assert mock_scrape.call_count == 4
        assert isinstance(result, ScrapeResult)

    @patch("app.scraper.scraper.scrape_jobs")
    def test_collects_jobs_from_all_combinations(self, mock_scrape, mock_settings):
        """Jobs from all combinations are collected into a single result."""
        df = pd.DataFrame(
            [
                {
                    "title": "Job A",
                    "company": "Co",
                    "location": "BLR",
                    "site": "linkedin",
                    "job_url": "https://example.com/a",
                    "description": "",
                    "job_type": "",
                    "min_amount": None,
                    "max_amount": None,
                    "currency": None,
                    "interval": None,
                    "date_posted": None,
                }
            ]
        )
        mock_scrape.return_value = df

        result = scrape_all(mock_settings)

        # 4 combinations × 1 job each = 4 jobs
        assert len(result.jobs) == 4
        assert len(result.errors) == 0

    @patch("app.scraper.scraper.scrape_jobs")
    def test_collects_errors_from_failed_combinations(self, mock_scrape, mock_settings):
        """Errors from failed combinations are collected without losing other results."""
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise RuntimeError("Source failed")
            return pd.DataFrame(
                [
                    {
                        "title": "Job",
                        "company": "Co",
                        "location": "BLR",
                        "site": "linkedin",
                        "job_url": f"https://example.com/{call_count[0]}",
                        "description": "",
                        "job_type": "",
                        "min_amount": None,
                        "max_amount": None,
                        "currency": None,
                        "interval": None,
                        "date_posted": None,
                    }
                ]
            )

        mock_scrape.side_effect = side_effect

        result = scrape_all(mock_settings)

        # 3 successful + 1 failed = 3 jobs, 1 error
        assert len(result.jobs) == 3
        assert len(result.errors) == 1
        assert "Source failed" in result.errors[0]

    @patch("app.scraper.scraper.scrape_jobs")
    def test_returns_empty_when_all_fail(self, mock_scrape, mock_settings):
        """If all combinations fail, returns empty jobs with errors."""
        mock_scrape.side_effect = RuntimeError("All sources down")

        result = scrape_all(mock_settings)

        assert len(result.jobs) == 0
        assert len(result.errors) == 4  # 2 terms × 2 locations

# ---------------------------------------------------------------------------
# Property-Based Tests
# ---------------------------------------------------------------------------

# Feature: jobcopilot-v1.1-upgrade, Property 2: JobSpy Normalization Correctness


# Strategies for generating random DataFrame rows
_SITE_VALUES = st.sampled_from(
    ["linkedin", "indeed", "naukri", "google", "LinkedIn", "Indeed", "NAUKRI", "Google"]
)

_non_empty_text = st.text(min_size=1, max_size=50).filter(lambda s: s.strip() != "")


@st.composite
def jobspy_row(draw):
    """Generate a random pd.Series mimicking a JobSpy DataFrame row."""
    title = draw(_non_empty_text)
    job_url = draw(_non_empty_text)
    site = draw(_SITE_VALUES)

    data = {
        "title": title,
        "job_url": job_url,
        "site": site,
    }

    # Optional fields
    if draw(st.booleans()):
        data["company"] = draw(st.text(max_size=30))
    if draw(st.booleans()):
        data["location"] = draw(st.text(max_size=30))
    if draw(st.booleans()):
        data["description"] = draw(st.text(max_size=100))
    if draw(st.booleans()):
        data["job_type"] = draw(st.text(max_size=20))
    if draw(st.booleans()):
        data["min_amount"] = draw(st.one_of(st.none(), st.floats(min_value=0, max_value=1e7, allow_nan=False)))
    if draw(st.booleans()):
        data["max_amount"] = draw(st.one_of(st.none(), st.floats(min_value=0, max_value=1e7, allow_nan=False)))
    if draw(st.booleans()):
        data["currency"] = draw(st.one_of(st.none(), st.sampled_from(["INR", "USD", "EUR", ""])))
    if draw(st.booleans()):
        data["interval"] = draw(st.one_of(st.none(), st.sampled_from(["yearly", "monthly", "hourly", ""])))
    if draw(st.booleans()):
        data["date_posted"] = draw(st.one_of(st.none(), st.just("2024-01-15"), st.just("")))

    return pd.Series(data)


class TestJobSpyNormalizationProperty:
    """Property-based tests for JobSpy normalization correctness.

    **Validates: Requirements 3.3**
    """

    @given(row=jobspy_row(), search_term=_non_empty_text)
    @hyp_settings(max_examples=100)
    def test_jobspy_normalization_source_metadata(self, row, search_term):
        """For any valid JobSpy row with non-empty title and job_url,
        _normalize_row produces a JobRecord with source_type='jobspy'
        and source_platform equal to the lowercase site value.

        **Validates: Requirements 3.3**
        """
        result = _normalize_row(row, search_term)

        # The row always has non-empty title and job_url by construction
        assert result is not None, "Expected a valid JobRecord for non-empty title and job_url"
        assert result.source_type == "jobspy"
        assert result.source_platform == row["site"].strip().lower()
