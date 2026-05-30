"""Watchlist endpoints for JobCopilot API.

Provides CRUD operations for the company watchlist.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.database.repository import JobsRepository
from app.models.schemas import AtsGroupResponse, WatchlistEntry, WatchlistRequest, WatchlistTierUpdate

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_TIERS = ("tier1", "tier2", "tier3")


@router.get("/watchlist")
def get_watchlist() -> list[WatchlistEntry]:
    """List all watchlist companies with ATS platform info and tier."""
    try:
        repo = JobsRepository()
        entries = repo.get_watchlist()
        return [WatchlistEntry(**entry) for entry in entries]
    except Exception as e:
        logger.error("Error fetching watchlist: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch watchlist")


@router.post("/watchlist", status_code=201)
def add_to_watchlist(request: WatchlistRequest) -> dict:
    """Add a company to the watchlist.

    Validates max 50 entries and max 100 characters per name.
    Accepts optional ats_platform field. Tier defaults to "tier3".
    """
    try:
        repo = JobsRepository()
        success = repo.add_to_watchlist(
            request.company_name, ats_platform=request.ats_platform
        )
        if not success:
            raise HTTPException(
                status_code=409,
                detail="Company already in watchlist or watchlist limit reached (max 50 entries)",
            )
        return {"message": f"Added '{request.company_name}' to watchlist"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error adding to watchlist: %s", e)
        raise HTTPException(status_code=500, detail="Failed to add to watchlist")


@router.get("/watchlist/ats-info")
def get_watchlist_ats_info() -> list[AtsGroupResponse]:
    """Return watchlist companies grouped by ATS platform."""
    try:
        repo = JobsRepository()
        groups = repo.get_watchlist_grouped_by_ats()
        return [AtsGroupResponse(**group) for group in groups]
    except Exception as e:
        logger.error("Error fetching watchlist ATS info: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch watchlist ATS info")


@router.patch("/watchlist/{company}")
def update_watchlist_tier(company: str, request: WatchlistTierUpdate) -> dict:
    """Update the tier of a watchlist company.

    Validates tier value to only allow tier1, tier2, tier3.
    """
    if request.tier not in VALID_TIERS:
        raise HTTPException(
            status_code=422,
            detail="Tier must be one of: tier1, tier2, tier3",
        )

    try:
        repo = JobsRepository()
        updated = repo.update_watchlist_tier(company, request.tier)
        if not updated:
            raise HTTPException(status_code=404, detail="Company not found in watchlist")
        return {"message": f"Updated tier for '{company}' to '{request.tier}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating watchlist tier: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update watchlist tier")


@router.delete("/watchlist/{company}")
def remove_from_watchlist(company: str) -> dict:
    """Remove a company from the watchlist."""
    try:
        repo = JobsRepository()
        removed = repo.remove_from_watchlist(company)
        if not removed:
            raise HTTPException(status_code=404, detail="Company not found in watchlist")
        return {"message": f"Removed '{company}' from watchlist"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error removing from watchlist: %s", e)
        raise HTTPException(status_code=500, detail="Failed to remove from watchlist")
