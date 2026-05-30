"""Unit tests for the export API router.

Tests cover:
- CSV endpoint returns correct Content-Type and Content-Disposition headers
- XLSX endpoint returns correct Content-Type and Content-Disposition headers
- X-Export-Truncated header is set when results are truncated
- Filter parameters are passed through correctly
- Error handling returns 500

Requirements: 5.1, 5.2, 5.3, 5.6, 5.7
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.job import FilterCriteria, JobRecord


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from main import app
    return TestClient(app)


def _make_job(index: int) -> JobRecord:
    """Create a sample JobRecord with deterministic values."""
    return JobRecord(
        title=f"Engineer {index}",
        company=f"Company {index}",
        location=f"City {index}",
        source="linkedin",
        job_url=f"https://example.com/job/{index}",
        description=f"Description {index}",
        job_type="Full-time",
        salary=f"${index * 1000}",
        date_posted=f"2024-01-{(index % 28) + 1:02d}",
        search_term="engineer",
        source_type="jobspy",
        source_platform="linkedin",
        created_at="2024-01-15T08:00:00+00:00",
    )


class TestExportCSVEndpoint:
    """Tests for GET /export/csv endpoint."""

    @patch("app.api.export.JobsRepository")
    @patch("app.api.export.export_csv")
    def test_csv_returns_correct_content_type(self, mock_export_csv, mock_repo_cls, client):
        mock_repo = MagicMock()
        mock_repo.get_export_jobs.return_value = [_make_job(0)]
        mock_repo_cls.return_value = mock_repo
        mock_export_csv.return_value = (BytesIO(b"title,company\n"), False)

        response = client.get("/export/csv")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")

    @patch("app.api.export.JobsRepository")
    @patch("app.api.export.export_csv")
    def test_csv_returns_correct_content_disposition(self, mock_export_csv, mock_repo_cls, client):
        mock_repo = MagicMock()
        mock_repo.get_export_jobs.return_value = []
        mock_repo_cls.return_value = mock_repo
        mock_export_csv.return_value = (BytesIO(b"title,company\n"), False)

        response = client.get("/export/csv")

        today = date.today().isoformat()
        expected_filename = f"jobs_export_{today}.csv"
        assert expected_filename in response.headers["content-disposition"]
        assert "attachment" in response.headers["content-disposition"]

    @patch("app.api.export.JobsRepository")
    @patch("app.api.export.export_csv")
    def test_csv_truncated_header_when_truncated(self, mock_export_csv, mock_repo_cls, client):
        mock_repo = MagicMock()
        mock_repo.get_export_jobs.return_value = []
        mock_repo_cls.return_value = mock_repo
        mock_export_csv.return_value = (BytesIO(b"title,company\n"), True)

        response = client.get("/export/csv")

        assert response.headers["x-export-truncated"] == "true"

    @patch("app.api.export.JobsRepository")
    @patch("app.api.export.export_csv")
    def test_csv_no_truncated_header_when_not_truncated(self, mock_export_csv, mock_repo_cls, client):
        mock_repo = MagicMock()
        mock_repo.get_export_jobs.return_value = []
        mock_repo_cls.return_value = mock_repo
        mock_export_csv.return_value = (BytesIO(b"title,company\n"), False)

        response = client.get("/export/csv")

        assert "x-export-truncated" not in response.headers

    @patch("app.api.export.JobsRepository")
    @patch("app.api.export.export_csv")
    def test_csv_passes_filter_params(self, mock_export_csv, mock_repo_cls, client):
        mock_repo = MagicMock()
        mock_repo.get_export_jobs.return_value = []
        mock_repo_cls.return_value = mock_repo
        mock_export_csv.return_value = (BytesIO(b"title,company\n"), False)

        client.get("/export/csv?source_type=jobhive&source_platform=workday&location=Bangalore")

        filters = mock_repo.get_export_jobs.call_args[0][0]
        assert filters.source_type == "jobhive"
        assert filters.source_platform == "workday"
        assert filters.location == "Bangalore"

    @patch("app.api.export.JobsRepository")
    def test_csv_returns_500_on_error(self, mock_repo_cls, client):
        mock_repo_cls.side_effect = Exception("DB connection failed")

        response = client.get("/export/csv")

        assert response.status_code == 500


class TestExportXLSXEndpoint:
    """Tests for GET /export/xlsx endpoint."""

    @patch("app.api.export.JobsRepository")
    @patch("app.api.export.export_xlsx")
    def test_xlsx_returns_correct_content_type(self, mock_export_xlsx, mock_repo_cls, client):
        mock_repo = MagicMock()
        mock_repo.get_export_jobs.return_value = [_make_job(0)]
        mock_repo_cls.return_value = mock_repo
        mock_export_xlsx.return_value = (BytesIO(b"fake xlsx"), False)

        response = client.get("/export/xlsx")

        assert response.status_code == 200
        expected_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert response.headers["content-type"].startswith(expected_type)

    @patch("app.api.export.JobsRepository")
    @patch("app.api.export.export_xlsx")
    def test_xlsx_returns_correct_content_disposition(self, mock_export_xlsx, mock_repo_cls, client):
        mock_repo = MagicMock()
        mock_repo.get_export_jobs.return_value = []
        mock_repo_cls.return_value = mock_repo
        mock_export_xlsx.return_value = (BytesIO(b"fake xlsx"), False)

        response = client.get("/export/xlsx")

        today = date.today().isoformat()
        expected_filename = f"jobs_export_{today}.xlsx"
        assert expected_filename in response.headers["content-disposition"]
        assert "attachment" in response.headers["content-disposition"]

    @patch("app.api.export.JobsRepository")
    @patch("app.api.export.export_xlsx")
    def test_xlsx_truncated_header_when_truncated(self, mock_export_xlsx, mock_repo_cls, client):
        mock_repo = MagicMock()
        mock_repo.get_export_jobs.return_value = []
        mock_repo_cls.return_value = mock_repo
        mock_export_xlsx.return_value = (BytesIO(b"fake xlsx"), True)

        response = client.get("/export/xlsx")

        assert response.headers["x-export-truncated"] == "true"

    @patch("app.api.export.JobsRepository")
    @patch("app.api.export.export_xlsx")
    def test_xlsx_no_truncated_header_when_not_truncated(self, mock_export_xlsx, mock_repo_cls, client):
        mock_repo = MagicMock()
        mock_repo.get_export_jobs.return_value = []
        mock_repo_cls.return_value = mock_repo
        mock_export_xlsx.return_value = (BytesIO(b"fake xlsx"), False)

        response = client.get("/export/xlsx")

        assert "x-export-truncated" not in response.headers

    @patch("app.api.export.JobsRepository")
    @patch("app.api.export.export_xlsx")
    def test_xlsx_passes_all_filter_params(self, mock_export_xlsx, mock_repo_cls, client):
        mock_repo = MagicMock()
        mock_repo.get_export_jobs.return_value = []
        mock_repo_cls.return_value = mock_repo
        mock_export_xlsx.return_value = (BytesIO(b"fake xlsx"), False)

        client.get(
            "/export/xlsx?source=indeed&location=Mumbai&company=Philips"
            "&keyword=engineer&job_type=Full-time&date_from=2024-01-01"
            "&date_to=2024-01-31&search_term=biomedical"
            "&source_type=jobspy&source_platform=indeed"
        )

        filters = mock_repo.get_export_jobs.call_args[0][0]
        assert filters.source == "indeed"
        assert filters.location == "Mumbai"
        assert filters.company == "Philips"
        assert filters.keyword == "engineer"
        assert filters.job_type == "Full-time"
        assert filters.date_from == "2024-01-01"
        assert filters.date_to == "2024-01-31"
        assert filters.search_term == "biomedical"
        assert filters.source_type == "jobspy"
        assert filters.source_platform == "indeed"

    @patch("app.api.export.JobsRepository")
    def test_xlsx_returns_500_on_error(self, mock_repo_cls, client):
        mock_repo_cls.side_effect = Exception("DB connection failed")

        response = client.get("/export/xlsx")

        assert response.status_code == 500
