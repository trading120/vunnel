"""Utilities for downloading files via FTP."""

from __future__ import annotations

import ftplib
import logging
import os
from typing import Optional

log = logging.getLogger(__name__)


def download(
    host: str,
    path: str,
    dest: str,
    user: str = "anonymous",
    password: str = "anonymous@",
    timeout: int = 30,
    retries: int = 3,
) -> str:
    """Download a file from an FTP server.

    Args:
        host: FTP server hostname.
        path: Remote path to the file.
        dest: Local destination path (file or directory).
        user: FTP username (default: anonymous).
        password: FTP password (default: anonymous@).
        timeout: Connection timeout in seconds.
        retries: Number of retry attempts on transient errors.

    Returns:
        The local path where the file was saved.

    Raises:
        ftplib.Error: On FTP-level errors after all retries are exhausted.
        OSError: On local filesystem errors.
    """
    # If dest is a directory, derive filename from the remote path
    if os.path.isdir(dest):
        filename = os.path.basename(path)
        dest = os.path.join(dest, filename)

    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)

    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            log.debug("ftp download attempt %d/%d: ftp://%s%s -> %s", attempt, retries, host, path, dest)
            _download(host=host, path=path, dest=dest, user=user, password=password, timeout=timeout)
            log.debug("ftp download complete: %s", dest)
            return dest
        except (ftplib.Error, OSError, EOFError, ConnectionError) as exc:
            last_exc = exc
            log.warning("ftp download attempt %d/%d failed: %s", attempt, retries, exc)

    raise RuntimeError(f"ftp download failed after {retries} attempts: {last_exc}") from last_exc


def _download(host: str, path: str, dest: str, user: str, password: str, timeout: int) -> None:
    """Internal helper that performs a single FTP download attempt."""
    with ftplib.FTP(timeout=timeout) as ftp:
        ftp.connect(host)
        ftp.login(user=user, passwd=password)
        ftp.set_pasv(True)

        with open(dest, "wb") as f:
            ftp.retrbinary(f"RETR {path}", f.write)


def list_directory(host: str, path: str = "/", user: str = "anonymous", password: str = "anonymous@", timeout: int = 30) -> list[str]:
    """List files in a remote FTP directory.

    Args:
        host: FTP server hostname.
        path: Remote directory path.
        user: FTP username.
        password: FTP password.
        timeout: Connection timeout in seconds.

    Returns:
        A list of filenames in the remote directory.
    """
    log.debug("ftp list: ftp://%s%s", host, path)
    with ftplib.FTP(timeout=timeout) as ftp:
        ftp.connect(host)
        ftp.login(user=user, passwd=password)
        ftp.set_pasv(True)
        return ftp.nlst(path)
