"""Unit tests for the scraper module."""

import sys
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

# Mock the jobspy module before importing scraper to avoid dependency issues
mock_jobspy = MagicMock()
sys.modules.setdefault("jobspy", mock_jobspy)

from scraper.scrape_jobs import scrape_all_jobs


@patch("scraper.scrape_jobs.scrape_jobs")
def test_scrape_all_jobs_returns_combined_results(mock_scrape):
    """Test that results from multiple search terms are concatenated."""
    df1 = pd.DataFrame({"title": ["Job A"], "company": ["Co A"]})
    df2 = pd.DataFrame({"title": ["Job B"], "company": ["Co B"]})
    mock_scrape.side_effect = [df1, df2]

    result = scrape_all_jobs(
        search_terms=["term1", "term2"],
        sites=["linkedin"],
        country="india",
        results_wanted=15,
    )

    assert len(result) == 2
    assert list(result["title"]) == ["Job A", "Job B"]


@patch("scraper.scrape_jobs.scrape_jobs")
def test_scrape_all_jobs_returns_empty_df_when_no_results(mock_scrape):
    """Test that an empty DataFrame is returned when all searches yield nothing."""
    mock_scrape.return_value = pd.DataFrame()

    result = scrape_all_jobs(
        search_terms=["term1"],
        sites=["linkedin"],
        country="india",
        results_wanted=15,
    )

    assert result.empty


@patch("scraper.scrape_jobs.scrape_jobs")
def test_scrape_all_jobs_handles_partial_failures(mock_scrape):
    """Test that partial failures don't halt the pipeline."""
    df1 = pd.DataFrame({"title": ["Job A"], "company": ["Co A"]})
    mock_scrape.side_effect = [Exception("Board failed"), df1]

    result = scrape_all_jobs(
        search_terms=["failing_term", "working_term"],
        sites=["linkedin"],
        country="india",
        results_wanted=15,
    )

    assert len(result) == 1
    assert result["title"].iloc[0] == "Job A"


@patch("scraper.scrape_jobs.scrape_jobs")
def test_scrape_all_jobs_returns_empty_df_when_all_fail(mock_scrape):
    """Test that an empty DataFrame is returned when all searches fail."""
    mock_scrape.side_effect = Exception("All boards failed")

    result = scrape_all_jobs(
        search_terms=["term1", "term2"],
        sites=["linkedin"],
        country="india",
        results_wanted=15,
    )

    assert result.empty


@patch("scraper.scrape_jobs.scrape_jobs")
def test_scrape_all_jobs_passes_correct_params(mock_scrape):
    """Test that jobspy.scrape_jobs is called with correct parameters."""
    mock_scrape.return_value = pd.DataFrame()

    scrape_all_jobs(
        search_terms=["Biomedical Engineer"],
        sites=["linkedin", "indeed", "naukri"],
        country="india",
        results_wanted=15,
    )

    mock_scrape.assert_called_once_with(
        site_name=["linkedin", "indeed", "naukri"],
        search_term="Biomedical Engineer",
        country_indeed="india",
        results_wanted=15,
    )


@patch("scraper.scrape_jobs.scrape_jobs")
def test_scrape_all_jobs_skips_none_results(mock_scrape):
    """Test that None return values are handled gracefully."""
    mock_scrape.return_value = None

    result = scrape_all_jobs(
        search_terms=["term1"],
        sites=["linkedin"],
        country="india",
        results_wanted=15,
    )

    assert result.empty
