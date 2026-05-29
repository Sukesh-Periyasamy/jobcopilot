"""Models package for JobCopilot Engine."""

from app.models.job import (
    BulkInsertResult,
    FilterCriteria,
    JobRecord,
    PaginatedResult,
    ScrapeHistoryEntry,
    ScrapeResult,
)

__all__ = [
    "JobRecord",
    "ScrapeResult",
    "BulkInsertResult",
    "ScrapeHistoryEntry",
    "FilterCriteria",
    "PaginatedResult",
]
