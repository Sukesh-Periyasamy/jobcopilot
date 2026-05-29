"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    ApplyJobRequest,
    JobResponse,
    PaginatedJobsResponse,
    SaveJobRequest,
    StatsResponse,
    WatchlistRequest,
)


class TestJobResponse:
    def test_valid_job_response(self):
        job = JobResponse(
            title="Software Engineer",
            company="Acme Corp",
            location="Bangalore",
            source="linkedin",
            job_url="https://example.com/job/1",
            description="A great job",
            job_type="full-time",
            salary="10-15 LPA",
            date_posted="2024-01-15",
            search_term="Python Developer",
            created_at="2024-01-15T10:00:00Z",
            updated_at="2024-01-15T10:00:00Z",
        )
        assert job.title == "Software Engineer"
        assert job.company == "Acme Corp"
        assert job.source == "linkedin"


class TestPaginatedJobsResponse:
    def test_valid_paginated_response(self):
        resp = PaginatedJobsResponse(
            jobs=[],
            total=0,
            page=1,
            page_size=50,
            total_pages=0,
        )
        assert resp.total == 0
        assert resp.page_size == 50

    def test_with_jobs(self):
        job = JobResponse(
            title="Engineer",
            company="Corp",
            location="Remote",
            source="indeed",
            job_url="https://example.com/job/2",
            description="",
            job_type="",
            salary="",
            date_posted="",
            search_term="Engineer",
            created_at="2024-01-15T10:00:00Z",
            updated_at="2024-01-15T10:00:00Z",
        )
        resp = PaginatedJobsResponse(
            jobs=[job],
            total=1,
            page=1,
            page_size=50,
            total_pages=1,
        )
        assert len(resp.jobs) == 1
        assert resp.jobs[0].title == "Engineer"


class TestStatsResponse:
    def test_valid_stats(self):
        stats = StatsResponse(
            total_jobs=100,
            jobs_today=5,
            jobs_this_week=30,
            saved_jobs=10,
            applied_jobs=3,
            companies_tracked=6,
        )
        assert stats.total_jobs == 100
        assert stats.companies_tracked == 6


class TestSaveJobRequest:
    def test_valid_save_request(self):
        req = SaveJobRequest(
            job_url="https://example.com/job/1",
            title="Software Engineer",
            company="Acme Corp",
            location="Bangalore",
            source="linkedin",
            date_posted="2024-01-15",
        )
        assert req.job_url == "https://example.com/job/1"
        assert req.title == "Software Engineer"


class TestApplyJobRequest:
    def test_valid_apply_request_default_status(self):
        req = ApplyJobRequest(
            job_url="https://example.com/job/1",
            title="Software Engineer",
            company="Acme Corp",
            location="Bangalore",
        )
        assert req.status == "Interested"

    def test_custom_status(self):
        req = ApplyJobRequest(
            job_url="https://example.com/job/1",
            title="Software Engineer",
            company="Acme Corp",
            location="Bangalore",
            status="Applied",
        )
        assert req.status == "Applied"


class TestWatchlistRequest:
    def test_valid_company_name(self):
        req = WatchlistRequest(company_name="Siemens Healthineers")
        assert req.company_name == "Siemens Healthineers"

    def test_max_length_company_name(self):
        name = "A" * 100
        req = WatchlistRequest(company_name=name)
        assert len(req.company_name) == 100

    def test_company_name_exceeds_max_length(self):
        name = "A" * 101
        with pytest.raises(ValidationError) as exc_info:
            WatchlistRequest(company_name=name)
        assert "company_name" in str(exc_info.value)

    def test_empty_company_name_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WatchlistRequest(company_name="")
        assert "company_name" in str(exc_info.value)

    def test_single_char_company_name(self):
        req = WatchlistRequest(company_name="A")
        assert req.company_name == "A"
