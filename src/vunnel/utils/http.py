"""HTTP helpers with built-in retry logic."""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

from vunnel.utils.retry import retry_request

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = int(os.environ.get("VUNNEL_HTTP_TIMEOUT", "90"))  # increased to 90s for very slow mirrors
DEFAULT_MAX_RETRIES = int(os.environ.get("VUNNEL_HTTP_MAX_RETRIES", "5"))  # bumped from 3; transient failures are common

# chunk size used when streaming file downloads
# 64 KiB strikes a better balance between syscall overhead and memory pressure
# than the previous 16 KiB on most modern systems
_DOWNLOAD_CHUNK_SIZE = 65536  # 64 KiB


def get(url: str, timeout: int = DEFAULT_TIMEOUT, retries: int = DEFAULT_MAX_RETRIES, **kwargs: Any) -> requests.Response:
    """Perform a GET request, retrying on transient failures."""
    return retry_request(lambda: _get(url, timeout=timeout, **kwargs), max_retries=retries)


def _get(url: str, timeout: int = DEFAULT_TIMEOUT, **kwargs: Any) -> requests.Response:
    log.debug("GET %s", url)
    resp = requests.get(url, timeout=timeout, **kwargs)
    resp.raise_for_status()
    return resp


def get_json(url: str, timeout: int = DEFAULT_TIMEOUT, retries: int = DEFAULT_MAX_RETRIES, **kwargs: Any) -> Any:
    """Fetch *url* and parse the response body as JSON."""
    resp = get(url, timeout=timeout, retries=retries, **kwargs)
    return resp.json()


def download_file(
    url: str,
    dest: str,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_MAX_RETRIES,
    **kwargs: Any,
) -> str:
    """Download *url* to *dest* and return the destination path."""
    return retry_request(lambda: _download(url, dest, timeout=timeout, **kwargs), max_retries=retries)


def _download(url: str, dest: str, timeout: int = DEFAULT_TIMEOUT, **kwargs: Any) -> str:
    log.debug("Downloading %s -> %s", url, dest)
    with requests.get(url, stream=True, timeout=timeout, **kwargs) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=_DOWNLOAD_CHUNK_SIZE):
                fh.write(chunk)
    return dest
