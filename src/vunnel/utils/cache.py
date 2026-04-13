"""Simple file-based caching utilities for vunnel providers."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from typing import Any

from vunnel.utils.fs import ensure_dir, safe_remove

log = logging.getLogger(__name__)

_DEFAULT_TTL = 60 * 60 * 24  # 24 hours in seconds


def cache_path(cache_dir: str, key: str) -> str:
    """Return the filesystem path for a given cache key."""
    hashed = hashlib.sha256(key.encode()).hexdigest()
    return os.path.join(cache_dir, f"{hashed}.json")


def get(cache_dir: str, key: str, ttl: int = _DEFAULT_TTL) -> Any | None:
    """Retrieve a cached value by key.

    Returns the cached value if it exists and has not expired,
    otherwise returns None.

    :param cache_dir: Directory where cache files are stored.
    :param key: Cache key string.
    :param ttl: Time-to-live in seconds. Use 0 to disable expiry.
    :return: Cached Python object or None.
    """
    path = cache_path(cache_dir, key)
    if not os.path.isfile(path):
        return None

    if ttl > 0:
        age = time.time() - os.path.getmtime(path)
        if age > ttl:
            log.debug("cache expired for key %r (age=%.0fs, ttl=%ds)", key, age, ttl)
            safe_remove(path)
            return None

    try:
        with open(path, encoding="utf-8") as f:
            entry = json.load(f)
        log.debug("cache hit for key %r", key)
        return entry.get("value")
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("failed to read cache entry %s: %s", path, exc)
        return None


def put(cache_dir: str, key: str, value: Any) -> None:
    """Store a value in the cache under the given key.

    :param cache_dir: Directory where cache files are stored.
    :param key: Cache key string.
    :param value: JSON-serialisable Python object to cache.
    """
    ensure_dir(cache_dir)
    path = cache_path(cache_dir, key)
    entry = {"key": key, "stored_at": time.time(), "value": value}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry, f)
        log.debug("cached value for key %r -> %s", key, path)
    except (OSError, TypeError) as exc:
        log.warning("failed to write cache entry %s: %s", path, exc)


def invalidate(cache_dir: str, key: str) -> bool:
    """Remove a single cache entry.

    :param cache_dir: Directory where cache files are stored.
    :param key: Cache key string.
    :return: True if the entry existed and was removed, False otherwise.
    """
    path = cache_path(cache_dir, key)
    removed = safe_remove(path)
    if removed:
        log.debug("invalidated cache entry for key %r", key)
    return removed


def clear(cache_dir: str) -> int:
    """Remove all cache entries from the given directory.

    :param cache_dir: Directory where cache files are stored.
    :return: Number of entries removed.
    """
    if not os.path.isdir(cache_dir):
        return 0

    count = 0
    for name in os.listdir(cache_dir):
        if name.endswith(".json"):
            safe_remove(os.path.join(cache_dir, name))
            count += 1

    log.debug("cleared %d cache entries from %s", count, cache_dir)
    return count
