"""Configuration loader for JobCopilot Engine.

Loads settings from .env file (via python-dotenv) with fallback to
system environment variables. Validates required fields and formats.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Default values per requirements 9.4
DEFAULT_SEARCH_TERMS = (
    "Biomedical Engineer,Medical Device Engineer,Research Engineer,"
    "Research Associate,Healthcare Technology,Healthcare AI,"
    "Signal Processing Engineer,Embedded Systems Engineer,IoT Engineer,"
    "Python Developer,Backend Developer,R&D Engineer,"
    "Clinical Data Analyst,Biomedical Research,Medical Technology,"
    "Research Scientist"
)

DEFAULT_LOCATIONS = (
    "India,Remote,Bangalore,Hyderabad,Chennai,Pune,"
    "Mumbai,Delhi,Noida,Gurugram,Ahmedabad,Kolkata"
)

DEFAULT_JOB_SOURCES = "linkedin,indeed,naukri,google"

_SCHEDULE_TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


@dataclass
class Settings:
    """Application configuration loaded from environment."""

    mongodb_uri: str
    database_name: str = "jobcopilot"
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    search_terms: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    job_sources: list[str] = field(default_factory=list)
    schedule_time: str = "08:00"

    @classmethod
    def load(cls) -> Settings:
        """Load configuration from .env file and environment variables.

        The .env file is loaded first (if it exists), then any values
        already present in the system environment take precedence only
        if they were not in the .env file (python-dotenv does NOT
        override existing env vars by default, but we load .env first
        so its values are available via os.environ.get).

        Raises:
            ValueError: If MONGODB_URI is missing or schedule_time is invalid.
        """
        # Load .env file if present; does not override existing env vars
        load_dotenv()

        # Required: MONGODB_URI
        mongodb_uri = os.environ.get("MONGODB_URI", "").strip()
        if not mongodb_uri:
            raise ValueError(
                "Required environment variable MONGODB_URI is not set. "
                "Please provide a MongoDB connection string via .env file "
                "or system environment variable."
            )

        # Optional with defaults
        database_name = os.environ.get("DATABASE_NAME", "").strip() or "jobcopilot"

        telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or None
        telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip() or None

        # Comma-separated lists with defaults
        search_terms = _parse_list(
            os.environ.get("SEARCH_TERMS", ""), DEFAULT_SEARCH_TERMS
        )
        locations = _parse_list(
            os.environ.get("LOCATIONS", ""), DEFAULT_LOCATIONS
        )
        job_sources = _parse_list(
            os.environ.get("JOB_SOURCES", ""), DEFAULT_JOB_SOURCES
        )

        # Schedule time with validation
        schedule_time = os.environ.get("SCHEDULE_TIME", "").strip() or "08:00"
        _validate_schedule_time(schedule_time)

        return cls(
            mongodb_uri=mongodb_uri,
            database_name=database_name,
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            search_terms=search_terms,
            locations=locations,
            job_sources=job_sources,
            schedule_time=schedule_time,
        )


def _parse_list(value: str, default: str) -> list[str]:
    """Parse a comma-separated string into a list of stripped, non-empty strings.

    Falls back to the default string if value is empty or whitespace-only.
    """
    raw = value.strip() if value else ""
    if not raw:
        raw = default
    return [item.strip() for item in raw.split(",") if item.strip()]


def _validate_schedule_time(time_str: str) -> None:
    """Validate that time_str matches HH:MM 24-hour format (00:00–23:59).

    Raises:
        ValueError: If the format is invalid.
    """
    if not _SCHEDULE_TIME_PATTERN.match(time_str):
        raise ValueError(
            f"Invalid schedule_time '{time_str}'. "
            f"Must be in HH:MM 24-hour format (00:00–23:59)."
        )
