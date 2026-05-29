"""Health check endpoint for JobCopilot API."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    """Return a simple health check response."""
    return {"status": "ok"}
