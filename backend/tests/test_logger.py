"""Tests for the logger module.

Note: These tests disable pytest's log capturing plugin to avoid
interference with root logger handler testing. Run with:
    python -m pytest tests/test_logger.py -p no:logging
"""

import logging
import os
from logging.handlers import RotatingFileHandler

import pytest

from app.utils.logger import (
    BACKUP_COUNT,
    LOG_FORMAT,
    MAX_BYTES,
    setup_logging,
)



@pytest.fixture(autouse=True)
def fresh_root_logger():
    """Ensure a clean root logger for each test.

    Removes ALL handlers (including pytest's LogCaptureHandler) before
    the test, and restores them after.
    """
    logger = logging.getLogger()
    original_handlers = logger.handlers[:]
    logger.handlers = []
    yield logger
    # Cleanup: remove any handlers added during the test
    for handler in logger.handlers[:]:
        handler.close()
    logger.handlers = original_handlers


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_returns_root_logger(self, fresh_root_logger):
        """setup_logging returns the root Logger instance."""
        result = setup_logging()
        assert result is fresh_root_logger

    def test_adds_rotating_file_handler(self, fresh_root_logger):
        """Logger should include a RotatingFileHandler."""
        setup_logging()
        file_handlers = [
            h for h in fresh_root_logger.handlers if isinstance(h, RotatingFileHandler)
        ]
        assert len(file_handlers) == 1

    def test_rotating_file_handler_max_bytes(self, fresh_root_logger):
        """RotatingFileHandler should have 10MB max size."""
        setup_logging()
        fh = next(
            h for h in fresh_root_logger.handlers if isinstance(h, RotatingFileHandler)
        )
        assert fh.maxBytes == 10 * 1024 * 1024

    def test_rotating_file_handler_backup_count(self, fresh_root_logger):
        """RotatingFileHandler should retain 5 backup files."""
        setup_logging()
        fh = next(
            h for h in fresh_root_logger.handlers if isinstance(h, RotatingFileHandler)
        )
        assert fh.backupCount == 5

    def test_adds_stream_handler(self, fresh_root_logger):
        """Logger should include a StreamHandler for console output."""
        setup_logging()
        stream_handlers = [
            h
            for h in fresh_root_logger.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, RotatingFileHandler)
        ]
        assert len(stream_handlers) == 1

    def test_idempotent_no_duplicate_handlers(self, fresh_root_logger):
        """Calling setup_logging multiple times should not add duplicate handlers."""
        setup_logging()
        count_after_first = len(fresh_root_logger.handlers)
        setup_logging()
        assert len(fresh_root_logger.handlers) == count_after_first

    def test_logger_level_is_debug(self, fresh_root_logger):
        """Root logger level should be DEBUG to allow all messages through."""
        setup_logging()
        assert fresh_root_logger.level == logging.DEBUG

    def test_file_handler_writes_to_data_dir(self, fresh_root_logger):
        """RotatingFileHandler should target data/jobcopilot.log."""
        setup_logging()
        fh = next(
            h for h in fresh_root_logger.handlers if isinstance(h, RotatingFileHandler)
        )
        assert fh.baseFilename.endswith("jobcopilot.log")
        assert "data" in fh.baseFilename


class TestConstants:
    """Tests for module-level constants."""

    def test_max_bytes_is_10mb(self):
        """MAX_BYTES should be 10MB."""
        assert MAX_BYTES == 10 * 1024 * 1024

    def test_backup_count_is_5(self):
        """BACKUP_COUNT should be 5."""
        assert BACKUP_COUNT == 5

    def test_log_format_has_iso8601_timestamp(self):
        """Format should include asctime for ISO 8601 timestamps."""
        assert "%(asctime)s" in LOG_FORMAT

    def test_log_format_has_level(self):
        """Format should include levelname."""
        assert "%(levelname)s" in LOG_FORMAT

    def test_log_format_has_module(self):
        """Format should include module name."""
        assert "%(module)s" in LOG_FORMAT

    def test_log_format_has_message(self):
        """Format should include message."""
        assert "%(message)s" in LOG_FORMAT

    def test_format_uses_pipe_separator(self):
        """Format fields should be separated by pipe characters."""
        assert " | " in LOG_FORMAT
