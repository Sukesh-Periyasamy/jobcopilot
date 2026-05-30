"""Research Tracker service for identifying research institution opportunities.

Filters and retrieves job postings from predefined Indian research institutions
by matching institution names (case-insensitive) in the company or description fields.
"""

from __future__ import annotations

import logging
import re

from app.database.connection import get_database
from app.services.constants import RESEARCH_INSTITUTIONS

logger = logging.getLogger(__name__)


class ResearchTracker:
    """Identifies and retrieves research opportunities from Indian research institutions."""

    def get_research_jobs(
        self, institution: str | None = None, page: int = 1, page_size: int = 50
    ) -> dict:
        """Return paginated research jobs, optionally filtered by institution.

        Args:
            institution: Optional institution name to filter by.
            page: Page number (1-indexed).
            page_size: Number of records per page.

        Returns:
            Dict with keys: items (list of job dicts), total, page, page_size.
        """
        db = get_database()
        jobs_collection = db["jobs"]

        query = self._build_research_query(institution)
        total = jobs_collection.count_documents(query)

        skip = (page - 1) * page_size
        cursor = (
            jobs_collection.find(query, {"_id": 0})
            .sort("date_posted", -1)
            .skip(skip)
            .limit(page_size)
        )

        items = list(cursor)

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_recent_research(self, limit: int = 10) -> list[dict]:
        """Return the most recent research opportunities.

        Args:
            limit: Maximum number of jobs to return (default 10).

        Returns:
            List of job dicts sorted by date_posted descending.
        """
        db = get_database()
        jobs_collection = db["jobs"]

        query = self._build_research_query(None)
        cursor = (
            jobs_collection.find(query, {"_id": 0})
            .sort("date_posted", -1)
            .limit(limit)
        )

        return list(cursor)

    def _build_research_query(self, institution: str | None) -> dict:
        """Build a MongoDB query matching research institution names.

        If institution is None, builds a $or query matching ANY of the 13
        research institution names (case-insensitive regex) in BOTH the
        "company" AND "description" fields.

        If institution is provided, builds a regex query matching just that
        specific institution (case-insensitive) in the "company" or
        "description" fields.

        Args:
            institution: Optional specific institution name to filter by.

        Returns:
            MongoDB query dict.
        """
        if institution is not None:
            escaped = re.escape(institution)
            return {
                "$or": [
                    {"company": {"$regex": escaped, "$options": "i"}},
                    {"description": {"$regex": escaped, "$options": "i"}},
                ]
            }

        # Build $or query matching any research institution in company or description
        or_conditions = []
        for inst in RESEARCH_INSTITUTIONS:
            escaped = re.escape(inst)
            or_conditions.append(
                {"company": {"$regex": escaped, "$options": "i"}}
            )
            or_conditions.append(
                {"description": {"$regex": escaped, "$options": "i"}}
            )

        return {"$or": or_conditions}
