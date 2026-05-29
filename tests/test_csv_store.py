"""Unit tests for the CSV storage utility (save_jobs_to_csv)."""

import datetime
import os
import sys
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Mock the jobspy module before importing scraper to avoid dependency issues
mock_jobspy = MagicMock()
sys.modules.setdefault("jobspy", mock_jobspy)

from scraper.scrape_jobs import save_jobs_to_csv, REQUIRED_CSV_COLUMNS


class TestSaveJobsToCsv:
    """Tests for save_jobs_to_csv function."""

    def test_creates_output_directory(self, tmp_path):
        """Test that the output directory is created if it doesn't exist."""
        output_dir = str(tmp_path / "new_dir")
        df = pd.DataFrame({"job_url": ["http://example.com/1"], "title": ["Job A"]})

        save_jobs_to_csv(df, output_dir=output_dir)

        assert os.path.isdir(output_dir)

    def test_returns_correct_file_path(self, tmp_path):
        """Test that the returned path matches the expected format."""
        output_dir = str(tmp_path)
        df = pd.DataFrame({"job_url": ["http://example.com/1"], "title": ["Job A"]})

        result = save_jobs_to_csv(df, output_dir=output_dir)

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        expected = os.path.join(output_dir, f"jobs_{today_str}.csv")
        assert result == expected

    def test_deduplicates_by_job_url(self, tmp_path):
        """Test that duplicate job_urls are removed, keeping first occurrence."""
        output_dir = str(tmp_path)
        df = pd.DataFrame({
            "job_url": ["http://example.com/1", "http://example.com/1", "http://example.com/2"],
            "title": ["First", "Duplicate", "Second"],
        })

        file_path = save_jobs_to_csv(df, output_dir=output_dir)
        result = pd.read_csv(file_path)

        assert len(result) == 2
        assert result["title"].iloc[0] == "First"
        assert result["title"].iloc[1] == "Second"

    def test_fills_nan_with_empty_strings(self, tmp_path):
        """Test that NaN/None values are filled with empty strings for required columns."""
        output_dir = str(tmp_path)
        df = pd.DataFrame({
            "job_url": ["http://example.com/1"],
            "title": [None],
            "company": [None],
            "site": ["linkedin"],
        })

        file_path = save_jobs_to_csv(df, output_dir=output_dir)
        result = pd.read_csv(file_path)

        # NaN values should be empty strings (read back as NaN by pandas, but written as "")
        # Re-read with keep_default_na=False to see actual empty strings
        result = pd.read_csv(file_path, keep_default_na=False)
        assert result["title"].iloc[0] == ""
        assert result["company"].iloc[0] == ""

    def test_includes_all_required_columns(self, tmp_path):
        """Test that all required columns are present in the output CSV."""
        output_dir = str(tmp_path)
        # DataFrame with only a subset of required columns
        df = pd.DataFrame({
            "job_url": ["http://example.com/1"],
            "title": ["Job A"],
        })

        file_path = save_jobs_to_csv(df, output_dir=output_dir)
        result = pd.read_csv(file_path)

        for col in REQUIRED_CSV_COLUMNS:
            assert col in result.columns

    def test_overwrites_existing_file(self, tmp_path):
        """Test that an existing CSV for today is overwritten."""
        output_dir = str(tmp_path)
        df1 = pd.DataFrame({"job_url": ["http://example.com/1"], "title": ["Old Job"]})
        df2 = pd.DataFrame({"job_url": ["http://example.com/2"], "title": ["New Job"]})

        save_jobs_to_csv(df1, output_dir=output_dir)
        file_path = save_jobs_to_csv(df2, output_dir=output_dir)

        result = pd.read_csv(file_path)
        assert len(result) == 1
        assert result["title"].iloc[0] == "New Job"

    def test_utf8_encoding(self, tmp_path):
        """Test that the CSV is written with UTF-8 encoding."""
        output_dir = str(tmp_path)
        df = pd.DataFrame({
            "job_url": ["http://example.com/1"],
            "title": ["Développeur Python"],  # French characters
            "company": ["Ünternehmen"],  # German characters
        })

        file_path = save_jobs_to_csv(df, output_dir=output_dir)

        # Read back with explicit UTF-8 encoding
        result = pd.read_csv(file_path, encoding="utf-8")
        assert result["title"].iloc[0] == "Développeur Python"
        assert result["company"].iloc[0] == "Ünternehmen"

    def test_raises_ioerror_on_write_failure(self, tmp_path):
        """Test that IOError is raised when file cannot be written."""
        # Use a path that cannot be written to
        output_dir = str(tmp_path / "output")
        os.makedirs(output_dir)
        df = pd.DataFrame({"job_url": ["http://example.com/1"], "title": ["Job A"]})

        with patch("pandas.DataFrame.to_csv", side_effect=OSError("Permission denied")):
            with pytest.raises(IOError, match="Failed to write CSV file"):
                save_jobs_to_csv(df, output_dir=output_dir)

    def test_empty_dataframe(self, tmp_path):
        """Test that an empty DataFrame produces a valid CSV with headers."""
        output_dir = str(tmp_path)
        df = pd.DataFrame()

        file_path = save_jobs_to_csv(df, output_dir=output_dir)
        result = pd.read_csv(file_path)

        assert len(result) == 0
        for col in REQUIRED_CSV_COLUMNS:
            assert col in result.columns

    def test_preserves_non_required_columns(self, tmp_path):
        """Test that columns beyond the required ones are preserved."""
        output_dir = str(tmp_path)
        df = pd.DataFrame({
            "job_url": ["http://example.com/1"],
            "title": ["Job A"],
            "extra_column": ["extra_value"],
        })

        file_path = save_jobs_to_csv(df, output_dir=output_dir)
        result = pd.read_csv(file_path)

        assert "extra_column" in result.columns
        assert result["extra_column"].iloc[0] == "extra_value"
