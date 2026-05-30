"""Internship Tracker service for Career Opportunity Radar.

Filters and retrieves internship-type positions from the jobs collection
using predefined internship keywords matched against job titles.
"""

from __future__ import annotations

import logging
import math
import re

from app.database.connection import get_database
from app.services.constants import INTERNSHIP_KEYWORDS

logger = logging.getLogger(__name__)


class InternshipTracker:
    """Identifies and filters internship-type positions using predefined keywords.

    Stateless service that builds MongoDB regex queries to match internship
    keywords in job titles and returns paginated results sorted by date_posted.
    """

    def get_internships(
        self, keyword: str | None = None, page: int = 1, page_size: int = 50
    ) -> dict:
        """Return paginated internships, optionally filtered by specific keyword.

        Args:
            keyword: Optional specific Internship_Keyword to filter by.
                     If None, matches any of the 15 predefined internship keywords.
            page: Page number (1-indexed).
            page_size: Number of records per page.

        Returns:
            Dict with keys: items (list of job dicts), total, page, page_size.
        """
        db = get_database()
        jobs_collection = db["jobs"]

        query = self._build_internship_query(keyword)
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

    def _build_internship_query(self, keyword: str | None = None) -> dict:
        """Build regex query matching internship keywords in the title field.

        Args:
            keyword: Optional specific keyword to match. If None, builds a
                     $or query matching any of the 15 internship keywords.

        Returns:
            MongoDB query document with case-insensitive regex matching.
        """
        if keyword is not None:
            # Match a specific keyword in the title (case-insensitive)
            return {
                "title": {"$regex": re.escape(keyword), "$options": "i"}
            }

        # Match any of the predefined internship keywords in the title
        conditions = [
            {"title": {"$regex": re.escape(kw), "$options": "i"}}
            for kw in INTERNSHIP_KEYWORDS
        ]
        return {"$or": conditions}
