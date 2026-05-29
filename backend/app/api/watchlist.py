"""Watchlist endpoints for JobCopilot API.

Provides CRUD operations for the company watchlist.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.database.repository import JobsRepository
from app.models.schemas import WatchlistRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/watchlist")
def get_watchlist() -> list[str]:
    """List all watchlist companies."""
    try:
        repo = JobsRepository()
        return repo.get_watchlist()
    except Exception as e:
        logger.error("Error fetching watchlist: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch watchlist")


@router.post("/watchlist", status_code=201)
def add_to_watchlist(request: WatchlistRequest) -> dict:
    """Add a company to the watchlist.

    Validates max 50 entries and max 100 characters per name.
    """
    try:
        repo = JobsRepository()
        success = repo.add_to_watchlist(request.company_name)
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
