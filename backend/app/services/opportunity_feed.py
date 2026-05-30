"""Opportunity Feed Service for Career Opportunity Radar.

Aggregates categorized top opportunities into a single response with six
categories: top companies, new companies, remote jobs, internships,
research roles, and healthcare roles. Each category is computed independently
and limited to a maximum of 10 entries.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

from app.database.connection import get_database
from app.services.constants import (
    COLLECTIONS,
    INTERNSHIP_KEYWORDS,
    RESEARCH_INSTITUTIONS,
)

logger = logging.getLogger(__name__)


class OpportunityFeedService:
    """Aggregates categorized top opportunities into a single feed response.

    Stateless service that queries the jobs collection using MongoDB
    aggregation pipelines and regex queries to produce six independent
    opportunity categories.
    """

    def get_feed(self) -> dict:
        """Return a dict with six opportunity categories.

        Each category is computed independently. If one category fails,
        it returns an empty list while others succeed.

        Returns:
            Dict with keys: top_companies, new_companies, remote_jobs,
            internships, research_roles, healthcare_roles.
        """
        feed = {}

        # Each category is independent — if one fails, return empty list
        try:
            feed["top_companies"] = self._get_top_companies()
        except Exception:
            logger.exception("Failed to compute top_companies")
            feed["top_companies"] = []

        try:
            feed["new_companies"] = self._get_new_companies()
        except Exception:
            logger.exception("Failed to compute new_companies")
            feed["new_companies"] = []

        try:
            feed["remote_jobs"] = self._get_remote_jobs()
        except Exception:
            logger.exception("Failed to compute remote_jobs")
            feed["remote_jobs"] = []

        try:
            feed["internships"] = self._get_internships()
        except Exception:
            logger.exception("Failed to compute internships")
            feed["internships"] = []

        try:
            feed["research_roles"] = self._get_research_roles()
        except Exception:
            logger.exception("Failed to compute research_roles")
            feed["research_roles"] = []

        try:
            feed["healthcare_roles"] = self._get_healthcare_roles()
        except Exception:
            logger.exception("Failed to compute healthcare_roles")
            feed["healthcare_roles"] = []

        return feed

    def _get_top_companies(self) -> list[dict]:
        """Aggregate companies by job count, return top 10.

        Uses MongoDB aggregation pipeline with $group by company,
        $sort by count descending, $limit 10.

        Returns:
            List of dicts with "company" and "job_count" keys.
        """
        db = get_database()
        jobs_collection = db["jobs"]

        pipeline = [
            {"$group": {"_id": "$company", "job_count": {"$sum": 1}}},
            {"$sort": {"job_count": -1}},
            {"$limit": 10},
        ]

        results = list(jobs_collection.aggregate(pipeline))
        return [
            {"company": doc["_id"], "job_count": doc["job_count"]}
            for doc in results
        ]

    def _get_new_companies(self) -> list[dict]:
        """Find companies first seen in last 7 days.

        Uses aggregation to group by company with $min date_posted,
        then filters where the earliest date_posted falls within
        the last 7 days.

        Returns:
            List of dicts with "company" and "first_seen" keys.
        """
        db = get_database()
        jobs_collection = db["jobs"]

        seven_days_ago = (
            datetime.now(timezone.utc) - timedelta(days=7)
        ).strftime("%Y-%m-%d")

        pipeline = [
            {"$group": {"_id": "$company", "first_seen": {"$min": "$date_posted"}}},
            {"$match": {"first_seen": {"$gte": seven_days_ago}}},
            {"$sort": {"first_seen": -1}},
            {"$limit": 10},
        ]

        results = list(jobs_collection.aggregate(pipeline))
        return [
            {"company": doc["_id"], "first_seen": doc["first_seen"]}
            for doc in results
        ]

    def _get_remote_jobs(self) -> list[dict]:
        """Query jobs with 'remote' in location field (case-insensitive).

        Returns:
            List of job dicts (excluding _id), sorted by date_posted
            descending, limited to 10.
        """
        db = get_database()
        jobs_collection = db["jobs"]

        query = {"location": {"$regex": "remote", "$options": "i"}}
        cursor = (
            jobs_collection.find(query, {"_id": 0})
            .sort("date_posted", -1)
            .limit(10)
        )

        return list(cursor)

    def _get_internships(self) -> list[dict]:
        """Query jobs matching internship keywords in title.

        Builds a case-insensitive regex $or query matching any
        INTERNSHIP_KEYWORD in the title field.

        Returns:
            List of job dicts (excluding _id), sorted by date_posted
            descending, limited to 10.
        """
        db = get_database()
        jobs_collection = db["jobs"]

        conditions = [
            {"title": {"$regex": re.escape(kw), "$options": "i"}}
            for kw in INTERNSHIP_KEYWORDS
        ]
        query = {"$or": conditions}

        cursor = (
            jobs_collection.find(query, {"_id": 0})
            .sort("date_posted", -1)
            .limit(10)
        )

        return list(cursor)

    def _get_research_roles(self) -> list[dict]:
        """Query jobs from research institutions.

        Builds a case-insensitive regex $or query matching any
        RESEARCH_INSTITUTION name in the company or description fields.

        Returns:
            List of job dicts (excluding _id), sorted by date_posted
            descending, limited to 10.
        """
        db = get_database()
        jobs_collection = db["jobs"]

        conditions = []
        for inst in RESEARCH_INSTITUTIONS:
            escaped = re.escape(inst)
            conditions.append({"company": {"$regex": escaped, "$options": "i"}})
            conditions.append({"description": {"$regex": escaped, "$options": "i"}})

        query = {"$or": conditions}

        cursor = (
            jobs_collection.find(query, {"_id": 0})
            .sort("date_posted", -1)
            .limit(10)
        )

        return list(cursor)

    def _get_healthcare_roles(self) -> list[dict]:
        """Query jobs matching healthcare/medtech collection keywords.

        Combines keywords from "Healthcare Technology" and "Medical Technology"
        collections and builds a case-insensitive regex $or query matching
        any keyword in title or description.

        Returns:
            List of job dicts (excluding _id), sorted by date_posted
            descending, limited to 10.
        """
        db = get_database()
        jobs_collection = db["jobs"]

        # Combine keywords from Healthcare Technology and Medical Technology collections
        healthcare_keywords: list[str] = []
        for collection_def in COLLECTIONS:
            if collection_def.name in ("Healthcare Technology", "Medical Technology"):
                healthcare_keywords.extend(collection_def.keywords)

        if not healthcare_keywords:
            return []

        conditions = []
        for keyword in healthcare_keywords:
            escaped = re.escape(keyword)
            conditions.append({"title": {"$regex": escaped, "$options": "i"}})
            conditions.append({"description": {"$regex": escaped, "$options": "i"}})

        query = {"$or": conditions}

        cursor = (
            jobs_collection.find(query, {"_id": 0})
            .sort("date_posted", -1)
            .limit(10)
        )

        return list(cursor)
