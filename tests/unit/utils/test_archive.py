"""Tests for vunnel.utils.archive."""

from __future__ import annotations

import gzip
import io
import os
import tarfile
import zipfile
from pathlib import Path

import pytest

from vunnel.utils.archive import extract


@pytest.fixture()
def tmp(tmp_path: Path) -> Path:
    return tmp_path


def _make_tar_gz(dest: Path, files: dict[str, str]) -> Path:
    """Helper to create a tar.gz archive for testing."""
    archive = dest / "test.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        for name, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return archive


def _make_zip(dest: Path, files: dict[str, str]) -> Path:
    """Helper to create a zip archive for testing."""
    archive = dest / "test.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return archive


def _make_gz(dest: Path, content: str) -> Path:
    """Helper to create a gzip compressed file for testing."""
    archive = dest / "data.txt.gz"
    with gzip.open(archive, "wb") as f:
        f.write(content.encode())
    return archive


def test_extract_tar_gz(tmp: Path) -> None:
    src_dir = tmp / "src"
    src_dir.mkdir()
    out_dir = tmp / "out"
    archive = _make_tar_gz(src_dir, {"hello.txt": "hello world"})
    paths = extract(archive, out_dir)
    assert len(paths) == 1
    assert Path(paths[0]).read_text() == "hello world"


def test_extract_zip(tmp: Path) -> None:
    src_dir = tmp / "src"
    src_dir.mkdir()
    out_dir = tmp / "out"
    archive = _make_zip(src_dir, {"a.txt": "aaa", "b.txt": "bbb"})
    paths = extract(archive, out_dir)
    assert len(paths) == 2
    names = {Path(p).name for p in paths}
    assert names == {"a.txt", "b.txt"}


def test_extract_gz(tmp: Path) -> None:
    src_dir = tmp / "src"
    src_dir.mkdir()
    out_dir = tmp / "out"
    archive = _make_gz(src_dir, "plain content")
    paths = extract(archive, out_dir)
    assert len(paths) == 1
    assert Path(paths[0]).read_text() == "plain content"


def test_extract_creates_dest(tmp: Path) -> None:
    src_dir = tmp / "src"
    src_dir.mkdir()
    out_dir = tmp / "nested" / "output"
    archive = _make_tar_gz(src_dir, {"x.txt": "x"})
    extract(archive, out_dir)
    assert out_dir.is_dir()


def test_extract_unsupported_format(tmp: Path) -> None:
    bad = tmp / "file.7z"
    bad.write_text("dummy")
    with pytest.raises(ValueError, match="Unsupported archive format"):
        extract(bad, tmp / "out")


def test_extract_tar_gz_multiple_files(tmp: Path) -> None:
    # Verify that all files in a multi-entry tar.gz are extracted correctly.
    src_dir = tmp / "src"
    src_dir.mkdir()
    out_dir = tmp / "out"
    files = {"one.txt": "one", "two.txt": "two", "three.txt": "three"}
    archive = _make_tar_gz(src_dir, files)
    paths = extract(archive, out_dir)
    # should extract exactly as many files as were put in
    assert len(paths) == len(files)
    extracted_names = {Path(p).name for p in paths}
    assert extracted_names == set(files.keys())
    # verify each file's content matches what was written
    for path in paths:
        name = Path(path).name
        assert Path(path).read_text() == files[name]
