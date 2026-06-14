"""BDD-TDD coverage tests for metadata_parser.py (Batch 3).

Triggered by application-test-coverage assessment: metadata_parser.py
was 81% line coverage. Missing lines cover:
- _parse_frontmatter: YAML error -> None, non-dict YAML -> None
- _parse_json_block: parse error -> None, dict with metadata key, dict w/o metadata
- parse_metadata: deps as string (comma-separated), consumers as string,
  last_reviewed date-object conversion

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from skill_governance.metadata_parser import (
    _parse_frontmatter,
    _parse_json_block,
    parse_metadata,
)


# ===========================================================================
# SCENARIO 1: _parse_frontmatter returns None for empty body
# ===========================================================================
def test_parse_frontmatter_returns_none_for_empty_body():
    """Empty body has no frontmatter, returns None."""
    assert _parse_frontmatter("") is None


# ===========================================================================
# SCENARIO 2: _parse_frontmatter returns None for invalid YAML
# ===========================================================================
def test_parse_frontmatter_returns_none_for_invalid_yaml():
    """Malformed YAML (unclosed bracket) returns None."""
    body = "---\n[unclosed\n---\n# x"
    assert _parse_frontmatter(body) is None


# ===========================================================================
# SCENARIO 3: _parse_frontmatter returns None for non-dict YAML
# ===========================================================================
def test_parse_frontmatter_returns_none_for_non_dict_yaml():
    """YAML that's a list (not a mapping) returns None."""
    body = "---\n- item1\n- item2\n---\n# x"
    assert _parse_frontmatter(body) is None


# ===========================================================================
# SCENARIO 4: _parse_json_block returns dict with `metadata` key
# ===========================================================================
def test_parse_json_block_extracts_metadata_key():
    """JSON with top-level 'metadata' key returns just that key."""
    body = json.dumps({"metadata": {"name": "x", "version": "1"}})
    result = _parse_json_block(body)
    assert result == {"name": "x", "version": "1"}


# ===========================================================================
# SCENARIO 5: _parse_json_block returns dict without `metadata` key
# ===========================================================================
def test_parse_json_block_returns_dict_even_without_metadata_key():
    """Plain JSON dict is returned as-is (no metadata key)."""
    body = json.dumps({"name": "x"})
    result = _parse_json_block(body)
    assert result == {"name": "x"}


# ===========================================================================
# SCENARIO 6: parse_metadata splits dependencies string by comma
#
# Given: a file with `dependencies: a, b, c` (string, not list)
# When:  parse_metadata is called
# Then:  dependencies is ['a', 'b', 'c']
# ===========================================================================
def test_parse_metadata_splits_dependencies_string_by_comma(tmp_path: Path):
    """A string `dependencies: a, b, c` is split into a list."""
    p = tmp_path / "skill.md"
    p.write_text("---\nname: x\ndependencies: a, b, c\n---\n# x")
    md = parse_metadata(p)
    assert md.dependencies == ["a", "b", "c"]


# ===========================================================================
# SCENARIO 7: parse_metadata splits intended_consumers string by comma
# ===========================================================================
def test_parse_metadata_splits_intended_consumers_string_by_comma(tmp_path: Path):
    """A string `intended_consumers: foo, bar` is split into a list."""
    p = tmp_path / "skill.md"
    p.write_text("---\nname: x\nintended_consumers: foo, bar\n---\n# x")
    md = parse_metadata(p)
    assert md.intended_consumers == ["foo", "bar"]


# ===========================================================================
# SCENARIO 8: parse_metadata handles dependencies as list
# ===========================================================================
def test_parse_metadata_handles_dependencies_as_list(tmp_path: Path):
    """A list dependencies is preserved as-is."""
    p = tmp_path / "skill.md"
    p.write_text("---\nname: x\ndependencies:\n  - a\n  - b\n---\n# x")
    md = parse_metadata(p)
    assert md.dependencies == ["a", "b"]


# ===========================================================================
# SCENARIO 9: parse_metadata converts last_reviewed date object to string
# ===========================================================================
def test_parse_metadata_converts_last_reviewed_date_to_string(tmp_path: Path):
    """YAML auto-parses '2026-06-14' to a date; we store it as a string."""
    p = tmp_path / "skill.md"
    p.write_text("---\nname: x\nlast_reviewed: 2026-06-14\n---\n# x")
    md = parse_metadata(p)
    assert isinstance(md.last_reviewed, str)
    assert md.last_reviewed == "2026-06-14"


# ===========================================================================
# SCENARIO 10: parse_metadata handles JSON file with metadata key
# ===========================================================================
def test_parse_metadata_handles_json_file_with_metadata_key(tmp_path: Path):
    """A .json file with a 'metadata' key parses correctly."""
    p = tmp_path / "skill.json"
    p.write_text(json.dumps({"metadata": {"name": "x", "version": "1"}}))
    md = parse_metadata(p)
    assert md.name == "x"
    assert md.version == "1"
