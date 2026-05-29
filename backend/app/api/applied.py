"""Applied jobs endpoints for JobCopilot API.

Provides operations for tracking job applications and their statuses.
"""

from __future__ import annotations

import logging
from urllib.parse import unquote

from fastapi import APIRouter, Body, HTTPException

from app.database.repository import JobsRepository
from app.models.schemas import ApplyJobRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/apply-job", status_code=201)
def apply_job(request: ApplyJobRequest) -> dict:
    """Mark a job as applied with an initial status.

    Default status is "Interested".
    """
    try:
        repo = JobsRepository()
        job_data = {
            "job_url": request.job_url,
            "title": request.title,
            "company": request.company,
            "location": request.location,
        }
        repo.add_applied_job(job_data, status=request.status)
        return {"message": "Job application recorded", "status": request.status}
    except Exception as e:
        logger.error("Error recording job application: %s", e)
        raise HTTPException(status_code=500, detail="Failed to record job application")


@router.patch("/apply-job/{job_url:path}")
def update_application_status(
    job_url: str,
    status: str = Body(..., embed=True),
) -> dict:
    """Update the application status for a job.

    The job_url path parameter should be URL-encoded.
    """
    try:
        decoded_url = unquote(job_url)
        repo = JobsRepository()
        repo.update_application_status(decoded_url, status)
        return {"message": "Application status updated", "status": status}
    except Exception as e:
        logger.error("Error updating application status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update application status")


@router.get("/applied-jobs")
def get_applied_jobs() -> list[dict]:
    """List all applied jobs."""
    try:
        repo = JobsRepository()
        return repo.get_applied_jobs()
    except Exception as e:
        logger.error("Error fetching applied jobs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch applied jobs")
