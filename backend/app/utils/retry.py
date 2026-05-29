"""Retry utility with exponential backoff.

Provides a generic retry mechanism that retries a callable with
exponential backoff delays: B, 2B, 4B, ..., 2^(attempt-1) * B seconds.
Logs a warning on each retry attempt and raises the final exception
after all retries are exhausted.
"""

import logging
import time
from typing import Callable, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


def retry_with_backoff(
    fn: Callable[[], T],
    max_retries: int = 3,
    initial_backoff: float = 1.0,
) -> T:
    """Retry a callable with exponential backoff on failure.

    Calls `fn()` up to `max_retries` times. On each failure, waits for
    an exponentially increasing delay before retrying:
    - Attempt 1 failure: wait `initial_backoff` seconds
    - Attempt 2 failure: wait `2 * initial_backoff` seconds
    - Attempt N failure: wait `2^(N-1) * initial_backoff` seconds

    Logs a warning on each retry attempt with the attempt number and error.
    Raises the final exception after all retries are exhausted.

    Args:
        fn: A zero-argument callable to execute.
        max_retries: Maximum number of retry attempts (must be >= 1).
        initial_backoff: Initial backoff delay in seconds (must be > 0).

    Returns:
        The return value of `fn()` on success.

    Raises:
        The exception from the last failed attempt if all retries are exhausted.
    """
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(
                    "All %d retry attempts exhausted. Last error: %s",
                    max_retries,
                    e,
                )
                raise
            sleep_time = initial_backoff * (2 ** attempt)
            logger.warning(
                "Attempt %d failed: %s. Retrying in %ss...",
                attempt + 1,
                e,
                sleep_time,
            )
            time.sleep(sleep_time)

    # This should never be reached, but satisfies type checkers
    raise RuntimeError("Unexpected state in retry_with_backoff")
