"""Utilities for extracting compressed archives."""

from __future__ import annotations

import gzip
import os
import shutil
import tarfile
import zipfile
from pathlib import Path


def extract(src: str | Path, dest: str | Path, preserve_permissions: bool = True) -> list[str]:
    """Extract an archive to *dest* and return the list of extracted paths.

    Supported formats: .tar.gz, .tgz, .tar.bz2, .tar, .zip, .gz, .tar.xz
    
    Args:
        src: Source archive path
        dest: Destination directory
        preserve_permissions: Whether to preserve file permissions (default: True)
    """
    src = Path(src)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    name = src.name.lower()
    if name.endswith(".tar.gz") or name.endswith(".tgz") or name.endswith(".tar.bz2") or name.endswith(".tar.xz") or name.endswith(".tar"):
        return _extract_tar(src, dest)
    if name.endswith(".zip"):
        return _extract_zip(src, dest)
    if name.endswith(".gz"):
        return _extract_gz(src, dest)
    raise ValueError(f"Unsupported archive format: {src}")


def _extract_tar(src: Path, dest: Path) -> list[str]:
    extracted: list[str] = []
    with tarfile.open(src) as tf:
        members = tf.getmembers()
        dest_resolved = str(dest.resolve())
        for member in members:
            # Guard against path traversal attacks
            member_path = (dest / member.name).resolve()
            if not str(member_path).startswith(dest_resolved):
                raise ValueError(f"Unsafe path in archive: {member.name}")
        tf.extractall(dest)  # noqa: S202
        # Only return files, not directories or symlinks
        extracted = [str(dest / m.name) for m in members if m.isfile()]
    return extracted


def _extract_zip(src: Path, dest: Path) -> list[str]:
    extracted: list[str] = []
    with zipfile.ZipFile(src) as zf:
        dest_resolved = str(dest.resolve())
        for info in zf.infolist():
            target = (dest / info.filename).resolve()
            if not str(target).startswith(dest_resolved):
                raise ValueError(f"Unsafe path in archive: {info.filename}")
        zf.extractall(dest)
        # Note: filter out directories and also skip __MACOSX metadata entries
        # that macOS adds to zip files — these are not useful and clutter the output.
        extracted = [
            str(dest / i.filename)
            for i in zf.infolist()
            if not i.is_dir() and not i.filename.startswith("__MACOSX/")
        ]
    return extracted


def _extract_gz(src: Path, dest: Path) -> list[str]:
    """Decompress a plain .gz file (not tar.gz)."""
    out_name = src.stem  # strip the .gz
    out_path = dest / out_name
    with gzip.open(src, "rb") as f_in, open(out_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return [str(out_path)]
