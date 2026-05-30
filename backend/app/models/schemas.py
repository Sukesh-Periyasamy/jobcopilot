"""Pydantic request/response models for the JobCopilot API."""

from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    """Response model for a single job listing."""

    title: str
    company: str
    location: str
    source: str
    source_type: str
    source_platform: str
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
    ats_platform: str | None = Field(
        None, pattern="^(workday|greenhouse|lever|ashby|successfactors)$"
    )


class WatchlistEntry(BaseModel):
    """Response model for a single watchlist entry."""

    company_name: str
    ats_platform: str | None = None
    tier: str = "tier3"


class WatchlistTierUpdate(BaseModel):
    """Request model for updating a watchlist company's tier."""

    tier: str


class AtsGroupResponse(BaseModel):
    """Response model for companies grouped by ATS platform."""

    platform: str
    companies: list[str]


class CollectionSummary(BaseModel):
    """Response model for a collection summary with job count."""

    name: str
    job_count: int


class CollectionDetail(BaseModel):
    """Response model for detailed collection info including keywords."""

    name: str
    keywords: list[str]
    job_count: int


class OpportunityFeedResponse(BaseModel):
    """Response model for the categorized opportunity feed."""

    top_companies: list[dict]
    new_companies: list[dict]
    remote_jobs: list[JobResponse]
    internships: list[JobResponse]
    research_roles: list[JobResponse]
    healthcare_roles: list[JobResponse]


class AnalyticsResponse(BaseModel):
    """Response model for all analytics metrics."""

    jobs_per_day: list[dict]
    jobs_per_company: list[dict]
    jobs_per_source: list[dict]
    jobs_per_platform: list[dict]
    jobs_per_location: list[dict]
    jobs_per_collection: list[dict]
    top_hiring_companies: list[dict]
    top_locations: list[dict]
    top_ats_platforms: list[dict]
    internship_vs_fulltime: dict
    research_vs_industry: dict


class PersonalDashboardResponse(BaseModel):
    """Response model for the personal dashboard with pinned preferences."""

    pinned_company_jobs: list[JobResponse]
    pinned_collection_jobs: list[JobResponse]
    new_research_opportunities: list[JobResponse]


class PaginatedResult(BaseModel):
    """Generic paginated result model."""

    items: list[dict]
    total: int
    page: int
    page_size: int
