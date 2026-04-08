from __future__ import annotations

import logging
import os
from typing import Any

import requests

from vunnel.utils.retry import retry_request

DEFAULT_TIMEOUT = int(os.environ.get("VUNNEL_HTTP_TIMEOUT", "30"))
DEFAULT_MAX_RETRIES = int(os.environ.get("VUNNEL_HTTP_MAX_RETRIES", "3"))
DEFAULT_BACKOFF = float(os.environ.get("VUNNEL_HTTP_BACKOFF", "1.0"))

LOGGER = logging.getLogger(__name__)


def get(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
    **kwargs: Any,
) -> requests.Response:
    """Perform a GET request with automatic retries on transient failures."""

    @retry_request(max_retries=max_retries, backoff=backoff)
    def _get() -> requests.Response:
        LOGGER.debug("GET %s", url)
        response = requests.get(url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response

    return _get()


def get_json(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
    **kwargs: Any,
) -> Any:
    """Perform a GET request and return parsed JSON body."""
    response = get(url, timeout=timeout, max_retries=max_retries, backoff=backoff, **kwargs)
    return response.json()


def download_file(
    url: str,
    dest: str,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
    chunk_size: int = 8192,
    **kwargs: Any,
) -> str:
    """Download a file from *url* to *dest*, returning the destination path."""

    @retry_request(max_retries=max_retries, backoff=backoff)
    def _download() -> str:
        LOGGER.debug("downloading %s -> %s", url, dest)
        with requests.get(url, stream=True, timeout=timeout, **kwargs) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    fh.write(chunk)
        return dest

    return _download()
