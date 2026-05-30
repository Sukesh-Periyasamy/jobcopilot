"""Analytics Engine for Career Opportunity Radar.

Computes aggregate statistics from the jobs collection using MongoDB
aggregation pipelines ($group, $sort, $limit). Each metric computation
is independent — if one fails, others still return. Failed metrics
return empty lists/dicts with the error logged.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta

from pymongo.database import Database

from app.database.connection import get_database
from app.services.collection_engine import CollectionEngine
from app.services.constants import INTERNSHIP_KEYWORDS, RESEARCH_INSTITUTIONS

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Computes aggregate analytics metrics from the jobs collection.

    Stateless class that uses MongoDB aggregation pipelines for all
    computations. Each metric is computed independently so that a
    failure in one does not affect the others.
    """

    def __init__(self, db: Database | None = None) -> None:
        """Initialize with a MongoDB database reference.

        Args:
            db: A pymongo Database instance. If None, uses get_database().
        """
        self._db = db or get_database()
        self._jobs = self._db["jobs"]

    def compute_analytics(self) -> dict:
        """Return all analytics metrics in a single dict.

        Each metric is computed independently. If any metric computation
        fails, it returns an empty list or dict and the error is logged.

        Returns:
            Dict with keys: jobs_per_day, jobs_per_company, jobs_per_source,
            jobs_per_platform, jobs_per_location, jobs_per_collection,
            top_hiring_companies, top_locations, top_ats_platforms,
            internship_vs_fulltime, research_vs_industry.
        """
        results = {}

        # List-type metrics
        list_metrics = {
            "jobs_per_day": self._jobs_per_day,
            "jobs_per_company": self._jobs_per_company,
            "jobs_per_source": self._jobs_per_source,
            "jobs_per_platform": self._jobs_per_platform,
            "jobs_per_location": self._jobs_per_location,
            "jobs_per_collection": self._jobs_per_collection,
        }

        for key, method in list_metrics.items():
            try:
                results[key] = method()
            except Exception:
                logger.exception("Failed to compute metric: %s", key)
                results[key] = []

        # Derived top-N metrics from already-computed data
        try:
            results["top_hiring_companies"] = results["jobs_per_company"][:10]
        except Exception:
            logger.exception("Failed to compute metric: top_hiring_companies")
            results["top_hiring_companies"] = []

        try:
            results["top_locations"] = results["jobs_per_location"][:10]
        except Exception:
            logger.exception("Failed to compute metric: top_locations")
            results["top_locations"] = []

        try:
            results["top_ats_platforms"] = results["jobs_per_platform"]
        except Exception:
            logger.exception("Failed to compute metric: top_ats_platforms")
            results["top_ats_platforms"] = []

        # Dict-type metrics
        dict_metrics = {
            "internship_vs_fulltime": self._internship_vs_fulltime,
            "research_vs_industry": self._research_vs_industry,
        }

        for key, method in dict_metrics.items():
            try:
                results[key] = method()
            except Exception:
                logger.exception("Failed to compute metric: %s", key)
                results[key] = {}

        return results

    def _jobs_per_day(self) -> list[dict]:
        """Aggregate job counts by date_posted for the last 30 days.

        Uses a MongoDB aggregation pipeline:
        - $match: date_posted >= 30 days ago
        - $group: by date_posted, count occurrences
        - $sort: by date ascending

        Returns:
            List of dicts with 'date' and 'count' keys.
        """
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        pipeline = [
            {"$match": {"date_posted": {"$gte": thirty_days_ago}}},
            {"$group": {"_id": "$date_posted", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]

        results = list(self._jobs.aggregate(pipeline))
        return [{"date": doc["_id"], "count": doc["count"]} for doc in results]

    def _jobs_per_company(self) -> list[dict]:
        """Aggregate top 20 companies by job count.

        Uses a MongoDB aggregation pipeline:
        - $group: by company, count occurrences
        - $sort: by count descending
        - $limit: 20

        Returns:
            List of dicts with 'company' and 'count' keys.
        """
        pipeline = [
            {"$group": {"_id": "$company", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20},
        ]

        results = list(self._jobs.aggregate(pipeline))
        return [{"company": doc["_id"], "count": doc["count"]} for doc in results]

    def _jobs_per_source(self) -> list[dict]:
        """Aggregate all sources by job count.

        Uses a MongoDB aggregation pipeline:
        - $group: by source, count occurrences
        - $sort: by count descending

        Returns:
            List of dicts with 'source' and 'count' keys.
        """
        pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]

        results = list(self._jobs.aggregate(pipeline))
        return [{"source": doc["_id"], "count": doc["count"]} for doc in results]

    def _jobs_per_platform(self) -> list[dict]:
        """Aggregate all ATS platforms by job count.

        Uses a MongoDB aggregation pipeline:
        - $group: by source_platform, count occurrences
        - $sort: by count descending

        Returns:
            List of dicts with 'platform' and 'count' keys.
        """
        pipeline = [
            {"$group": {"_id": "$source_platform", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]

        results = list(self._jobs.aggregate(pipeline))
        return [{"platform": doc["_id"], "count": doc["count"]} for doc in results]

    def _jobs_per_location(self) -> list[dict]:
        """Aggregate top 20 locations by job count.

        Uses a MongoDB aggregation pipeline:
        - $group: by location, count occurrences
        - $sort: by count descending
        - $limit: 20

        Returns:
            List of dicts with 'location' and 'count' keys.
        """
        pipeline = [
            {"$group": {"_id": "$location", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20},
        ]

        results = list(self._jobs.aggregate(pipeline))
        return [{"location": doc["_id"], "count": doc["count"]} for doc in results]

    def _jobs_per_collection(self) -> list[dict]:
        """Compute job count for each collection using CollectionEngine.

        Delegates to CollectionEngine.get_all_collections() which already
        returns a list of dicts with 'name' and 'job_count' keys.

        Returns:
            List of dicts with 'name' and 'job_count' keys.
        """
        engine = CollectionEngine(self._db)
        return engine.get_all_collections()

    def _internship_vs_fulltime(self) -> dict:
        """Count internship vs non-internship jobs.

        Counts jobs matching any INTERNSHIP_KEYWORD in the title field
        (case-insensitive). Full-time count is total jobs minus internship count.

        Returns:
            Dict with 'internship_count' and 'fulltime_count' keys.
        """
        # Build regex pattern matching any internship keyword in title
        conditions = []
        for keyword in INTERNSHIP_KEYWORDS:
            escaped = re.escape(keyword)
            conditions.append({"title": {"$regex": escaped, "$options": "i"}})

        internship_query = {"$or": conditions}
        internship_count = self._jobs.count_documents(internship_query)
        total_count = self._jobs.count_documents({})
        fulltime_count = total_count - internship_count

        return {
            "internship_count": internship_count,
            "fulltime_count": fulltime_count,
        }

    def _research_vs_industry(self) -> dict:
        """Count research institution vs other jobs.

        Counts jobs matching any RESEARCH_INSTITUTION name in the company
        or description fields (case-insensitive). Industry count is total
        jobs minus research count.

        Returns:
            Dict with 'research_count' and 'industry_count' keys.
        """
        # Build regex pattern matching any research institution in company or description
        conditions = []
        for institution in RESEARCH_INSTITUTIONS:
            escaped = re.escape(institution)
            conditions.append({"company": {"$regex": escaped, "$options": "i"}})
            conditions.append({"description": {"$regex": escaped, "$options": "i"}})

        research_query = {"$or": conditions}
        research_count = self._jobs.count_documents(research_query)
        total_count = self._jobs.count_documents({})
        industry_count = total_count - research_count

        return {
            "research_count": research_count,
            "industry_count": industry_count,
        }
