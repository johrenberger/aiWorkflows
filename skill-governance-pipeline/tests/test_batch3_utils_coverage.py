"""BDD-TDD coverage tests for utils.py (Batch 3).

Triggered by application-test-coverage assessment: utils.py
was 70% line coverage. Missing lines cover:
- sha256_text: hashes a string
- sha256_file: hashes a file in chunks
- estimate_tokens: empty text -> 0, returns max(1, ...)
- estimate_tokens_from_bytes: returns max(1, ...)
- parse_iso_timestamp: invalid input -> None
- FileInfo.modified_timestamp
- is_skill_artifact: extension check, path hint, basename check, False fallback
- walk_files: deterministic order, nonexistent root
- read_text_safe: UnicodeDecodeError fallback
- write_json: creates parent dirs
- write_text: creates parent dirs
- relative_to_root: ValueError fallback

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from skill_governance.utils import (
    FileInfo,
    estimate_tokens,
    estimate_tokens_from_bytes,
    is_skill_artifact,
    parse_iso_timestamp,
    read_text_safe,
    relative_to_root,
    sha256_file,
    sha256_text,
    utc_now_iso,
    walk_files,
    write_json,
    write_text,
)


# ===========================================================================
# SCENARIO 1: sha256_text hashes a string
# ===========================================================================
def test_sha256_text_hashes_string_deterministically():
    """sha256_text returns the same hash for the same input."""
    h1 = sha256_text("hello")
    h2 = sha256_text("hello")
    assert h1 == h2
    assert len(h1) == 64  # hex SHA-256
    assert sha256_text("hello") != sha256_text("world")


# ===========================================================================
# SCENARIO 2: sha256_file hashes a file in chunks
# ===========================================================================
def test_sha256_file_hashes_large_file_via_chunked_read(tmp_path: Path):
    """sha256_file handles large files via 64KB chunked reads."""
    p = tmp_path / "big.txt"
    p.write_bytes(b"x" * (64 * 1024 * 3))  # 3 chunks worth
    h = sha256_file(p)
    assert len(h) == 64
    # Should match sha256_text of the same content
    assert h == sha256_text("x" * (64 * 1024 * 3))


# ===========================================================================
# SCENARIO 3: estimate_tokens returns 0 for empty text
# ===========================================================================
def test_estimate_tokens_returns_zero_for_empty_text():
    """Empty text returns 0 (not max(1, 0))."""
    assert estimate_tokens("") == 0


# ===========================================================================
# SCENARIO 4: estimate_tokens_from_bytes returns max(1, ...)
# ===========================================================================
def test_estimate_tokens_from_bytes_returns_at_least_one():
    """Even a 0-byte file returns at least 1 token."""
    assert estimate_tokens_from_bytes(0) == 1
    assert estimate_tokens_from_bytes(100) == 25


# ===========================================================================
# SCENARIO 5: parse_iso_timestamp returns None for invalid input
# ===========================================================================
def test_parse_iso_timestamp_returns_none_for_invalid_input():
    """Invalid ISO strings return None."""
    assert parse_iso_timestamp("") is None
    assert parse_iso_timestamp("not a date") is None
    assert parse_iso_timestamp("2026-13-99T99:99:99") is None


# ===========================================================================
# SCENARIO 6: parse_iso_timestamp handles trailing Z
# ===========================================================================
def test_parse_iso_timestamp_handles_trailing_z():
    """A 'Z' suffix is accepted as UTC."""
    from datetime import timezone
    dt = parse_iso_timestamp("2026-06-14T00:00:00Z")
    assert dt is not None
    assert dt.tzinfo is not None
    # The offset is +00:00 (UTC)
    assert dt.utcoffset().total_seconds() == 0


# ===========================================================================
# SCENARIO 7: utc_now_iso returns Z-suffixed ISO string
# ===========================================================================
def test_utc_now_iso_returns_z_suffixed_string():
    """utc_now_iso ends with 'Z' (UTC marker)."""
    s = utc_now_iso()
    assert s.endswith("Z")
    assert "T" in s


# ===========================================================================
# SCENARIO 8: FileInfo.modified_timestamp returns Z-suffixed ISO
# ===========================================================================
def test_file_info_modified_timestamp_returns_iso_string(tmp_path: Path):
    """FileInfo.modified_timestamp is a Z-suffixed ISO string."""
    p = tmp_path / "x.txt"
    p.write_text("hello")
    fi = FileInfo(path=p, size_bytes=5, content_hash="h")
    ts = fi.modified_timestamp
    assert ts.endswith("Z")
    assert "T" in ts


# ===========================================================================
# SCENARIO 9: is_skill_artifact returns False for unknown extension
# ===========================================================================
def test_is_skill_artifact_returns_false_for_unknown_extension(tmp_path: Path):
    """A .py file (not in SKILL_EXTENSIONS) returns False."""
    p = tmp_path / "skills" / "thing.py"
    p.parent.mkdir()
    p.write_text("# python")
    assert is_skill_artifact(p, tmp_path) is False


# ===========================================================================
# SCENARIO 10: is_skill_artifact recognizes known basenames
# ===========================================================================
def test_is_skill_artifact_recognizes_known_basenames(tmp_path: Path):
    """Files named AGENT, AGENTS, SKILL, PROMPT, INSTRUCTIONS are recognized."""
    for name in ("AGENT", "AGENTS", "SKILL", "PROMPT", "INSTRUCTIONS"):
        p = tmp_path / f"{name}.md"
        p.write_text("x")
        assert is_skill_artifact(p, tmp_path) is True, f"failed for {name}"


# ===========================================================================
# SCENARIO 11: walk_files yields nothing for nonexistent root
# ===========================================================================
def test_walk_files_yields_nothing_for_nonexistent_root(tmp_path: Path):
    """A nonexistent root returns an empty iterator."""
    result = list(walk_files(tmp_path / "nope"))
    assert result == []


# ===========================================================================
# SCENARIO 12: walk_files yields files in deterministic sorted order
# ===========================================================================
def test_walk_files_yields_files_in_sorted_order(tmp_path: Path):
    """walk_files iterates in sorted order for determinism."""
    (tmp_path / "a.md").write_text("a")
    (tmp_path / "b.md").write_text("b")
    (tmp_path / "c.md").write_text("c")
    result = list(walk_files(tmp_path))
    names = [p.name for p in result]
    assert names == sorted(names)


# ===========================================================================
# SCENARIO 13: read_text_safe handles UnicodeDecodeError
# ===========================================================================
def test_read_text_safe_handles_unicode_decode_error(tmp_path: Path):
    """A file with non-UTF-8 bytes still returns a string (latin-1 fallback)."""
    p = tmp_path / "binary.md"
    p.write_bytes(b"\xff\xfe\x00\x01invalid")
    result = read_text_safe(p)
    assert isinstance(result, str)
    # The latin-1 fallback replaces undecodable chars
    assert len(result) > 0


# ===========================================================================
# SCENARIO 14: write_json creates parent directories
# ===========================================================================
def test_write_json_creates_parent_directories(tmp_path: Path):
    """write_json creates the parent dir if it doesn't exist."""
    p = tmp_path / "deep" / "nested" / "data.json"
    write_json(p, {"key": "value"})
    assert p.exists()
    data = json.loads(p.read_text())
    assert data == {"key": "value"}


# ===========================================================================
# SCENARIO 15: write_text creates parent directories
# ===========================================================================
def test_write_text_creates_parent_directories(tmp_path: Path):
    """write_text creates the parent dir if it doesn't exist."""
    p = tmp_path / "deep" / "nested" / "data.txt"
    write_text(p, "hello")
    assert p.exists()
    assert p.read_text() == "hello"


# ===========================================================================
# SCENARIO 16: relative_to_root falls back to absolute path on ValueError
# ===========================================================================
def test_relative_to_root_falls_back_on_value_error(tmp_path: Path):
    """A path not under root returns its absolute form, not raise."""
    p = tmp_path / "x" / "y.md"
    p.parent.mkdir()
    p.write_text("x")
    other_root = tmp_path / "other"
    other_root.mkdir()
    rel = relative_to_root(p, other_root)
    # Falls back to the path as-is
    assert rel == str(p).replace(os.sep, "/") or rel == "x/y.md"
