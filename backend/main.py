"""FastAPI application entry point for JobCopilot Engine.

Provides the REST API server and CLI interface for running the
scraper or serving the API.

CLI usage:
    python main.py serve    → Start FastAPI with uvicorn on 0.0.0.0:8000
    python main.py scrape   → Run a single scrape cycle, exit 0/1
    python main.py          → Show help, exit 0
    python main.py <other>  → Show error + help, exit 2
"""

from __future__ import annotations

import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- FastAPI Application ---

app = FastAPI(title="JobCopilot API", version="1.0.0")

# CORS middleware for GitHub Pages frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register API Routers ---

from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.watchlist import router as watchlist_router
from app.api.saved import router as saved_router
from app.api.applied import router as applied_router
from app.api.stats import router as stats_router
from app.api.export import router as export_router
from app.api.collections import router as collections_router
from app.api.research import router as research_router
from app.api.internships import router as internships_router
from app.api.opportunities import router as opportunities_router
from app.api.analytics import router as analytics_router
from app.api.preferences import router as preferences_router
from app.api.career_radar import router as career_radar_router

app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(watchlist_router)
app.include_router(saved_router)
app.include_router(applied_router)
app.include_router(stats_router)
app.include_router(export_router)
app.include_router(collections_router)
app.include_router(research_router)
app.include_router(internships_router)
app.include_router(opportunities_router)
app.include_router(analytics_router)
app.include_router(preferences_router)
app.include_router(career_radar_router)


# --- CLI ---

HELP_TEXT = """\
JobCopilot CLI

Usage: python main.py <command>

Commands:
  serve   Start the FastAPI server (uvicorn on 0.0.0.0:8000)
  scrape  Run a single scrape cycle and exit (0=success, 1=failure)
"""

VALID_COMMANDS = {"serve", "scrape"}


def _show_help() -> None:
    """Print help text to stdout."""
    print(HELP_TEXT)


def main() -> None:
    """CLI entry point.

    - No args        → show help, exit 0
    - 'serve'        → start uvicorn
    - 'scrape'       → run daily_scraper.main(), exit 0 on success, 1 on failure
    - invalid arg    → error message + help, exit 2
    """
    args = sys.argv[1:]

    # No arguments → help, exit 0
    if not args:
        _show_help()
        sys.exit(0)

    command = args[0]

    if command == "serve":
        import os

        import uvicorn

        port = int(os.environ.get("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)

    elif command == "scrape":
        import daily_scraper

        try:
            daily_scraper.main()
            sys.exit(0)
        except SystemExit as exc:
            # daily_scraper.main() calls sys.exit(1) on failure
            sys.exit(exc.code if exc.code is not None else 0)

    else:
        print(f"Error: '{command}' is not a valid command.", file=sys.stderr)
        _show_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
