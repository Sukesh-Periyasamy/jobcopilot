"""Unit tests for the JobsRepository module."""

import os
from dataclasses import asdict
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.models.job import (
    BulkInsertResult,
    FilterCriteria,
    JobRecord,
    PaginatedResult,
    ScrapeHistoryEntry,
)


def _make_job_record(**kwargs) -> JobRecord:
    """Helper to create a JobRecord with sensible defaults."""
    defaults = {
        "title": "Software Engineer",
        "company": "TestCorp",
        "location": "Bangalore",
        "source": "linkedin",
        "job_url": "https://example.com/job/1",
        "description": "A great job",
        "job_type": "full-time",
        "salary": "10-15 LPA",
        "date_posted": "2024-01-15",
        "search_term": "Python Developer",
        "created_at": "2024-01-15T10:00:00+00:00",
        "updated_at": "2024-01-15T10:00:00+00:00",
    }
    defaults.update(kwargs)
    return JobRecord(**defaults)


@pytest.fixture
def mock_db():
    """Create a mock database with all required collections."""
    db = MagicMock()
    db.__getitem__ = MagicMock(side_effect=lambda name: {
        "jobs": db.jobs,
        "saved_jobs": db.saved_jobs,
        "applied_jobs": db.applied_jobs,
        "company_watchlist": db.watchlist,
        "scrape_history": db.scrape_history,
    }.get(name, MagicMock()))
    db.jobs = MagicMock()
    db.saved_jobs = MagicMock()
    db.applied_jobs = MagicMock()
    db.watchlist = MagicMock()
    db.scrape_history = MagicMock()
    return db


@pytest.fixture
def repo(mock_db):
    """Create a JobsRepository with mocked database connection."""
    # Watchlist is empty so seeding will happen
    mock_db.watchlist.count_documents.return_value = 0

    with patch("app.database.repository.get_database", return_value=mock_db):
        from app.database.repository import JobsRepository
        repository = JobsRepository()
    return repository


class TestEnsureIndexes:
    """Tests for ensure_indexes method."""

    def test_creates_jobs_indexes(self, repo, mock_db):
        mock_db.jobs.create_indexes.assert_called_once()
        call_args = mock_db.jobs.create_indexes.call_args[0][0]
        # Should have 5 indexes: job_url unique, date_posted, source, company, text
        assert len(call_args) == 5

    def test_creates_saved_jobs_index(self, repo, mock_db):
        mock_db.saved_jobs.create_index.assert_called_once_with("job_url", unique=True)

    def test_creates_applied_jobs_index(self, repo, mock_db):
        mock_db.applied_jobs.create_index.assert_called_once_with("job_url", unique=True)

    def test_creates_watchlist_index(self, repo, mock_db):
        mock_db.watchlist.create_index.assert_called_once_with("company_name", unique=True)


class TestSeedDefaultWatchlist:
    """Tests for default watchlist seeding."""

    def test_seeds_when_empty(self, repo, mock_db):
        mock_db.watchlist.insert_many.assert_called_once()
        docs = mock_db.watchlist.insert_many.call_args[0][0]
        names = [d["company_name"] for d in docs]
        assert "Siemens Healthineers" in names
        assert "GE HealthCare" in names
        assert "Philips" in names
        assert "Medtronic" in names
        assert "Abbott" in names
        assert "Dozee" in names
        assert len(names) == 6

    def test_does_not_seed_when_not_empty(self, mock_db):
        mock_db.watchlist.count_documents.return_value = 3

        with patch("app.database.repository.get_database", return_value=mock_db):
            from app.database.repository import JobsRepository
            repository = JobsRepository()

        mock_db.watchlist.insert_many.assert_not_called()


class TestBulkInsert:
    """Tests for bulk_insert method."""

    def test_empty_records_returns_empty_result(self, repo):
        result = repo.bulk_insert([])
        assert result.inserted_count == 0
        assert result.duplicates_skipped == 0
        assert result.new_jobs == []

    def test_successful_insert(self, repo, mock_db):
        records = [_make_job_record(job_url=f"https://example.com/job/{i}") for i in range(3)]
        mock_result = MagicMock()
        mock_result.inserted_ids = ["id1", "id2", "id3"]
        mock_db.jobs.insert_many.return_value = mock_result

        result = repo.bulk_insert(records)

        assert result.inserted_count == 3
        assert result.duplicates_skipped == 0
        assert len(result.new_jobs) == 3
        mock_db.jobs.insert_many.assert_called_once()

    def test_handles_duplicate_key_errors(self, repo, mock_db):
        from pymongo.errors import BulkWriteError

        records = [_make_job_record(job_url=f"https://example.com/job/{i}") for i in range(5)]
        error_details = {
            "nInserted": 3,
            "writeErrors": [
                {"code": 11000, "index": 3},
                {"code": 11000, "index": 4},
            ],
        }
        mock_db.jobs.insert_many.side_effect = BulkWriteError(error_details)

        result = repo.bulk_insert(records)

        assert result.inserted_count == 3
        assert result.duplicates_skipped == 2


class TestRecordScrapeHistory:
    """Tests for record_scrape_history method."""

    def test_inserts_history_entry(self, repo, mock_db):
        entry = ScrapeHistoryEntry(
            timestamp="2024-01-15T10:00:00+00:00",
            jobs_found=50,
            duplicates_skipped=10,
            errors=["source1 failed"],
        )

        repo.record_scrape_history(entry)

        mock_db.scrape_history.insert_one.assert_called_once()
        doc = mock_db.scrape_history.insert_one.call_args[0][0]
        assert doc["jobs_found"] == 50
        assert doc["duplicates_skipped"] == 10
        assert doc["errors"] == ["source1 failed"]


class TestGetJobs:
    """Tests for get_jobs method."""

    def test_returns_paginated_result(self, repo, mock_db):
        mock_db.jobs.count_documents.return_value = 100
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = MagicMock(return_value=iter([
            {"title": "Job 1", "company": "Co", "location": "BLR",
             "source": "linkedin", "job_url": "http://x.com/1"},
        ]))
        mock_db.jobs.find.return_value = mock_cursor

        filters = FilterCriteria()
        result = repo.get_jobs(filters, page=1, page_size=50)

        assert result.total == 100
        assert result.page == 1
        assert result.page_size == 50
        assert result.total_pages == 2
        assert len(result.jobs) == 1

    def test_empty_result(self, repo, mock_db):
        mock_db.jobs.count_documents.return_value = 0
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))
        mock_db.jobs.find.return_value = mock_cursor

        filters = FilterCriteria()
        result = repo.get_jobs(filters, page=1, page_size=50)

        assert result.total == 0
        assert result.total_pages == 0
        assert result.jobs == []


class TestGetRecentJobs:
    """Tests for get_recent_jobs method."""

    def test_returns_limited_jobs(self, repo, mock_db):
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = MagicMock(return_value=iter([
            {"title": "Job 1", "company": "Co", "location": "BLR",
             "source": "linkedin", "job_url": "http://x.com/1"},
        ]))
        mock_db.jobs.find.return_value = mock_cursor

        result = repo.get_recent_jobs(limit=10)

        assert len(result) == 1
        mock_cursor.sort.assert_called_once_with("date_posted", -1)
        mock_cursor.limit.assert_called_once_with(10)


class TestSearchJobs:
    """Tests for search_jobs method."""

    def test_uses_text_search(self, repo, mock_db):
        mock_db.jobs.count_documents.return_value = 5
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))
        mock_db.jobs.find.return_value = mock_cursor

        repo.search_jobs("python developer", page=1, page_size=50)

        # Verify text search filter was used
        find_call = mock_db.jobs.find.call_args[0][0]
        assert "$text" in find_call
        assert find_call["$text"]["$search"] == "python developer"


class TestGetJobsByCompany:
    """Tests for get_jobs_by_company method."""

    def test_uses_case_insensitive_match(self, repo, mock_db):
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))
        mock_db.jobs.find.return_value = mock_cursor

        repo.get_jobs_by_company("TestCorp")

        find_call = mock_db.jobs.find.call_args[0][0]
        assert "company" in find_call
        assert "$regex" in find_call["company"]
        assert "$options" in find_call["company"]
        assert find_call["company"]["$options"] == "i"


class TestSaveJob:
    """Tests for save_job and remove_saved_job methods."""

    def test_save_job_success(self, repo, mock_db):
        job_data = {"job_url": "http://x.com/1", "title": "Dev"}
        mock_db.saved_jobs.insert_one.return_value = MagicMock()

        result = repo.save_job(job_data)

        assert result is True
        mock_db.saved_jobs.insert_one.assert_called_once()

    def test_save_job_duplicate_returns_false(self, repo, mock_db):
        job_data = {"job_url": "http://x.com/1", "title": "Dev"}
        mock_db.saved_jobs.insert_one.side_effect = Exception("duplicate key")

        result = repo.save_job(job_data)

        assert result is False

    def test_remove_saved_job_success(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        mock_db.saved_jobs.delete_one.return_value = mock_result

        result = repo.remove_saved_job("http://x.com/1")

        assert result is True

    def test_remove_saved_job_not_found(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.deleted_count = 0
        mock_db.saved_jobs.delete_one.return_value = mock_result

        result = repo.remove_saved_job("http://x.com/nonexistent")

        assert result is False


class TestAppliedJobs:
    """Tests for applied jobs CRUD methods."""

    def test_add_applied_job(self, repo, mock_db):
        job_data = {"job_url": "http://x.com/1", "title": "Dev", "company": "Co"}
        mock_db.applied_jobs.insert_one.return_value = MagicMock()

        repo.add_applied_job(job_data, status="Applied")

        mock_db.applied_jobs.insert_one.assert_called_once()
        doc = mock_db.applied_jobs.insert_one.call_args[0][0]
        assert doc["status"] == "Applied"
        assert "date_applied" in doc
        assert "updated_at" in doc

    def test_add_applied_job_default_status(self, repo, mock_db):
        job_data = {"job_url": "http://x.com/1", "title": "Dev"}
        mock_db.applied_jobs.insert_one.return_value = MagicMock()

        repo.add_applied_job(job_data)

        doc = mock_db.applied_jobs.insert_one.call_args[0][0]
        assert doc["status"] == "Interested"

    def test_update_application_status(self, repo, mock_db):
        repo.update_application_status("http://x.com/1", "Interview")

        mock_db.applied_jobs.update_one.assert_called_once()
        call_args = mock_db.applied_jobs.update_one.call_args[0]
        assert call_args[0] == {"job_url": "http://x.com/1"}
        assert call_args[1]["$set"]["status"] == "Interview"


class TestWatchlist:
    """Tests for watchlist CRUD methods."""

    def test_get_watchlist(self, repo, mock_db):
        mock_db.watchlist.find.return_value = [
            {"company_name": "Google"},
            {"company_name": "Meta"},
        ]

        result = repo.get_watchlist()

        assert result == ["Google", "Meta"]

    def test_add_to_watchlist_success(self, repo, mock_db):
        mock_db.watchlist.count_documents.return_value = 5
        mock_db.watchlist.insert_one.return_value = MagicMock()

        result = repo.add_to_watchlist("NewCompany")

        assert result is True

    def test_add_to_watchlist_name_too_long(self, repo, mock_db):
        result = repo.add_to_watchlist("A" * 101)

        assert result is False

    def test_add_to_watchlist_empty_name(self, repo, mock_db):
        result = repo.add_to_watchlist("")

        assert result is False

    def test_add_to_watchlist_max_entries_reached(self, repo, mock_db):
        mock_db.watchlist.count_documents.return_value = 50

        result = repo.add_to_watchlist("NewCompany")

        assert result is False

    def test_remove_from_watchlist_success(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        mock_db.watchlist.delete_one.return_value = mock_result

        result = repo.remove_from_watchlist("Google")

        assert result is True

    def test_remove_from_watchlist_not_found(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.deleted_count = 0
        mock_db.watchlist.delete_one.return_value = mock_result

        result = repo.remove_from_watchlist("NonExistent")

        assert result is False


class TestGetStats:
    """Tests for get_stats method."""

    def test_returns_all_metrics(self, repo, mock_db):
        mock_db.jobs.count_documents.side_effect = [100, 5, 25]
        mock_db.saved_jobs.count_documents.return_value = 10
        mock_db.applied_jobs.count_documents.return_value = 3
        mock_db.watchlist.count_documents.return_value = 6

        stats = repo.get_stats()

        assert stats["total_jobs"] == 100
        assert stats["jobs_today"] == 5
        assert stats["jobs_this_week"] == 25
        assert stats["saved_jobs"] == 10
        assert stats["applied_jobs"] == 3
        assert stats["companies_tracked"] == 6
