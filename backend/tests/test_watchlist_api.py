"""Unit tests for the watchlist API router.

Tests cover:
- GET /watchlist returns list of {company_name, ats_platform, tier} objects
- POST /watchlist with ats_platform stores it correctly
- POST /watchlist with invalid ats_platform returns 422
- GET /watchlist returns ats_platform=null for entries without it
- GET /watchlist/ats-info returns companies grouped by platform
- GET /watchlist/ats-info excludes companies without ats_platform
- PATCH /watchlist/{company} updates tier
- PATCH /watchlist/{company} with invalid tier returns 422

Requirements: 6.1, 6.3, 6.4, 6.5, 6.6, 6.7, 9.1, 9.2, 9.3, 9.4
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


class TestGetWatchlist:
    """Tests for GET /watchlist endpoint."""

    @patch("app.api.watchlist.JobsRepository")
    def test_returns_list_of_watchlist_entries(self, mock_repo_cls, client):
        """GET /watchlist returns list of {company_name, ats_platform, tier} objects.

        Validates: Requirements 6.3, 9.3
        """
        mock_repo = MagicMock()
        mock_repo.get_watchlist.return_value = [
            {"company_name": "Philips", "ats_platform": "workday", "tier": "tier1"},
            {"company_name": "Dozee", "ats_platform": "lever", "tier": "tier3"},
        ]
        mock_repo_cls.return_value = mock_repo

        response = client.get("/watchlist")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0] == {"company_name": "Philips", "ats_platform": "workday", "tier": "tier1"}
        assert data[1] == {"company_name": "Dozee", "ats_platform": "lever", "tier": "tier3"}

    @patch("app.api.watchlist.JobsRepository")
    def test_returns_ats_platform_null_for_entries_without_it(self, mock_repo_cls, client):
        """GET /watchlist returns ats_platform=null for entries without ats_platform.

        Validates: Requirements 6.6
        """
        mock_repo = MagicMock()
        mock_repo.get_watchlist.return_value = [
            {"company_name": "Acme Corp", "ats_platform": None, "tier": "tier3"},
            {"company_name": "Philips", "ats_platform": "workday", "tier": "tier2"},
        ]
        mock_repo_cls.return_value = mock_repo

        response = client.get("/watchlist")

        assert response.status_code == 200
        data = response.json()
        assert data[0]["company_name"] == "Acme Corp"
        assert data[0]["ats_platform"] is None
        assert data[0]["tier"] == "tier3"
        assert data[1]["ats_platform"] == "workday"

    @patch("app.api.watchlist.JobsRepository")
    def test_returns_empty_list_when_no_entries(self, mock_repo_cls, client):
        """GET /watchlist returns empty list when watchlist is empty."""
        mock_repo = MagicMock()
        mock_repo.get_watchlist.return_value = []
        mock_repo_cls.return_value = mock_repo

        response = client.get("/watchlist")

        assert response.status_code == 200
        assert response.json() == []

    @patch("app.api.watchlist.JobsRepository")
    def test_tier_defaults_to_tier3(self, mock_repo_cls, client):
        """GET /watchlist returns tier=tier3 as default for entries without tier.

        Validates: Requirements 9.2
        """
        mock_repo = MagicMock()
        mock_repo.get_watchlist.return_value = [
            {"company_name": "NewCo", "ats_platform": None, "tier": "tier3"},
        ]
        mock_repo_cls.return_value = mock_repo

        response = client.get("/watchlist")

        assert response.status_code == 200
        data = response.json()
        assert data[0]["tier"] == "tier3"


class TestPostWatchlist:
    """Tests for POST /watchlist endpoint."""

    @patch("app.api.watchlist.JobsRepository")
    def test_stores_company_with_ats_platform(self, mock_repo_cls, client):
        """POST /watchlist with ats_platform stores it correctly.

        Validates: Requirements 6.1, 6.4
        """
        mock_repo = MagicMock()
        mock_repo.add_to_watchlist.return_value = True
        mock_repo_cls.return_value = mock_repo

        response = client.post(
            "/watchlist",
            json={"company_name": "TestCo", "ats_platform": "greenhouse"},
        )

        assert response.status_code == 201
        mock_repo.add_to_watchlist.assert_called_once_with(
            "TestCo", ats_platform="greenhouse"
        )

    @patch("app.api.watchlist.JobsRepository")
    def test_stores_company_without_ats_platform(self, mock_repo_cls, client):
        """POST /watchlist without ats_platform stores company with null platform.

        Validates: Requirements 6.4
        """
        mock_repo = MagicMock()
        mock_repo.add_to_watchlist.return_value = True
        mock_repo_cls.return_value = mock_repo

        response = client.post(
            "/watchlist",
            json={"company_name": "NewCorp"},
        )

        assert response.status_code == 201
        mock_repo.add_to_watchlist.assert_called_once_with(
            "NewCorp", ats_platform=None
        )

    def test_invalid_ats_platform_returns_422(self, client):
        """POST /watchlist with invalid ats_platform returns 422.

        Validates: Requirements 6.1
        """
        response = client.post(
            "/watchlist",
            json={"company_name": "TestCo", "ats_platform": "invalid_platform"},
        )

        assert response.status_code == 422

    def test_empty_company_name_returns_422(self, client):
        """POST /watchlist with empty company_name returns 422.

        Validates: Requirements 6.7
        """
        response = client.post(
            "/watchlist",
            json={"company_name": ""},
        )

        assert response.status_code == 422

    def test_company_name_too_long_returns_422(self, client):
        """POST /watchlist with company_name > 100 chars returns 422.

        Validates: Requirements 6.7
        """
        response = client.post(
            "/watchlist",
            json={"company_name": "A" * 101},
        )

        assert response.status_code == 422

    @patch("app.api.watchlist.JobsRepository")
    def test_all_valid_ats_platforms_accepted(self, mock_repo_cls, client):
        """POST /watchlist accepts all valid ats_platform values.

        Validates: Requirements 6.1
        """
        mock_repo = MagicMock()
        mock_repo.add_to_watchlist.return_value = True
        mock_repo_cls.return_value = mock_repo

        valid_platforms = ["workday", "greenhouse", "lever", "ashby", "successfactors"]
        for platform in valid_platforms:
            response = client.post(
                "/watchlist",
                json={"company_name": f"Company_{platform}", "ats_platform": platform},
            )
            assert response.status_code == 201, f"Failed for platform: {platform}"

    @patch("app.api.watchlist.JobsRepository")
    def test_duplicate_company_returns_409(self, mock_repo_cls, client):
        """POST /watchlist with duplicate company returns 409.

        Validates: Requirements 6.7
        """
        mock_repo = MagicMock()
        mock_repo.add_to_watchlist.return_value = False
        mock_repo_cls.return_value = mock_repo

        response = client.post(
            "/watchlist",
            json={"company_name": "Philips", "ats_platform": "workday"},
        )

        assert response.status_code == 409


class TestPatchWatchlistTier:
    """Tests for PATCH /watchlist/{company} endpoint."""

    @patch("app.api.watchlist.JobsRepository")
    def test_updates_tier_successfully(self, mock_repo_cls, client):
        """PATCH /watchlist/{company} updates tier to valid value.

        Validates: Requirements 9.4
        """
        mock_repo = MagicMock()
        mock_repo.update_watchlist_tier.return_value = True
        mock_repo_cls.return_value = mock_repo

        response = client.patch(
            "/watchlist/Philips",
            json={"tier": "tier1"},
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Updated tier for 'Philips' to 'tier1'"}
        mock_repo.update_watchlist_tier.assert_called_once_with("Philips", "tier1")

    @patch("app.api.watchlist.JobsRepository")
    def test_updates_to_tier2(self, mock_repo_cls, client):
        """PATCH /watchlist/{company} updates tier to tier2.

        Validates: Requirements 9.1, 9.4
        """
        mock_repo = MagicMock()
        mock_repo.update_watchlist_tier.return_value = True
        mock_repo_cls.return_value = mock_repo

        response = client.patch(
            "/watchlist/Dozee",
            json={"tier": "tier2"},
        )

        assert response.status_code == 200
        mock_repo.update_watchlist_tier.assert_called_once_with("Dozee", "tier2")

    @patch("app.api.watchlist.JobsRepository")
    def test_updates_to_tier3(self, mock_repo_cls, client):
        """PATCH /watchlist/{company} updates tier to tier3.

        Validates: Requirements 9.1, 9.4
        """
        mock_repo = MagicMock()
        mock_repo.update_watchlist_tier.return_value = True
        mock_repo_cls.return_value = mock_repo

        response = client.patch(
            "/watchlist/Abbott",
            json={"tier": "tier3"},
        )

        assert response.status_code == 200
        mock_repo.update_watchlist_tier.assert_called_once_with("Abbott", "tier3")

    def test_invalid_tier_returns_422(self, client):
        """PATCH /watchlist/{company} with invalid tier returns 422.

        Validates: Requirements 9.1
        """
        response = client.patch(
            "/watchlist/Philips",
            json={"tier": "tier4"},
        )

        assert response.status_code == 422
        assert response.json()["detail"] == "Tier must be one of: tier1, tier2, tier3"

    def test_empty_tier_returns_422(self, client):
        """PATCH /watchlist/{company} with empty tier returns 422.

        Validates: Requirements 9.1
        """
        response = client.patch(
            "/watchlist/Philips",
            json={"tier": ""},
        )

        assert response.status_code == 422
        assert response.json()["detail"] == "Tier must be one of: tier1, tier2, tier3"

    def test_arbitrary_string_tier_returns_422(self, client):
        """PATCH /watchlist/{company} with arbitrary string returns 422.

        Validates: Requirements 9.1
        """
        response = client.patch(
            "/watchlist/Philips",
            json={"tier": "gold"},
        )

        assert response.status_code == 422
        assert response.json()["detail"] == "Tier must be one of: tier1, tier2, tier3"

    @patch("app.api.watchlist.JobsRepository")
    def test_company_not_found_returns_404(self, mock_repo_cls, client):
        """PATCH /watchlist/{company} for non-existent company returns 404.

        Validates: Requirements 9.4
        """
        mock_repo = MagicMock()
        mock_repo.update_watchlist_tier.return_value = False
        mock_repo_cls.return_value = mock_repo

        response = client.patch(
            "/watchlist/NonExistentCo",
            json={"tier": "tier1"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Company not found in watchlist"


class TestGetWatchlistAtsInfo:
    """Tests for GET /watchlist/ats-info endpoint."""

    @patch("app.api.watchlist.JobsRepository")
    def test_returns_companies_grouped_by_platform(self, mock_repo_cls, client):
        """GET /watchlist/ats-info returns companies grouped by platform.

        Validates: Requirements 6.5
        """
        mock_repo = MagicMock()
        mock_repo.get_watchlist_grouped_by_ats.return_value = [
            {"platform": "workday", "companies": ["Philips", "Medtronic"]},
            {"platform": "lever", "companies": ["Dozee"]},
        ]
        mock_repo_cls.return_value = mock_repo

        response = client.get("/watchlist/ats-info")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0] == {"platform": "workday", "companies": ["Philips", "Medtronic"]}
        assert data[1] == {"platform": "lever", "companies": ["Dozee"]}

    @patch("app.api.watchlist.JobsRepository")
    def test_excludes_companies_without_ats_platform(self, mock_repo_cls, client):
        """GET /watchlist/ats-info excludes companies without ats_platform.

        Validates: Requirements 6.5, 6.6
        """
        mock_repo = MagicMock()
        # The repository method already filters out companies without ats_platform
        mock_repo.get_watchlist_grouped_by_ats.return_value = [
            {"platform": "workday", "companies": ["Philips"]},
        ]
        mock_repo_cls.return_value = mock_repo

        response = client.get("/watchlist/ats-info")

        assert response.status_code == 200
        data = response.json()
        # Only companies with ats_platform should appear
        assert len(data) == 1
        assert data[0]["platform"] == "workday"

    @patch("app.api.watchlist.JobsRepository")
    def test_returns_empty_list_when_no_ats_companies(self, mock_repo_cls, client):
        """GET /watchlist/ats-info returns empty list when no companies have ats_platform."""
        mock_repo = MagicMock()
        mock_repo.get_watchlist_grouped_by_ats.return_value = []
        mock_repo_cls.return_value = mock_repo

        response = client.get("/watchlist/ats-info")

        assert response.status_code == 200
        assert response.json() == []
