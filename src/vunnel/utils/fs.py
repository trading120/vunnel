from __future__ import annotations

import hashlib
import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_dir(path: str | Path) -> Path:
    """Create directory (and parents) if it does not already exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_remove(path: str | Path) -> bool:
    """Remove a file or directory tree. Returns True if something was removed."""
    p = Path(path)
    if not p.exists():
        return False
    if p.is_dir():
        shutil.rmtree(p)
        logger.debug(f"removed directory: {p}")
    else:
        p.unlink()
        logger.debug(f"removed file: {p}")
    return True


def sha256_file(path: str | Path, chunk_size: int = 65536) -> str:
    """Return the hex SHA-256 digest of the file at *path*.

    Args:
        path: Path to the file to hash
        chunk_size: Size of chunks to read (default 64KB; reduced from 128KB to
                    keep memory usage lower when hashing many small files)
    """
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write(path: str | Path, content: str | bytes, encoding: str = "utf-8") -> None:
    """Write *content* to *path* atomically via a temporary sibling file."""
    p = Path(path)
    ensure_dir(p.parent)
    tmp = p.with_suffix(p.suffix + ".tmp")
    try:
        if isinstance(content, str):
            tmp.write_text(content, encoding=encoding)
        else:
            tmp.write_bytes(content)
        tmp.replace(p)
        logger.debug(f"atomically wrote {p}")
    except Exception:
        safe_remove(tmp)
        raise


def list_files(directory: str | Path, suffix: str = "") -> list[Path]:
    """Return a sorted list of files in *directory* optionally filtered by *suffix*."""
    d = Path(directory)
    if not d.is_dir():
        return []
    files = [f for f in d.iterdir() if f.is_file()]
    if suffix:
        files = [f for f in files if f.name.endswith(suffix)]
    return sorted(files)
