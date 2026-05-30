"""Unit tests for the CollectionEngine service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.collection_engine import CollectionEngine
from app.services.constants import COLLECTIONS


@pytest.fixture
def mock_db():
    """Create a mock MongoDB database."""
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=MagicMock())
    return db


@pytest.fixture
def engine(mock_db):
    """Create a CollectionEngine with a mock database."""
    return CollectionEngine(mock_db)


class TestBuildCollectionQuery:
    """Tests for _build_collection_query method."""

    def test_single_keyword_generates_two_conditions(self, engine):
        """Each keyword should produce a title and description regex condition."""
        query = engine._build_collection_query(["python"])
        assert "$or" in query
        assert len(query["$or"]) == 2
        assert query["$or"][0] == {"title": {"$regex": "python", "$options": "i"}}
        assert query["$or"][1] == {"description": {"$regex": "python", "$options": "i"}}

    def test_multiple_keywords_generate_correct_conditions(self, engine):
        """Multiple keywords should each produce two conditions."""
        query = engine._build_collection_query(["python", "django", "flask"])
        assert "$or" in query
        assert len(query["$or"]) == 6  # 3 keywords * 2 fields

    def test_special_regex_characters_are_escaped(self, engine):
        """Keywords with regex special chars should be escaped."""
        query = engine._build_collection_query(["R&D engineer"])
        assert "$or" in query
        # & is not a regex special char, but let's check the pattern is there
        condition = query["$or"][0]
        assert condition["title"]["$regex"] == "R\\&D\\ engineer"

    def test_empty_keywords_returns_empty_or(self, engine):
        """Empty keywords list should produce an $or with no conditions."""
        query = engine._build_collection_query([])
        assert "$or" in query
        assert len(query["$or"]) == 0


class TestGetAllCollections:
    """Tests for get_all_collections method."""

    def test_returns_all_defined_collections(self, engine):
        """Should return one entry per defined collection."""
        engine._jobs.count_documents = MagicMock(return_value=5)
        result = engine.get_all_collections()
        assert len(result) == len(COLLECTIONS)
        for item in result:
            assert "name" in item
            assert "job_count" in item
            assert item["job_count"] == 5

    def test_collection_names_match_definitions(self, engine):
        """Returned names should match the COLLECTIONS constant."""
        engine._jobs.count_documents = MagicMock(return_value=0)
        result = engine.get_all_collections()
        names = [item["name"] for item in result]
        expected_names = [c.name for c in COLLECTIONS]
        assert names == expected_names


class TestGetCollection:
    """Tests for get_collection method."""

    def test_returns_metadata_for_valid_collection(self, engine):
        """Should return name, keywords, and job_count for a valid collection."""
        engine._jobs.count_documents = MagicMock(return_value=10)
        result = engine.get_collection("Python Development")
        assert result is not None
        assert result["name"] == "Python Development"
        assert "python" in result["keywords"]
        assert result["job_count"] == 10

    def test_returns_none_for_invalid_collection(self, engine):
        """Should return None for a non-existent collection name."""
        result = engine.get_collection("Nonexistent Collection")
        assert result is None

    def test_case_sensitive_name_matching(self, engine):
        """Collection name matching should be case-sensitive."""
        result = engine.get_collection("python development")
        assert result is None


class TestGetCollectionJobs:
    """Tests for get_collection_jobs method."""

    def test_returns_none_for_invalid_collection(self, engine):
        """Should return None for a non-existent collection."""
        result = engine.get_collection_jobs("Nonexistent", page=1, page_size=50)
        assert result is None

    def test_returns_paginated_result_for_valid_collection(self, engine):
        """Should return a PaginatedResult for a valid collection."""
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))

        engine._jobs.count_documents = MagicMock(return_value=0)
        engine._jobs.find = MagicMock(return_value=mock_cursor)

        result = engine.get_collection_jobs("Python Development", page=1, page_size=50)
        assert result is not None
        assert result.total == 0
        assert result.page == 1
        assert result.page_size == 50
        assert result.total_pages == 0
        assert result.jobs == []

    def test_pagination_calculates_total_pages(self, engine):
        """Should correctly calculate total_pages."""
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))

        engine._jobs.count_documents = MagicMock(return_value=120)
        engine._jobs.find = MagicMock(return_value=mock_cursor)

        result = engine.get_collection_jobs("Python Development", page=1, page_size=50)
        assert result is not None
        assert result.total == 120
        assert result.total_pages == 3  # ceil(120/50) = 3

    def test_sort_called_with_date_posted_descending(self, engine):
        """Should sort by date_posted descending."""
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))

        engine._jobs.count_documents = MagicMock(return_value=0)
        engine._jobs.find = MagicMock(return_value=mock_cursor)

        engine.get_collection_jobs("Python Development", page=1, page_size=50)
        mock_cursor.sort.assert_called_once_with("date_posted", -1)
