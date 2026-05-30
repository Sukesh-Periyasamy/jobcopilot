"""Data models for JobCopilot Engine.

Defines core dataclasses used across the scraper, repository,
filter engine, and API layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class JobRecord:
    """A normalized job listing record stored in MongoDB.

    All fields are strings. Optional fields that are unavailable
    from the source default to empty string.
    """

    title: str
    company: str
    location: str
    source: str
    job_url: str
    description: str = ""
    job_type: str = ""
    salary: str = ""
    date_posted: str = ""
    search_term: str = ""
    source_type: str = ""       # "jobspy" or "jobhive"
    source_platform: str = ""   # linkedin, indeed, naukri, google, workday, greenhouse, lever, ashby, successfactors
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ScrapeResult:
    """Result of a scrape cycle containing collected jobs and any errors."""

    jobs: list[JobRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class BulkInsertResult:
    """Result of a bulk insert operation into MongoDB."""

    inserted_count: int = 0
    duplicates_skipped: int = 0
    new_jobs: list[JobRecord] = field(default_factory=list)


@dataclass
class ScrapeHistoryEntry:
    """A record of a single scrape run stored in scrape_history collection."""

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    jobs_found: int = 0
    duplicates_skipped: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class FilterCriteria:
    """Filter parameters for querying jobs.

    All fields are optional. None or empty values are ignored
    during query building.
    """

    source: str | None = None
    location: str | None = None
    company: str | None = None
    keyword: str | None = None
    job_type: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    search_term: str | None = None
    source_type: str | None = None
    source_platform: str | None = None


@dataclass
class PaginatedResult:
    """Paginated query result with metadata for frontend rendering."""

    jobs: list[JobRecord] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50
    total_pages: int = 0
