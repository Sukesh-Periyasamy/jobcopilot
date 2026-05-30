"""Unit tests for the preferences API router.

Tests cover:
- POST /preferences/pinned-collections pins a collection (max 5, 409 if exceeded)
- POST /preferences/pinned-companies pins a company (max 10, 409 if exceeded)
- GET /preferences/dashboard returns jobs from pinned companies, collections, and research
- DELETE /preferences/pinned-collections/{name} unpins a collection (404 if not found)
- DELETE /preferences/pinned-companies/{name} unpins a company (404 if not found)

Requirements: 12.1, 12.2, 12.3, 12.5, 12.6, 12.7
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from main import app
    return TestClient(app)


class TestPinCollection:
    """Tests for POST /preferences/pinned-collections endpoint."""

    @patch("app.api.preferences.JobsRepository")
    def test_pins_collection_successfully(self, mock_repo_cls, client):
        """POST /preferences/pinned-collections pins a collection.

        Validates: Requirements 12.1, 12.5
        """
        mock_repo = MagicMock()
        mock_repo.add_pinned_collection.return_value = True
        mock_repo_cls.return_value = mock_repo

        response = client.post(
            "/preferences/pinned-collections",
            json={"name": "Medical Technology"},
        )

        assert response.status_code == 201
        assert response.json() == {"message": "Pinned collection 'Medical Technology'"}
        mock_repo.add_pinned_collection.assert_called_once_with("Medical Technology")

    @patch("app.api.preferences.JobsRepository")
    def test_returns_409_when_limit_exceeded(self, mock_repo_cls, client):
        """POST /preferences/pinned-collections returns 409 when max 5 reached.

        Validates: Requirements 12.6
        """
        mock_repo = MagicMock()
        mock_repo.add_pinned_collection.return_value = False
        mock_repo_cls.return_value = mock_repo

        response = client.post(
            "/preferences/pinned-collections",
            json={"name": "IoT"},
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Maximum 5 pinned collections allowed"


class TestPinCompany:
    """Tests for POST /preferences/pinned-companies endpoint."""

    @patch("app.api.preferences.JobsRepository")
    def test_pins_company_successfully(self, mock_repo_cls, client):
        """POST /preferences/pinned-companies pins a company.

        Validates: Requirements 12.2, 12.5
        """
        mock_repo = MagicMock()
        mock_repo.add_pinned_company.return_value = True
        mock_repo_cls.return_value = mock_repo

        response = client.post(
            "/preferences/pinned-companies",
            json={"name": "Philips"},
        )

        assert response.status_code == 201
        assert response.json() == {"message": "Pinned company 'Philips'"}
        mock_repo.add_pinned_company.assert_called_once_with("Philips")

    @patch("app.api.preferences.JobsRepository")
    def test_returns_409_when_limit_exceeded(self, mock_repo_cls, client):
        """POST /preferences/pinned-companies returns 409 when max 10 reached.

        Validates: Requirements 12.7
        """
        mock_repo = MagicMock()
        mock_repo.add_pinned_company.return_value = False
        mock_repo_cls.return_value = mock_repo

        response = client.post(
            "/preferences/pinned-companies",
            json={"name": "NewCo"},
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Maximum 10 pinned companies allowed"


class TestGetDashboard:
    """Tests for GET /preferences/dashboard endpoint."""

    @patch("app.api.preferences.ResearchTracker")
    @patch("app.api.preferences.CollectionEngine")
    @patch("app.api.preferences.JobsRepository")
    @patch("app.api.preferences.get_database")
    def test_returns_dashboard_with_pinned_data(
        self, mock_get_db, mock_repo_cls, mock_ce_cls, mock_rt_cls, client
    ):
        """GET /preferences/dashboard returns jobs from pinned companies, collections, and research.

        Validates: Requirements 12.3
        """
        # Setup mock database
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Setup mock jobs collection with chained methods
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.__iter__ = lambda self: iter([])
        mock_db.__getitem__.return_value = mock_cursor
        mock_cursor.find.return_value = mock_cursor

        # Setup mock repository
        mock_repo = MagicMock()
        mock_repo.get_pinned_companies.return_value = []
        mock_repo.get_pinned_collections.return_value = []
        mock_repo_cls.return_value = mock_repo

        # Setup mock research tracker
        mock_rt = MagicMock()
        mock_rt.get_recent_research.return_value = []
        mock_rt_cls.return_value = mock_rt

        response = client.get("/preferences/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert "pinned_company_jobs" in data
        assert "pinned_collection_jobs" in data
        assert "new_research_opportunities" in data
        assert data["pinned_company_jobs"] == []
        assert data["pinned_collection_jobs"] == []
        assert data["new_research_opportunities"] == []

    @patch("app.api.preferences.ResearchTracker")
    @patch("app.api.preferences.CollectionEngine")
    @patch("app.api.preferences.JobsRepository")
    @patch("app.api.preferences.get_database")
    def test_returns_pinned_company_jobs(
        self, mock_get_db, mock_repo_cls, mock_ce_cls, mock_rt_cls, client
    ):
        """GET /preferences/dashboard returns jobs from pinned companies.

        Validates: Requirements 12.3
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock jobs collection
        mock_jobs_col = MagicMock()
        mock_db.__getitem__.return_value = mock_jobs_col

        job_doc = {
            "title": "Software Engineer",
            "company": "Philips",
            "location": "Bangalore",
            "source": "LinkedIn",
            "source_type": "jobspy",
            "source_platform": "linkedin",
            "job_url": "https://example.com/job1",
            "description": "A great job",
            "job_type": "Full-time",
            "salary": "",
            "date_posted": "2025-01-10",
            "search_term": "engineer",
            "created_at": "2025-01-10T00:00:00Z",
            "updated_at": "2025-01-10T00:00:00Z",
        }

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.__iter__ = lambda self: iter([job_doc])
        mock_jobs_col.find.return_value = mock_cursor

        # Setup mock repository
        mock_repo = MagicMock()
        mock_repo.get_pinned_companies.return_value = ["Philips"]
        mock_repo.get_pinned_collections.return_value = []
        mock_repo_cls.return_value = mock_repo

        # Setup mock research tracker
        mock_rt = MagicMock()
        mock_rt.get_recent_research.return_value = []
        mock_rt_cls.return_value = mock_rt

        response = client.get("/preferences/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert len(data["pinned_company_jobs"]) == 1
        assert data["pinned_company_jobs"][0]["company"] == "Philips"


class TestUnpinCollection:
    """Tests for DELETE /preferences/pinned-collections/{name} endpoint."""

    @patch("app.api.preferences.JobsRepository")
    def test_unpins_collection_successfully(self, mock_repo_cls, client):
        """DELETE /preferences/pinned-collections/{name} unpins a collection.

        Validates: Requirements 12.1
        """
        mock_repo = MagicMock()
        mock_repo.remove_pinned_collection.return_value = True
        mock_repo_cls.return_value = mock_repo

        response = client.delete("/preferences/pinned-collections/Medical Technology")

        assert response.status_code == 200
        assert response.json() == {"message": "Unpinned collection 'Medical Technology'"}
        mock_repo.remove_pinned_collection.assert_called_once_with("Medical Technology")

    @patch("app.api.preferences.JobsRepository")
    def test_returns_404_when_not_found(self, mock_repo_cls, client):
        """DELETE /preferences/pinned-collections/{name} returns 404 if not pinned.

        Validates: Requirements 12.1
        """
        mock_repo = MagicMock()
        mock_repo.remove_pinned_collection.return_value = False
        mock_repo_cls.return_value = mock_repo

        response = client.delete("/preferences/pinned-collections/NonExistent")

        assert response.status_code == 404
        assert response.json()["detail"] == "Collection not found in pinned list"


class TestUnpinCompany:
    """Tests for DELETE /preferences/pinned-companies/{name} endpoint."""

    @patch("app.api.preferences.JobsRepository")
    def test_unpins_company_successfully(self, mock_repo_cls, client):
        """DELETE /preferences/pinned-companies/{name} unpins a company.

        Validates: Requirements 12.2
        """
        mock_repo = MagicMock()
        mock_repo.remove_pinned_company.return_value = True
        mock_repo_cls.return_value = mock_repo

        response = client.delete("/preferences/pinned-companies/Philips")

        assert response.status_code == 200
        assert response.json() == {"message": "Unpinned company 'Philips'"}
        mock_repo.remove_pinned_company.assert_called_once_with("Philips")

    @patch("app.api.preferences.JobsRepository")
    def test_returns_404_when_not_found(self, mock_repo_cls, client):
        """DELETE /preferences/pinned-companies/{name} returns 404 if not pinned.

        Validates: Requirements 12.2
        """
        mock_repo = MagicMock()
        mock_repo.remove_pinned_company.return_value = False
        mock_repo_cls.return_value = mock_repo

        response = client.delete("/preferences/pinned-companies/NonExistent")

        assert response.status_code == 404
        assert response.json()["detail"] == "Company not found in pinned list"
