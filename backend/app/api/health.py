"""Health check endpoint for JobCopilot API."""

from fastapi import APIRouter

router = APIRouter()


@router.api_route("/health", methods=["GET", "HEAD"])
def health_check() -> dict:
    """Return a simple health check response."""
    return {"status": "ok"}
