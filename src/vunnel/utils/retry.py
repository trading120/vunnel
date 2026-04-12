"""Retry utilities for HTTP requests and other transient failures."""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Callable, Tuple, Type

logger = logging.getLogger(__name__)

DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 2.0
DEFAULT_DELAY = 5.0  # increased from 1.0 — 1s felt too aggressive for network calls
MAX_DELAY = 60.0  # cap the delay so it doesn't grow unbounded on many retries


def retry_request(
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
    delay: float = DEFAULT_DELAY,
    on_exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator that retries a function on specified exceptions with exponential backoff.

    :param retries: Maximum number of retry attempts.
    :param backoff: Multiplier applied to delay between retries.
    :param delay: Initial delay in seconds between retries.
    :param on_exceptions: Tuple of exception types that trigger a retry.

    Note: delay is capped at MAX_DELAY (60s) to avoid excessively long waits.

    Example usage::

        @retry_request(retries=5, delay=2.0, on_exceptions=(IOError, TimeoutError))
        def fetch_data(url):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, retries + 2):
                try:
                    return func(*args, **kwargs)
                except on_exceptions as exc:
                    last_exception = exc
                    if attempt > retries:
                        logger.error(
                            "function %s failed after %d attempts: %s",
                            func.__name__,
                            retries + 1,
                            exc,
                        )
                        raise
                    logger.warning(
                        "attempt %d/%d for %s failed: %s — retrying in %.1fs",
                        attempt,
                        retries + 1,
                        func.__name__,
                        exc,
                        current_delay,
                    )
                    time.sleep(current_delay)
                    current_delay = min(current_delay * backoff, MAX_DELAY)

            raise last_exception  # pragma: no cover

        return wrapper

    return decorator
