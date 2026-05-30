"""Regional Radar endpoints for South India Fresher jobs.

Provides location-based job filtering for Tamil Nadu, Bangalore,
with fresher scoring and district-level granularity.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.services.regional_radar import RegionalRadarService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/regional/tamilnadu")
def get_tamil_nadu() -> dict:
    """Return jobs in Tamil Nadu with fresher scoring and district breakdown."""
    try:
        service = RegionalRadarService()
        return service.get_tamil_nadu()
    except Exception as e:
        logger.error("Error fetching Tamil Nadu jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch regional jobs")


@router.get("/regional/bangalore")
def get_bangalore() -> dict:
    """Return jobs in Bangalore/Karnataka with fresher scoring."""
    try:
        service = RegionalRadarService()
        return service.get_bangalore()
    except Exception as e:
        logger.error("Error fetching Bangalore jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch regional jobs")


@router.get("/regional/freshers")
def get_freshers() -> dict:
    """Return fresher-friendly jobs across South India."""
    try:
        service = RegionalRadarService()
        return service.get_freshers()
    except Exception as e:
        logger.error("Error fetching fresher jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch fresher jobs")


@router.get("/regional/research")
def get_regional_research() -> dict:
    """Return research positions in South India."""
    try:
        service = RegionalRadarService()
        return service.get_research()
    except Exception as e:
        logger.error("Error fetching research jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch research jobs")


@router.get("/regional/internships")
def get_regional_internships() -> dict:
    """Return internships in South India."""
    try:
        service = RegionalRadarService()
        return service.get_internships()
    except Exception as e:
        logger.error("Error fetching internships: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch internships")


@router.get("/regional/core-engineering")
def get_core_engineering() -> dict:
    """Return core engineering jobs in South India."""
    try:
        service = RegionalRadarService()
        return service.get_core_engineering()
    except Exception as e:
        logger.error("Error fetching core engineering jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch engineering jobs")


@router.get("/regional/district/{district}")
def get_district(district: str) -> dict:
    """Return jobs in a specific district/city."""
    try:
        service = RegionalRadarService()
        return service.get_district(district)
    except Exception as e:
        logger.error("Error fetching district jobs for '%s': %s", district, e)
        raise HTTPException(status_code=500, detail="Failed to fetch district jobs")
