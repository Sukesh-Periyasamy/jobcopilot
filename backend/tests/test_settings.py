"""Unit tests for the Settings configuration loader."""

import os
from unittest.mock import patch

import pytest

from app.config.settings import Settings, _parse_list, _validate_schedule_time


class TestParseList:
    """Tests for the _parse_list helper."""

    def test_parses_comma_separated_values(self):
        result = _parse_list("a,b,c", "x,y")
        assert result == ["a", "b", "c"]

    def test_strips_whitespace_from_items(self):
        result = _parse_list(" a , b , c ", "x,y")
        assert result == ["a", "b", "c"]

    def test_falls_back_to_default_when_empty(self):
        result = _parse_list("", "x,y,z")
        assert result == ["x", "y", "z"]

    def test_falls_back_to_default_when_whitespace_only(self):
        result = _parse_list("   ", "x,y,z")
        assert result == ["x", "y", "z"]

    def test_skips_empty_items(self):
        result = _parse_list("a,,b,,c", "x")
        assert result == ["a", "b", "c"]


class TestValidateScheduleTime:
    """Tests for schedule time validation."""

    @pytest.mark.parametrize("valid_time", [
        "00:00", "08:00", "12:30", "23:59", "09:05", "15:45",
    ])
    def test_accepts_valid_times(self, valid_time):
        # Should not raise
        _validate_schedule_time(valid_time)

    @pytest.mark.parametrize("invalid_time", [
        "24:00", "25:00", "12:60", "99:99",
        "8:00", "08:0", "abc", "", "12:345",
        "08:00:00", "8am", "noon", "-1:00",
    ])
    def test_rejects_invalid_times(self, invalid_time):
        with pytest.raises(ValueError, match="Invalid schedule_time"):
            _validate_schedule_time(invalid_time)


class TestSettingsLoad:
    """Tests for Settings.load() classmethod."""

    def _env(self, overrides: dict | None = None) -> dict:
        """Build a minimal valid environment dict."""
        base = {"MONGODB_URI": "mongodb://localhost:27017/test"}
        if overrides:
            base.update(overrides)
        return base

    @patch.dict(os.environ, {"MONGODB_URI": "mongodb://localhost:27017/test"}, clear=True)
    def test_loads_with_minimal_config(self):
        settings = Settings.load()
        assert settings.mongodb_uri == "mongodb://localhost:27017/test"
        assert settings.database_name == "jobcopilot"
        assert settings.schedule_time == "08:00"
        assert settings.telegram_bot_token is None
        assert settings.telegram_chat_id is None

    @patch.dict(os.environ, {}, clear=True)
    def test_raises_when_mongodb_uri_missing(self):
        with pytest.raises(ValueError, match="MONGODB_URI"):
            Settings.load()

    @patch.dict(os.environ, {"MONGODB_URI": "   "}, clear=True)
    def test_raises_when_mongodb_uri_is_whitespace(self):
        with pytest.raises(ValueError, match="MONGODB_URI"):
            Settings.load()

    @patch.dict(os.environ, {
        "MONGODB_URI": "mongodb://localhost:27017/test",
        "DATABASE_NAME": "mydb",
    }, clear=True)
    def test_uses_provided_database_name(self):
        settings = Settings.load()
        assert settings.database_name == "mydb"

    @patch.dict(os.environ, {
        "MONGODB_URI": "mongodb://localhost:27017/test",
        "TELEGRAM_BOT_TOKEN": "bot123",
        "TELEGRAM_CHAT_ID": "chat456",
    }, clear=True)
    def test_loads_telegram_credentials(self):
        settings = Settings.load()
        assert settings.telegram_bot_token == "bot123"
        assert settings.telegram_chat_id == "chat456"

    @patch.dict(os.environ, {
        "MONGODB_URI": "mongodb://localhost:27017/test",
        "SEARCH_TERMS": "Python,Java,Go",
    }, clear=True)
    def test_parses_search_terms(self):
        settings = Settings.load()
        assert settings.search_terms == ["Python", "Java", "Go"]

    @patch.dict(os.environ, {
        "MONGODB_URI": "mongodb://localhost:27017/test",
        "LOCATIONS": "Remote,NYC",
    }, clear=True)
    def test_parses_locations(self):
        settings = Settings.load()
        assert settings.locations == ["Remote", "NYC"]

    @patch.dict(os.environ, {
        "MONGODB_URI": "mongodb://localhost:27017/test",
        "JOB_SOURCES": "linkedin,google",
    }, clear=True)
    def test_parses_job_sources(self):
        settings = Settings.load()
        assert settings.job_sources == ["linkedin", "google"]

    @patch.dict(os.environ, {
        "MONGODB_URI": "mongodb://localhost:27017/test",
    }, clear=True)
    def test_applies_default_search_terms(self):
        settings = Settings.load()
        assert "Biomedical Engineer" in settings.search_terms
        assert "Research Scientist" in settings.search_terms
        assert len(settings.search_terms) == 16

    @patch.dict(os.environ, {
        "MONGODB_URI": "mongodb://localhost:27017/test",
    }, clear=True)
    def test_applies_default_locations(self):
        settings = Settings.load()
        assert "India" in settings.locations
        assert "Remote" in settings.locations
        assert "Kolkata" in settings.locations
        assert len(settings.locations) == 12

    @patch.dict(os.environ, {
        "MONGODB_URI": "mongodb://localhost:27017/test",
    }, clear=True)
    def test_applies_default_job_sources(self):
        settings = Settings.load()
        assert settings.job_sources == ["linkedin", "indeed", "naukri", "google"]

    @patch.dict(os.environ, {
        "MONGODB_URI": "mongodb://localhost:27017/test",
        "SCHEDULE_TIME": "14:30",
    }, clear=True)
    def test_uses_provided_schedule_time(self):
        settings = Settings.load()
        assert settings.schedule_time == "14:30"

    @patch.dict(os.environ, {
        "MONGODB_URI": "mongodb://localhost:27017/test",
        "SCHEDULE_TIME": "25:00",
    }, clear=True)
    def test_raises_on_invalid_schedule_time(self):
        with pytest.raises(ValueError, match="Invalid schedule_time"):
            Settings.load()

    @patch.dict(os.environ, {
        "MONGODB_URI": "mongodb://localhost:27017/test",
        "SCHEDULE_TIME": "not-a-time",
    }, clear=True)
    def test_raises_on_non_time_schedule_value(self):
        with pytest.raises(ValueError, match="Invalid schedule_time"):
            Settings.load()
