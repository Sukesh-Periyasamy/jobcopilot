"""Saved jobs endpoints for JobCopilot API.

Provides operations for saving and managing bookmarked jobs.
"""

from __future__ import annotations

import logging
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException

from app.database.repository import JobsRepository
from app.models.schemas import SaveJobRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/save-job", status_code=201)
def save_job(request: SaveJobRequest) -> dict:
    """Save a job to the saved_jobs collection."""
    try:
        repo = JobsRepository()
        job_data = {
            "job_url": request.job_url,
            "title": request.title,
            "company": request.company,
            "location": request.location,
            "source": request.source,
            "date_posted": request.date_posted,
        }
        success = repo.save_job(job_data)
        if not success:
            raise HTTPException(status_code=409, detail="Job already saved")
        return {"message": "Job saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error saving job: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save job")


@router.delete("/save-job/{job_url:path}")
def remove_saved_job(job_url: str) -> dict:
    """Remove a job from saved jobs.

    The job_url path parameter should be URL-encoded.
    """
    try:
        decoded_url = unquote(job_url)
        repo = JobsRepository()
        removed = repo.remove_saved_job(decoded_url)
        if not removed:
            raise HTTPException(status_code=404, detail="Saved job not found")
        return {"message": "Saved job removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error removing saved job: %s", e)
        raise HTTPException(status_code=500, detail="Failed to remove saved job")


@router.get("/saved-jobs")
def get_saved_jobs() -> list[dict]:
    """List all saved jobs."""
    try:
        repo = JobsRepository()
        return repo.get_saved_jobs()
    except Exception as e:
        logger.error("Error fetching saved jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch saved jobs")
