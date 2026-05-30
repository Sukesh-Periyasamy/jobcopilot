"""Unit tests for the collections API router.

Tests cover:
- GET /collections returns list of CollectionSummary objects
- GET /collections/{name} returns CollectionDetail or 404
- GET /collections/{name}/jobs returns paginated jobs or 404
- Default pagination parameters (page=1, page_size=50)

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.job import JobRecord, PaginatedResult


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from main import app
    return TestClient(app)


def _make_job_record(**overrides) -> JobRecord:
    """Create a JobRecord with sensible defaults."""
    defaults = {
        "title": "Software Engineer",
        "company": "TestCo",
        "location": "Remote",
        "source": "linkedin",
        "job_url": "https://example.com/job/1",
        "description": "A great job",
        "job_type": "Full-time",
        "salary": "",
        "date_posted": "2024-01-15",
        "search_term": "engineer",
        "source_type": "jobspy",
        "source_platform": "linkedin",
        "created_at": "2024-01-15T00:00:00Z",
        "updated_at": "2024-01-15T00:00:00Z",
    }
    defaults.update(overrides)
    return JobRecord(**defaults)


class TestGetCollections:
    """Tests for GET /collections endpoint."""

    @patch("app.api.collections.get_database")
    @patch("app.api.collections.CollectionEngine")
    def test_returns_list_of_collection_summaries(self, mock_engine_cls, mock_get_db, client):
        """GET /collections returns list of {name, job_count} objects.

        Validates: Requirements 2.1
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_engine = MagicMock()
        mock_engine.get_all_collections.return_value = [
            {"name": "Medical Technology", "job_count": 42},
            {"name": "IoT", "job_count": 15},
        ]
        mock_engine_cls.return_value = mock_engine

        response = client.get("/collections")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0] == {"name": "Medical Technology", "job_count": 42}
        assert data[1] == {"name": "IoT", "job_count": 15}

    @patch("app.api.collections.get_database")
    @patch("app.api.collections.CollectionEngine")
    def test_returns_empty_list_when_no_jobs(self, mock_engine_cls, mock_get_db, client):
        """GET /collections returns collections with zero counts when no jobs exist."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_engine = MagicMock()
        mock_engine.get_all_collections.return_value = [
            {"name": "Medical Technology", "job_count": 0},
        ]
        mock_engine_cls.return_value = mock_engine

        response = client.get("/collections")

        assert response.status_code == 200
        data = response.json()
        assert data[0]["job_count"] == 0


class TestGetCollection:
    """Tests for GET /collections/{name} endpoint."""

    @patch("app.api.collections.get_database")
    @patch("app.api.collections.CollectionEngine")
    def test_returns_collection_detail(self, mock_engine_cls, mock_get_db, client):
        """GET /collections/{name} returns {name, keywords, job_count}.

        Validates: Requirements 2.2
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_engine = MagicMock()
        mock_engine.get_collection.return_value = {
            "name": "IoT",
            "keywords": ["IoT", "internet of things", "connected devices", "smart devices", "edge computing"],
            "job_count": 15,
        }
        mock_engine_cls.return_value = mock_engine

        response = client.get("/collections/IoT")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "IoT"
        assert "IoT" in data["keywords"]
        assert data["job_count"] == 15

    @patch("app.api.collections.get_database")
    @patch("app.api.collections.CollectionEngine")
    def test_returns_404_for_nonexistent_collection(self, mock_engine_cls, mock_get_db, client):
        """GET /collections/{name} returns 404 when collection does not exist.

        Validates: Requirements 2.4
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_engine = MagicMock()
        mock_engine.get_collection.return_value = None
        mock_engine_cls.return_value = mock_engine

        response = client.get("/collections/NonExistent")

        assert response.status_code == 404
        assert response.json()["detail"] == "Collection 'NonExistent' not found"


class TestGetCollectionJobs:
    """Tests for GET /collections/{name}/jobs endpoint."""

    @patch("app.api.collections.get_database")
    @patch("app.api.collections.CollectionEngine")
    def test_returns_paginated_jobs(self, mock_engine_cls, mock_get_db, client):
        """GET /collections/{name}/jobs returns paginated job list.

        Validates: Requirements 2.3
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_engine = MagicMock()
        job = _make_job_record(title="IoT Engineer")
        mock_engine.get_collection_jobs.return_value = PaginatedResult(
            jobs=[job],
            total=1,
            page=1,
            page_size=50,
            total_pages=1,
        )
        mock_engine_cls.return_value = mock_engine

        response = client.get("/collections/IoT/jobs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 50
        assert data["total_pages"] == 1
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["title"] == "IoT Engineer"

    @patch("app.api.collections.get_database")
    @patch("app.api.collections.CollectionEngine")
    def test_uses_default_pagination_params(self, mock_engine_cls, mock_get_db, client):
        """GET /collections/{name}/jobs defaults to page=1, page_size=50.

        Validates: Requirements 2.5
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_engine = MagicMock()
        mock_engine.get_collection_jobs.return_value = PaginatedResult(
            jobs=[], total=0, page=1, page_size=50, total_pages=0,
        )
        mock_engine_cls.return_value = mock_engine

        client.get("/collections/IoT/jobs")

        mock_engine.get_collection_jobs.assert_called_once_with("IoT", page=1, page_size=50)

    @patch("app.api.collections.get_database")
    @patch("app.api.collections.CollectionEngine")
    def test_accepts_custom_pagination_params(self, mock_engine_cls, mock_get_db, client):
        """GET /collections/{name}/jobs accepts custom page and page_size.

        Validates: Requirements 2.5
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_engine = MagicMock()
        mock_engine.get_collection_jobs.return_value = PaginatedResult(
            jobs=[], total=0, page=2, page_size=10, total_pages=0,
        )
        mock_engine_cls.return_value = mock_engine

        client.get("/collections/IoT/jobs?page=2&page_size=10")

        mock_engine.get_collection_jobs.assert_called_once_with("IoT", page=2, page_size=10)

    @patch("app.api.collections.get_database")
    @patch("app.api.collections.CollectionEngine")
    def test_returns_404_for_nonexistent_collection(self, mock_engine_cls, mock_get_db, client):
        """GET /collections/{name}/jobs returns 404 when collection does not exist.

        Validates: Requirements 2.4
        """
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_engine = MagicMock()
        mock_engine.get_collection_jobs.return_value = None
        mock_engine_cls.return_value = mock_engine

        response = client.get("/collections/NonExistent/jobs")

        assert response.status_code == 404
        assert response.json()["detail"] == "Collection 'NonExistent' not found"

    def test_invalid_page_returns_422(self, client):
        """GET /collections/{name}/jobs with page < 1 returns 422."""
        response = client.get("/collections/IoT/jobs?page=0")
        assert response.status_code == 422

    def test_invalid_page_size_returns_422(self, client):
        """GET /collections/{name}/jobs with page_size < 1 returns 422."""
        response = client.get("/collections/IoT/jobs?page_size=0")
        assert response.status_code == 422
