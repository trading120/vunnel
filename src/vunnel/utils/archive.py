"""Utilities for extracting compressed archives."""

from __future__ import annotations

import gzip
import os
import shutil
import tarfile
import zipfile
from pathlib import Path


def extract(src: str | Path, dest: str | Path) -> list[str]:
    """Extract an archive to *dest* and return the list of extracted paths."""
    src = Path(src)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    name = src.name.lower()
    if name.endswith(".tar.gz") or name.endswith(".tgz") or name.endswith(".tar.bz2") or name.endswith(".tar"):
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
        for member in members:
            # Guard against path traversal
            member_path = (dest / member.name).resolve()
            if not str(member_path).startswith(str(dest.resolve())):
                raise ValueError(f"Unsafe path in archive: {member.name}")
        tf.extractall(dest)  # noqa: S202
        extracted = [str(dest / m.name) for m in members if not m.isdir()]
    return extracted


def _extract_zip(src: Path, dest: Path) -> list[str]:
    extracted: list[str] = []
    with zipfile.ZipFile(src) as zf:
        for info in zf.infolist():
            target = (dest / info.filename).resolve()
            if not str(target).startswith(str(dest.resolve())):
                raise ValueError(f"Unsafe path in archive: {info.filename}")
        zf.extractall(dest)
        extracted = [
            str(dest / i.filename) for i in zf.infolist() if not i.is_dir()
        ]
    return extracted


def _extract_gz(src: Path, dest: Path) -> list[str]:
    """Decompress a plain .gz file (not tar.gz)."""
    out_name = src.stem  # strip the .gz
    out_path = dest / out_name
    with gzip.open(src, "rb") as f_in, open(out_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return [str(out_path)]
