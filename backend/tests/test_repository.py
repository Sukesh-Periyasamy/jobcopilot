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
        # Should have 7 indexes: job_url unique, date_posted, source, company, text, source_type, source_platform
        assert len(call_args) == 7

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
        assert "Niramai" in names
        assert len(names) == 13
        # Verify ats_platform is included
        platforms = {d["company_name"]: d["ats_platform"] for d in docs}
        assert platforms["Philips"] == "workday"
        assert platforms["Siemens Healthineers"] == "successfactors"
        assert platforms["Dozee"] == "lever"
        assert platforms["Niramai"] == "greenhouse"
        # Verify tier is included
        tiers = {d["company_name"]: d["tier"] for d in docs}
        assert tiers["Philips"] == "tier3"

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
            {"company_name": "Google", "ats_platform": "greenhouse", "tier": "tier1"},
            {"company_name": "Meta"},
        ]

        result = repo.get_watchlist()

        assert result == [
            {"company_name": "Google", "ats_platform": "greenhouse", "tier": "tier1"},
            {"company_name": "Meta", "ats_platform": None, "tier": "tier3"},
        ]

    def test_add_to_watchlist_success(self, repo, mock_db):
        mock_db.watchlist.count_documents.return_value = 5
        mock_db.watchlist.insert_one.return_value = MagicMock()

        result = repo.add_to_watchlist("NewCompany")

        assert result is True

    def test_add_to_watchlist_with_ats_platform(self, repo, mock_db):
        mock_db.watchlist.count_documents.return_value = 5
        mock_db.watchlist.insert_one.return_value = MagicMock()

        result = repo.add_to_watchlist("NewCompany", ats_platform="workday")

        assert result is True
        doc = mock_db.watchlist.insert_one.call_args[0][0]
        assert doc["company_name"] == "NewCompany"
        assert doc["ats_platform"] == "workday"

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


class TestDocToJobRecordBackwardCompat:
    """Tests for _doc_to_job_record backward compatibility with legacy documents."""

    def test_legacy_doc_missing_source_type_defaults_to_jobspy(self, repo):
        doc = {
            "title": "Legacy Job",
            "company": "OldCorp",
            "location": "Mumbai",
            "source": "LinkedIn",
            "job_url": "https://example.com/legacy/1",
            "description": "Old job",
            "job_type": "full-time",
            "salary": "",
            "date_posted": "2023-06-01",
            "search_term": "engineer",
            "created_at": "2023-06-01T00:00:00+00:00",
            "updated_at": "2023-06-01T00:00:00+00:00",
        }

        from app.database.repository import JobsRepository
        record = JobsRepository._doc_to_job_record(doc)

        assert record.source_type == "jobspy"

    def test_legacy_doc_missing_source_platform_derived_from_source(self, repo):
        doc = {
            "title": "Legacy Job",
            "company": "OldCorp",
            "location": "Mumbai",
            "source": "Indeed",
            "job_url": "https://example.com/legacy/2",
        }

        from app.database.repository import JobsRepository
        record = JobsRepository._doc_to_job_record(doc)

        assert record.source_platform == "indeed"

    def test_legacy_doc_source_platform_lowercased(self, repo):
        doc = {
            "title": "Job",
            "company": "Co",
            "location": "BLR",
            "source": "NAUKRI",
            "job_url": "https://example.com/legacy/3",
        }

        from app.database.repository import JobsRepository
        record = JobsRepository._doc_to_job_record(doc)

        assert record.source_platform == "naukri"

    def test_doc_with_source_type_and_platform_uses_them(self, repo):
        doc = {
            "title": "New Job",
            "company": "NewCorp",
            "location": "Delhi",
            "source": "workday",
            "job_url": "https://example.com/new/1",
            "source_type": "jobhive",
            "source_platform": "workday",
        }

        from app.database.repository import JobsRepository
        record = JobsRepository._doc_to_job_record(doc)

        assert record.source_type == "jobhive"
        assert record.source_platform == "workday"


class TestGetExportJobs:
    """Tests for get_export_jobs method."""

    def test_returns_job_records_with_limit(self, repo, mock_db):
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = MagicMock(return_value=iter([
            {"title": "Job 1", "company": "Co", "location": "BLR",
             "source": "linkedin", "job_url": "http://x.com/1"},
            {"title": "Job 2", "company": "Co2", "location": "MUM",
             "source": "indeed", "job_url": "http://x.com/2"},
        ]))
        mock_db.jobs.find.return_value = mock_cursor

        filters = FilterCriteria()
        result = repo.get_export_jobs(filters)

        assert len(result) == 2
        assert all(isinstance(r, JobRecord) for r in result)
        mock_cursor.limit.assert_called_once_with(10000)

    def test_export_jobs_applies_sort(self, repo, mock_db):
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))
        mock_db.jobs.find.return_value = mock_cursor

        filters = FilterCriteria()
        repo.get_export_jobs(filters)

        mock_cursor.sort.assert_called_once_with("date_posted", -1)

    def test_export_jobs_empty_result(self, repo, mock_db):
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))
        mock_db.jobs.find.return_value = mock_cursor

        filters = FilterCriteria()
        result = repo.get_export_jobs(filters)

        assert result == []


class TestGetWatchlistGroupedByAts:
    """Tests for get_watchlist_grouped_by_ats method."""

    def test_groups_companies_by_platform(self, repo, mock_db):
        mock_db.watchlist.find.return_value = [
            {"company_name": "Philips", "ats_platform": "workday"},
            {"company_name": "Medtronic", "ats_platform": "workday"},
            {"company_name": "Dozee", "ats_platform": "lever"},
            {"company_name": "Niramai", "ats_platform": "greenhouse"},
        ]

        result = repo.get_watchlist_grouped_by_ats()

        # Convert to dict for easier assertion
        groups = {g["platform"]: g["companies"] for g in result}
        assert "workday" in groups
        assert set(groups["workday"]) == {"Philips", "Medtronic"}
        assert groups["lever"] == ["Dozee"]
        assert groups["greenhouse"] == ["Niramai"]

    def test_excludes_companies_without_platform(self, repo, mock_db):
        mock_db.watchlist.find.return_value = [
            {"company_name": "Philips", "ats_platform": "workday"},
        ]

        result = repo.get_watchlist_grouped_by_ats()

        # Only companies with ats_platform should appear
        all_companies = []
        for group in result:
            all_companies.extend(group["companies"])
        assert "Philips" in all_companies
        assert len(all_companies) == 1

    def test_empty_watchlist_returns_empty(self, repo, mock_db):
        mock_db.watchlist.find.return_value = []

        result = repo.get_watchlist_grouped_by_ats()

        assert result == []


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


# Feature: jobcopilot-v1.1-upgrade, Property 4: Backward Compatibility Defaults
# Validates: Requirements 3.5

from hypothesis import given, settings
from hypothesis import strategies as st

from app.database.repository import JobsRepository

# Strategy for source values that legacy documents might contain
_legacy_sources = st.sampled_from(["linkedin", "indeed", "naukri", "google", "LinkedIn", "Indeed"])

# Strategy for optional string fields (either missing or present)
_optional_str = st.one_of(st.none(), st.text(min_size=0, max_size=50))


@st.composite
def legacy_mongo_documents(draw):
    """Generate legacy MongoDB documents that lack source_type and source_platform."""
    source = draw(_legacy_sources)
    doc = {
        "title": draw(st.text(min_size=1, max_size=100)),
        "company": draw(st.text(min_size=1, max_size=100)),
        "location": draw(st.text(min_size=1, max_size=100)),
        "source": source,
        "job_url": draw(st.text(min_size=1, max_size=200)),
    }

    # Optionally include other fields (but NEVER source_type or source_platform)
    description = draw(_optional_str)
    if description is not None:
        doc["description"] = description

    job_type = draw(_optional_str)
    if job_type is not None:
        doc["job_type"] = job_type

    salary = draw(_optional_str)
    if salary is not None:
        doc["salary"] = salary

    date_posted = draw(_optional_str)
    if date_posted is not None:
        doc["date_posted"] = date_posted

    search_term = draw(_optional_str)
    if search_term is not None:
        doc["search_term"] = search_term

    created_at = draw(_optional_str)
    if created_at is not None:
        doc["created_at"] = created_at

    updated_at = draw(_optional_str)
    if updated_at is not None:
        doc["updated_at"] = updated_at

    return doc


class TestBackwardCompatibilityDefaults:
    """Property test: legacy documents get correct default source_type and source_platform."""

    @given(doc=legacy_mongo_documents())
    @settings(max_examples=100)
    def test_legacy_doc_defaults(self, doc):
        """
        **Validates: Requirements 3.5**

        For any legacy MongoDB document missing source_type and source_platform:
        - source_type must default to "jobspy"
        - source_platform must equal doc["source"].strip().lower()
        """
        result = JobsRepository._doc_to_job_record(doc)

        assert result.source_type == "jobspy"
        assert result.source_platform == doc["source"].strip().lower()


# Feature: jobcopilot-v1.1-upgrade, Property 8: ATS-Info Grouping Correctness
# Validates: Requirements 6.5

_ats_platforms = st.sampled_from(["workday", "greenhouse", "lever", "ashby", "successfactors", None])


@st.composite
def watchlist_entries(draw):
    """Generate a list of watchlist entries with unique company names and various ats_platform values."""
    # Generate between 0 and 30 entries with unique company names
    num_entries = draw(st.integers(min_value=0, max_value=30))
    names = draw(
        st.lists(
            st.text(alphabet=st.characters(whitelist_categories=("L", "N", "Zs")), min_size=1, max_size=50),
            min_size=num_entries,
            max_size=num_entries,
            unique=True,
        )
    )
    entries = []
    for name in names:
        platform = draw(_ats_platforms)
        entries.append({"company_name": name, "ats_platform": platform})
    return entries


class TestAtsInfoGroupingCorrectness:
    """Property test: ATS-info grouping returns correct groups."""

    @given(entries=watchlist_entries())
    @settings(max_examples=100)
    def test_ats_info_grouping(self, entries):
        """
        **Validates: Requirements 6.5**

        For any set of watchlist entries with various ats_platform values:
        - Every company in a group has the corresponding ats_platform value
        - Every company with a non-null ats_platform appears in exactly one group
        - Companies with null ats_platform do NOT appear in any group
        """
        # Filter entries the way the repository method does: only non-null ats_platform
        filtered_entries = [
            e for e in entries if e["ats_platform"] is not None
        ]

        with patch("app.database.repository.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_db.__getitem__ = MagicMock(side_effect=lambda name: {
                "jobs": mock_db.jobs,
                "saved_jobs": mock_db.saved_jobs,
                "applied_jobs": mock_db.applied_jobs,
                "company_watchlist": mock_db.watchlist,
                "scrape_history": mock_db.scrape_history,
            }.get(name, MagicMock()))
            mock_db.jobs = MagicMock()
            mock_db.saved_jobs = MagicMock()
            mock_db.applied_jobs = MagicMock()
            mock_db.watchlist = MagicMock()
            mock_db.scrape_history = MagicMock()
            mock_db.watchlist.count_documents.return_value = 0
            mock_get_db.return_value = mock_db

            repo = JobsRepository()

            # Mock the find() call used by get_watchlist_grouped_by_ats
            mock_db.watchlist.find.return_value = filtered_entries

            result = repo.get_watchlist_grouped_by_ats()

        # Build a lookup from entries: company_name -> ats_platform
        platform_by_company = {e["company_name"]: e["ats_platform"] for e in entries}

        # Property 1: Every company in a group has the corresponding ats_platform value
        for group in result:
            platform = group["platform"]
            for company in group["companies"]:
                assert platform_by_company[company] == platform, (
                    f"Company '{company}' is in group '{platform}' but has platform "
                    f"'{platform_by_company[company]}'"
                )

        # Property 2: Every company with a non-null ats_platform appears in exactly one group
        all_grouped_companies = []
        for group in result:
            all_grouped_companies.extend(group["companies"])

        companies_with_platform = {
            e["company_name"] for e in entries if e["ats_platform"] is not None
        }
        assert set(all_grouped_companies) == companies_with_platform, (
            "Not all companies with non-null platform appear in groups"
        )
        # Check no duplicates (exactly one group)
        assert len(all_grouped_companies) == len(set(all_grouped_companies)), (
            "Some companies appear in more than one group"
        )

        # Property 3: Companies with null ats_platform do NOT appear in any group
        companies_without_platform = {
            e["company_name"] for e in entries if e["ats_platform"] is None
        }
        grouped_set = set(all_grouped_companies)
        assert grouped_set.isdisjoint(companies_without_platform), (
            "Companies with null ats_platform should not appear in any group"
        )
