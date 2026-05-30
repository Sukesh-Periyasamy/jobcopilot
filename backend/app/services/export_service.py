"""Export service for generating CSV and XLSX files from job records.

Generates files in-memory using BytesIO buffers (no disk I/O)
to remain compatible with Render's ephemeral filesystem.
"""

from __future__ import annotations

import csv
import io
from io import BytesIO

from openpyxl import Workbook

from app.models.job import JobRecord

EXPORT_COLUMNS = [
    "title",
    "company",
    "location",
    "source",
    "source_type",
    "source_platform",
    "job_url",
    "description",
    "job_type",
    "salary",
    "date_posted",
    "search_term",
    "created_at",
]

MAX_EXPORT_RECORDS = 10000


def _get_row(job: JobRecord) -> list[str]:
    """Extract a row of values from a JobRecord in EXPORT_COLUMNS order."""
    return [getattr(job, col, "") for col in EXPORT_COLUMNS]


def export_csv(jobs: list[JobRecord]) -> tuple[BytesIO, bool]:
    """Generate CSV from job records. Returns (buffer, was_truncated).

    If len(jobs) > MAX_EXPORT_RECORDS, truncate to MAX_EXPORT_RECORDS
    and set was_truncated=True.
    If jobs is empty, return a file with only the header row.
    The buffer is seeked to position 0 before returning.
    """
    was_truncated = len(jobs) > MAX_EXPORT_RECORDS
    records = jobs[:MAX_EXPORT_RECORDS]

    buffer = BytesIO()
    text_buffer = io.StringIO()
    writer = csv.writer(text_buffer)
    writer.writerow(EXPORT_COLUMNS)

    for job in records:
        writer.writerow(_get_row(job))

    buffer.write(text_buffer.getvalue().encode("utf-8"))
    buffer.seek(0)
    return buffer, was_truncated


def export_xlsx(jobs: list[JobRecord]) -> tuple[BytesIO, bool]:
    """Generate XLSX from job records. Returns (buffer, was_truncated).

    Uses openpyxl to generate the Excel file in-memory.
    If len(jobs) > MAX_EXPORT_RECORDS, truncate to MAX_EXPORT_RECORDS
    and set was_truncated=True.
    If jobs is empty, return a file with only the header row.
    The buffer is seeked to position 0 before returning.
    """
    was_truncated = len(jobs) > MAX_EXPORT_RECORDS
    records = jobs[:MAX_EXPORT_RECORDS]

    wb = Workbook()
    ws = wb.active
    ws.title = "Jobs"

    # Write header row
    ws.append(EXPORT_COLUMNS)

    # Write data rows
    for job in records:
        ws.append(_get_row(job))

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer, was_truncated
