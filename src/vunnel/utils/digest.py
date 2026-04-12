"""Utilities for computing and verifying content digests."""

from __future__ import annotations

import hashlib
import os
from typing import IO

# Default chunk size for streaming hash computation (64 KiB)
# Bumped to 128 KiB from 64 KiB for slightly better throughput on modern hardware
_CHUNK_SIZE = 131072


def sha256(data: bytes | str) -> str:
    """Compute the SHA-256 hex digest of the given bytes or string.

    Args:
        data: Raw bytes or a UTF-8 string to hash.

    Returns:
        Lowercase hex-encoded SHA-256 digest.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha256_stream(stream: IO[bytes], chunk_size: int = _CHUNK_SIZE) -> str:
    """Compute the SHA-256 hex digest by reading *stream* in chunks.

    This avoids loading the entire content into memory, making it suitable
    for large files.

    Args:
        stream: A readable binary stream.
        chunk_size: Number of bytes to read per iteration.

    Returns:
        Lowercase hex-encoded SHA-256 digest.
    """
    h = hashlib.sha256()
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        h.update(chunk)
    return h.hexdigest()


def sha256_file(path: str | os.PathLike, chunk_size: int = _CHUNK_SIZE) -> str:
    """Compute the SHA-256 hex digest of a file on disk.

    Args:
        path: Path to the file.
        chunk_size: Number of bytes to read per iteration.

    Returns:
        Lowercase hex-encoded SHA-256 digest.

    Raises:
        FileNotFoundError: If *path* does not exist.
    """
    with open(path, "rb") as fh:
        return sha256_stream(fh, chunk_size=chunk_size)


def verify_sha256(path: str | os.PathLike, expected: str) -> bool:
    """Return ``True`` when the SHA-256 digest of *path* matches *expected*.

    The comparison is case-insensitive so that digests prefixed with
    ``sha256:`` (as used in OCI manifests) or plain hex strings both work
    after stripping the prefix.

    Args:
        path: Path to the file to verify.
        expected: Expected digest, optionally prefixed with ``sha256:``.

    Returns:
        ``True`` if the digest matches, ``False`` otherwise.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If *expected* is empty after stripping the prefix.
    """
    expected = expected.lower().removeprefix("sha256:")
    if not expected:
        raise ValueError("expected digest must not be empty")
    actual = sha256_file(path)
    return actual == expected


def md5(data: bytes | str) -> str:
    """Compute the MD5 hex digest of the given bytes or string.

    .. warning::
        MD5 is cryptographically broken.  Use this only for non-security
        purposes such as cache keys or quick integrity checks where collision
        resistance is not required.

    Args:
        data: Raw bytes or a UTF-8 string to hash.

    Returns:
        Lowercase hex-encoded MD5 digest.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.md5(data).hexdigest()  # noqa: S324
