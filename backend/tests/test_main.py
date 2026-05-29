"""Tests for backend/main.py CLI and FastAPI app configuration."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


# Resolve the backend directory relative to this test file
BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
MAIN_PY = os.path.join(BACKEND_DIR, "main.py")


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Run main.py with given arguments and capture output."""
    return subprocess.run(
        [sys.executable, MAIN_PY, *args],
        capture_output=True,
        text=True,
        cwd=BACKEND_DIR,
    )


class TestCLI:
    """Tests for CLI argument handling."""

    def test_no_args_shows_help_exit_0(self):
        result = run_cli()
        assert result.returncode == 0
        assert "serve" in result.stdout
        assert "scrape" in result.stdout

    def test_invalid_arg_shows_error_exit_2(self):
        result = run_cli("invalid_command")
        assert result.returncode == 2
        assert "invalid_command" in result.stderr
        assert "serve" in result.stdout
        assert "scrape" in result.stdout

    def test_another_invalid_arg_exit_2(self):
        result = run_cli("foobar")
        assert result.returncode == 2
        assert "foobar" in result.stderr


class TestFastAPIApp:
    """Tests for FastAPI app configuration."""

    def test_app_title(self):
        sys.path.insert(0, "backend")
        from main import app

        assert app.title == "JobCopilot API"

    def test_app_version(self):
        sys.path.insert(0, "backend")
        from main import app

        assert app.version == "1.0.0"

    def test_cors_middleware_configured(self):
        sys.path.insert(0, "backend")
        from main import app

        cors_middlewares = [
            m
            for m in app.user_middleware
            if m.cls.__name__ == "CORSMiddleware"
        ]
        assert len(cors_middlewares) == 1
        cors = cors_middlewares[0]
        assert cors.kwargs["allow_origins"] == [
            "https://sukeshperiyasamy.github.io"
        ]
        assert cors.kwargs["allow_credentials"] is True
        assert cors.kwargs["allow_methods"] == ["*"]
        assert cors.kwargs["allow_headers"] == ["*"]
