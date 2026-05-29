"""Pydantic request/response models for the JobCopilot API."""

from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    """Response model for a single job listing."""

    title: str
    company: str
    location: str
    source: str
    job_url: str
    description: str
    job_type: str
    salary: str
    date_posted: str
    search_term: str
    created_at: str
    updated_at: str


class PaginatedJobsResponse(BaseModel):
    """Response model for paginated job listings."""

    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatsResponse(BaseModel):
    """Response model for dashboard summary metrics."""

    total_jobs: int
    jobs_today: int
    jobs_this_week: int
    saved_jobs: int
    applied_jobs: int
    companies_tracked: int


class SaveJobRequest(BaseModel):
    """Request model for saving a job."""

    job_url: str
    title: str
    company: str
    location: str
    source: str
    date_posted: str


class ApplyJobRequest(BaseModel):
    """Request model for marking a job as applied."""

    job_url: str
    title: str
    company: str
    location: str
    status: str = "Interested"


class WatchlistRequest(BaseModel):
    """Request model for adding a company to the watchlist."""

    company_name: str = Field(..., min_length=1, max_length=100)
