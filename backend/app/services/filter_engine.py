"""Filter engine for building MongoDB query documents.

Converts FilterCriteria into MongoDB query documents with support for
case-insensitive matching, substring search, date ranges, and AND composition.
"""

from __future__ import annotations

import re

from app.models.job import FilterCriteria


def build_query(criteria: FilterCriteria) -> dict:
    """Convert FilterCriteria into a MongoDB query document.

    Ignores None/empty fields. Combines all present criteria with AND logic.
    Returns empty dict if no criteria specified.

    Matching rules:
    - source, job_type, search_term: case-insensitive exact match
    - location, company: case-insensitive substring (regex)
    - keyword: case-insensitive substring in title OR description ($or)
    - date_from/date_to: inclusive range using $gte/$lte on date_posted
    """
    conditions: list[dict] = []

    # Case-insensitive exact match fields
    if criteria.source:
        conditions.append(
            {"source": {"$regex": f"^{re.escape(criteria.source)}$", "$options": "i"}}
        )

    if criteria.job_type:
        conditions.append(
            {"job_type": {"$regex": f"^{re.escape(criteria.job_type)}$", "$options": "i"}}
        )

    if criteria.search_term:
        conditions.append(
            {"search_term": {"$regex": f"^{re.escape(criteria.search_term)}$", "$options": "i"}}
        )

    # Case-insensitive substring match fields
    if criteria.location:
        conditions.append(
            {"location": {"$regex": re.escape(criteria.location), "$options": "i"}}
        )

    if criteria.company:
        conditions.append(
            {"company": {"$regex": re.escape(criteria.company), "$options": "i"}}
        )

    # Keyword: substring in title OR description
    if criteria.keyword:
        escaped_keyword = re.escape(criteria.keyword)
        conditions.append(
            {
                "$or": [
                    {"title": {"$regex": escaped_keyword, "$options": "i"}},
                    {"description": {"$regex": escaped_keyword, "$options": "i"}},
                ]
            }
        )

    # Date range: inclusive $gte/$lte on date_posted
    if criteria.date_from or criteria.date_to:
        date_condition: dict = {}
        if criteria.date_from:
            date_condition["$gte"] = criteria.date_from
        if criteria.date_to:
            date_condition["$lte"] = criteria.date_to
        conditions.append({"date_posted": date_condition})

    # Combine with AND logic
    if not conditions:
        return {}

    if len(conditions) == 1:
        return conditions[0]

    return {"$and": conditions}
