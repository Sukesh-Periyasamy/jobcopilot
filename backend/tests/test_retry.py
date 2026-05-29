"""Unit tests for the retry_with_backoff utility."""

import logging
from unittest.mock import patch

import pytest

from app.utils.retry import retry_with_backoff


class TestRetryWithBackoff:
    """Tests for retry_with_backoff function."""

    def test_succeeds_on_first_attempt(self):
        """Function that succeeds immediately returns its value without retrying."""
        result = retry_with_backoff(lambda: 42, max_retries=3, initial_backoff=1.0)
        assert result == 42

    def test_succeeds_after_one_failure(self):
        """Function that fails once then succeeds returns the successful value."""
        call_count = {"n": 0}

        def flaky():
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise ValueError("transient error")
            return "success"

        with patch("app.utils.retry.time.sleep") as mock_sleep:
            result = retry_with_backoff(flaky, max_retries=3, initial_backoff=1.0)

        assert result == "success"
        assert call_count["n"] == 2
        mock_sleep.assert_called_once_with(1.0)

    def test_succeeds_after_multiple_failures(self):
        """Function that fails multiple times then succeeds returns the value."""
        call_count = {"n": 0}

        def flaky():
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise RuntimeError(f"fail #{call_count['n']}")
            return "done"

        with patch("app.utils.retry.time.sleep") as mock_sleep:
            result = retry_with_backoff(flaky, max_retries=5, initial_backoff=2.0)

        assert result == "done"
        assert call_count["n"] == 3
        # Backoff delays: 2.0, 4.0
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(2.0)
        mock_sleep.assert_any_call(4.0)

    def test_raises_after_all_retries_exhausted(self):
        """Raises the last exception when all retries are exhausted."""

        def always_fails():
            raise ConnectionError("cannot connect")

        with patch("app.utils.retry.time.sleep"):
            with pytest.raises(ConnectionError, match="cannot connect"):
                retry_with_backoff(always_fails, max_retries=3, initial_backoff=1.0)

    def test_exponential_backoff_delays(self):
        """Verifies delays follow exponential pattern: B, 2B, 4B, 8B."""

        def always_fails():
            raise IOError("fail")

        with patch("app.utils.retry.time.sleep") as mock_sleep:
            with pytest.raises(IOError):
                retry_with_backoff(always_fails, max_retries=5, initial_backoff=0.5)

        # 4 sleeps for 5 retries (last attempt raises without sleeping)
        expected_delays = [0.5, 1.0, 2.0, 4.0]
        actual_delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays

    def test_logs_warning_on_each_retry(self, caplog):
        """Logs a warning message on each retry attempt."""
        call_count = {"n": 0}

        def flaky():
            call_count["n"] += 1
            if call_count["n"] <= 2:
                raise ValueError(f"error {call_count['n']}")
            return "ok"

        with patch("app.utils.retry.time.sleep"):
            with caplog.at_level(logging.WARNING, logger="app.utils.retry"):
                retry_with_backoff(flaky, max_retries=3, initial_backoff=1.0)

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 2
        assert "Attempt 1 failed" in warnings[0].message
        assert "Attempt 2 failed" in warnings[1].message

    def test_single_retry_raises_immediately(self):
        """With max_retries=1, raises on first failure without sleeping."""

        def fails():
            raise RuntimeError("instant fail")

        with patch("app.utils.retry.time.sleep") as mock_sleep:
            with pytest.raises(RuntimeError, match="instant fail"):
                retry_with_backoff(fails, max_retries=1, initial_backoff=1.0)

        mock_sleep.assert_not_called()

    def test_preserves_return_type(self):
        """Return value type is preserved from the callable."""
        result = retry_with_backoff(lambda: {"key": [1, 2, 3]}, max_retries=1)
        assert result == {"key": [1, 2, 3]}
