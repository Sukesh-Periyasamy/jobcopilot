"""Export endpoints for JobCopilot API.

Provides CSV and XLSX export of filtered job listings
with streaming responses for efficient downloads.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.database.repository import JobsRepository
from app.models.job import FilterCriteria
from app.services.export_service import export_csv, export_xlsx

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/export/csv")
def export_jobs_csv(
    source: Optional[str] = Query(None, description="Filter by source"),
    location: Optional[str] = Query(None, description="Filter by location"),
    company: Optional[str] = Query(None, description="Filter by company"),
    keyword: Optional[str] = Query(None, description="Filter by keyword"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    search_term: Optional[str] = Query(None, description="Filter by search term"),
    source_type: Optional[str] = Query(None, description="Filter by source type (jobspy or jobhive)"),
    source_platform: Optional[str] = Query(None, description="Filter by source platform"),
) -> StreamingResponse:
    """Export filtered jobs as CSV download."""
    try:
        repo = JobsRepository()
        filters = FilterCriteria(
            source=source,
            location=location,
            company=company,
            keyword=keyword,
            job_type=job_type,
            date_from=date_from,
            date_to=date_to,
            search_term=search_term,
            source_type=source_type,
            source_platform=source_platform,
        )
        jobs = repo.get_export_jobs(filters)
        buffer, was_truncated = export_csv(jobs)

        filename = f"jobs_export_{date.today().isoformat()}.csv"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
        if was_truncated:
            headers["X-Export-Truncated"] = "true"

        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers=headers,
        )
    except Exception as e:
        logger.error("Error exporting jobs as CSV: %s", e)
        raise HTTPException(status_code=500, detail="Failed to export jobs as CSV")


@router.get("/export/xlsx")
def export_jobs_xlsx(
    source: Optional[str] = Query(None, description="Filter by source"),
    location: Optional[str] = Query(None, description="Filter by location"),
    company: Optional[str] = Query(None, description="Filter by company"),
    keyword: Optional[str] = Query(None, description="Filter by keyword"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    search_term: Optional[str] = Query(None, description="Filter by search term"),
    source_type: Optional[str] = Query(None, description="Filter by source type (jobspy or jobhive)"),
    source_platform: Optional[str] = Query(None, description="Filter by source platform"),
) -> StreamingResponse:
    """Export filtered jobs as XLSX download."""
    try:
        repo = JobsRepository()
        filters = FilterCriteria(
            source=source,
            location=location,
            company=company,
            keyword=keyword,
            job_type=job_type,
            date_from=date_from,
            date_to=date_to,
            search_term=search_term,
            source_type=source_type,
            source_platform=source_platform,
        )
        jobs = repo.get_export_jobs(filters)
        buffer, was_truncated = export_xlsx(jobs)

        filename = f"jobs_export_{date.today().isoformat()}.xlsx"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
        if was_truncated:
            headers["X-Export-Truncated"] = "true"

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers,
        )
    except Exception as e:
        logger.error("Error exporting jobs as XLSX: %s", e)
        raise HTTPException(status_code=500, detail="Failed to export jobs as XLSX")
