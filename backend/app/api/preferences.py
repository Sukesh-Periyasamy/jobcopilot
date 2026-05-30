"""Preferences endpoints for JobCopilot API.

Provides endpoints for pinning collections and companies,
and a personal dashboard aggregating relevant opportunities.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.connection import get_database
from app.database.repository import JobsRepository
from app.models.schemas import JobResponse, PersonalDashboardResponse
from app.services.collection_engine import CollectionEngine
from app.services.research_tracker import ResearchTracker

logger = logging.getLogger(__name__)

router = APIRouter()


class PinRequest(BaseModel):
    """Request model for pinning a collection or company."""

    name: str


@router.post("/preferences/pinned-collections", status_code=201)
def pin_collection(request: PinRequest) -> dict:
    """Pin a collection. Maximum 5 pinned collections allowed.

    Returns 409 if the limit is exceeded.
    """
    try:
        repo = JobsRepository()
        success = repo.add_pinned_collection(request.name)
        if not success:
            raise HTTPException(
                status_code=409,
                detail="Maximum 5 pinned collections allowed",
            )
        return {"message": f"Pinned collection '{request.name}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error pinning collection: %s", e)
        raise HTTPException(status_code=500, detail="Failed to pin collection")


@router.post("/preferences/pinned-companies", status_code=201)
def pin_company(request: PinRequest) -> dict:
    """Pin a company. Maximum 10 pinned companies allowed.

    Returns 409 if the limit is exceeded.
    """
    try:
        repo = JobsRepository()
        success = repo.add_pinned_company(request.name)
        if not success:
            raise HTTPException(
                status_code=409,
                detail="Maximum 10 pinned companies allowed",
            )
        return {"message": f"Pinned company '{request.name}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error pinning company: %s", e)
        raise HTTPException(status_code=500, detail="Failed to pin company")


@router.get("/preferences/dashboard")
def get_dashboard() -> PersonalDashboardResponse:
    """Return personal dashboard data with pinned company jobs,
    pinned collection jobs, and new research opportunities from the last 7 days.
    """
    try:
        db = get_database()
        repo = JobsRepository()
        jobs_collection = db["jobs"]

        # Calculate 7-day cutoff date
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

        # Get pinned companies and their jobs
        pinned_companies = repo.get_pinned_companies()
        pinned_company_jobs: list[dict] = []
        if pinned_companies:
            company_conditions = [
                {"company": {"$regex": f"^{re.escape(c)}$", "$options": "i"}}
                for c in pinned_companies
            ]
            company_query = {
                "$and": [
                    {"$or": company_conditions},
                    {"date_posted": {"$gte": seven_days_ago}},
                ]
            }
            cursor = jobs_collection.find(company_query, {"_id": 0}).sort("date_posted", -1)
            pinned_company_jobs = list(cursor)

        # Get pinned collections and their jobs
        pinned_collections = repo.get_pinned_collections()
        pinned_collection_jobs: list[dict] = []
        if pinned_collections:
            collection_engine = CollectionEngine(db)
            keyword_conditions = []
            for coll_name in pinned_collections:
                coll_def = collection_engine._find_collection_def(coll_name)
                if coll_def:
                    for keyword in coll_def.keywords:
                        escaped = re.escape(keyword)
                        keyword_conditions.append(
                            {"title": {"$regex": escaped, "$options": "i"}}
                        )
                        keyword_conditions.append(
                            {"description": {"$regex": escaped, "$options": "i"}}
                        )

            if keyword_conditions:
                collection_query = {
                    "$and": [
                        {"$or": keyword_conditions},
                        {"date_posted": {"$gte": seven_days_ago}},
                    ]
                }
                cursor = jobs_collection.find(collection_query, {"_id": 0}).sort("date_posted", -1)
                pinned_collection_jobs = list(cursor)

        # Get recent research opportunities (last 7 days)
        research_tracker = ResearchTracker()
        all_research = research_tracker.get_recent_research(limit=100)
        new_research = [
            job for job in all_research
            if job.get("date_posted", "") >= seven_days_ago
        ]

        return PersonalDashboardResponse(
            pinned_company_jobs=[_doc_to_job_response(doc) for doc in pinned_company_jobs],
            pinned_collection_jobs=[_doc_to_job_response(doc) for doc in pinned_collection_jobs],
            new_research_opportunities=[_doc_to_job_response(doc) for doc in new_research],
        )
    except Exception as e:
        logger.error("Error fetching dashboard: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")


@router.delete("/preferences/pinned-collections/{name}")
def unpin_collection(name: str) -> dict:
    """Unpin a collection. Returns 404 if not found."""
    try:
        repo = JobsRepository()
        removed = repo.remove_pinned_collection(name)
        if not removed:
            raise HTTPException(status_code=404, detail="Collection not found in pinned list")
        return {"message": f"Unpinned collection '{name}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error unpinning collection: %s", e)
        raise HTTPException(status_code=500, detail="Failed to unpin collection")


@router.delete("/preferences/pinned-companies/{name}")
def unpin_company(name: str) -> dict:
    """Unpin a company. Returns 404 if not found."""
    try:
        repo = JobsRepository()
        removed = repo.remove_pinned_company(name)
        if not removed:
            raise HTTPException(status_code=404, detail="Company not found in pinned list")
        return {"message": f"Unpinned company '{name}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error unpinning company: %s", e)
        raise HTTPException(status_code=500, detail="Failed to unpin company")


def _doc_to_job_response(doc: dict) -> JobResponse:
    """Convert a MongoDB document to a JobResponse model.

    Handles backward compatibility for legacy documents missing
    source_type and source_platform fields.

    Args:
        doc: MongoDB document dictionary.

    Returns:
        JobResponse instance.
    """
    source_type = doc.get("source_type", "")
    if not source_type:
        source_type = "jobspy"

    source_platform = doc.get("source_platform", "")
    if not source_platform:
        source_platform = doc.get("source", "").strip().lower()

    return JobResponse(
        title=doc.get("title", ""),
        company=doc.get("company", ""),
        location=doc.get("location", ""),
        source=doc.get("source", ""),
        source_type=source_type,
        source_platform=source_platform,
        job_url=doc.get("job_url", ""),
        description=doc.get("description", ""),
        job_type=doc.get("job_type", ""),
        salary=doc.get("salary", ""),
        date_posted=doc.get("date_posted", ""),
        search_term=doc.get("search_term", ""),
        created_at=doc.get("created_at", ""),
        updated_at=doc.get("updated_at", ""),
    )
