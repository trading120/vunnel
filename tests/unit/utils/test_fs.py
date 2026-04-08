import os
from pathlib import Path

import pytest

from vunnel.utils.fs import ensure_dir, safe_remove, sha256_file, atomic_write, list_files


def test_ensure_dir_creates_nested_dirs(tmp_path):
    target = tmp_path / "a" / "b" / "c"
    result = ensure_dir(target)
    assert result == target
    assert target.is_dir()


def test_ensure_dir_is_idempotent(tmp_path):
    ensure_dir(tmp_path)
    ensure_dir(tmp_path)  # should not raise
    assert tmp_path.is_dir()


def test_safe_remove_file(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("hello")
    assert safe_remove(f) is True
    assert not f.exists()


def test_safe_remove_directory(tmp_path):
    d = tmp_path / "subdir"
    d.mkdir()
    (d / "nested.txt").write_text("data")
    assert safe_remove(d) is True
    assert not d.exists()


def test_safe_remove_nonexistent_returns_false(tmp_path):
    assert safe_remove(tmp_path / "ghost") is False


def test_sha256_file(tmp_path):
    import hashlib
    data = b"vunnel test data"
    f = tmp_path / "data.bin"
    f.write_bytes(data)
    expected = hashlib.sha256(data).hexdigest()
    assert sha256_file(f) == expected


def test_atomic_write_string(tmp_path):
    target = tmp_path / "out.txt"
    atomic_write(target, "hello world")
    assert target.read_text() == "hello world"
    assert not (tmp_path / "out.txt.tmp").exists()


def test_atomic_write_bytes(tmp_path):
    target = tmp_path / "out.bin"
    atomic_write(target, b"\x00\x01\x02")
    assert target.read_bytes() == b"\x00\x01\x02"


def test_atomic_write_creates_parent_dirs(tmp_path):
    target = tmp_path / "deep" / "nested" / "file.txt"
    atomic_write(target, "content")
    assert target.read_text() == "content"


def test_list_files_returns_sorted(tmp_path):
    for name in ["c.xml", "a.xml", "b.xml"]:
        (tmp_path / name).write_text("")
    result = list_files(tmp_path, suffix=".xml")
    assert [f.name for f in result] == ["a.xml", "b.xml", "c.xml"]


def test_list_files_filters_by_suffix(tmp_path):
    (tmp_path / "data.xml").write_text("")
    (tmp_path / "data.json").write_text("")
    result = list_files(tmp_path, suffix=".xml")
    assert len(result) == 1
    assert result[0].name == "data.xml"


def test_list_files_nonexistent_dir_returns_empty(tmp_path):
    assert list_files(tmp_path / "missing") == []
