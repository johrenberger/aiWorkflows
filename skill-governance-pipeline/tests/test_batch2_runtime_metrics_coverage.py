"""BDD-TDD coverage tests for runtime_metrics.py (Batch 2).

Triggered by application-test-coverage assessment: runtime_metrics.py
was 81% line coverage with 0 tests. The Phase 7 fix code (the real
JSONL parser) is completely untested.

8 statements uncovered (L43, 46-47, 51, 54-56, 58, 61) are all
edge cases in the ingest() function: empty file, missing path,
non-JSON line, non-dict line, missing artifact_name field, etc.

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

import json
import os
from pathlib import Path


# ===========================================================================
# SCENARIO 1: ingest returns [] for a non-existent file
#
# Given: a path to a file that doesn't exist
# When:  ingest() is called
# Then:  it returns [] (no error, no entry)
# ===========================================================================
def test_ingest_returns_empty_list_for_missing_file(tmp_path: Path):
    """A non-existent file produces no entries (no error)."""
    from skill_governance.runtime_metrics import ingest
    result = ingest(str(tmp_path / "missing.jsonl"))
    assert result == [], f"missing file should produce [], got {result}"


# ===========================================================================
# SCENARIO 2: ingest handles non-JSON lines by skipping them
#
# Given: a file with a mix of valid JSON lines and garbage
# When:  ingest() is called
# Then:  only the valid lines produce entries; the garbage is skipped
# ===========================================================================
def test_ingest_skips_non_json_lines(tmp_path: Path):
    """Malformed JSON lines are silently skipped."""
    from skill_governance.runtime_metrics import ingest
    log = tmp_path / "log.jsonl"
    log.write_text(
        "this is not json\n"
        "{\n"  # truncated JSON
        '{"artifact_name": "x", "total_tokens": 100, "success": true}\n'
    )
    result = ingest(str(log))
    assert len(result) == 1, f"expected 1 valid entry, got {len(result)}"
    assert result[0].artifact_name == "x"


# ===========================================================================
# SCENARIO 3: ingest handles non-dict lines by skipping them
#
# Given: a file with JSON values that aren't dicts (e.g. lists, strings)
# When:  ingest() is called
# Then:  those lines are skipped
# ===========================================================================
def test_ingest_skips_non_dict_json_values(tmp_path: Path):
    """Non-dict JSON values (lists, strings, numbers) are skipped."""
    from skill_governance.runtime_metrics import ingest
    log = tmp_path / "log.jsonl"
    log.write_text(
        '"just a string"\n'
        "[1, 2, 3]\n"
        "42\n"
        "null\n"
        '{"artifact_name": "x", "total_tokens": 100}\n'
    )
    result = ingest(str(log))
    assert len(result) == 1, f"expected 1 entry (the dict), got {len(result)}"


# ===========================================================================
# SCENARIO 4: ingest skips lines without an artifact_name field
# ===========================================================================
def test_ingest_skips_lines_without_artifact_name(tmp_path: Path):
    """Lines missing or with non-string artifact_name are skipped."""
    from skill_governance.runtime_metrics import ingest
    log = tmp_path / "log.jsonl"
    log.write_text(
        '{"total_tokens": 100}\n'  # no artifact_name
        '{"artifact_name": 42, "total_tokens": 50}\n'  # non-string name
        '{"artifact_name": null, "total_tokens": 50}\n'  # null name
        '{"artifact_name": "x", "total_tokens": 100}\n'
    )
    result = ingest(str(log))
    assert len(result) == 1, f"expected 1 valid entry, got {len(result)}"
    assert result[0].artifact_name == "x"


# ===========================================================================
# SCENARIO 5: ingest aggregates retries across multiple invocations
# ===========================================================================
def test_ingest_aggregates_retries(tmp_path: Path):
    """Multiple invocations of the same artifact have retries summed."""
    from skill_governance.runtime_metrics import ingest
    log = tmp_path / "log.jsonl"
    log.write_text(
        '{"artifact_name": "x", "total_tokens": 100, "retries": 1}\n'
        '{"artifact_name": "x", "total_tokens": 200, "retries": 2}\n'
    )
    result = ingest(str(log))
    assert len(result) == 1
    assert result[0].retries == 3, f"expected 3 retries, got {result[0].retries}"
    assert result[0].total_tokens == 300, f"expected 300 tokens, got {result[0].total_tokens}"


# ===========================================================================
# SCENARIO 6: ingest handles missing optional fields (input_tokens, output_tokens)
# ===========================================================================
def test_ingest_handles_missing_optional_fields(tmp_path: Path):
    """Missing input_tokens/output_tokens default to 0."""
    from skill_governance.runtime_metrics import ingest
    log = tmp_path / "log.jsonl"
    log.write_text(
        '{"artifact_name": "x", "total_tokens": 100}\n'  # no input/output split
    )
    result = ingest(str(log))
    assert len(result) == 1
    assert result[0].total_input_tokens == 0
    assert result[0].total_output_tokens == 0


# ===========================================================================
# SCENARIO 7: ingest handles None values for numeric fields
# ===========================================================================
def test_ingest_handles_none_numeric_fields(tmp_path: Path):
    """None values for numeric fields default to 0."""
    from skill_governance.runtime_metrics import ingest
    log = tmp_path / "log.jsonl"
    log.write_text(
        '{"artifact_name": "x", "total_tokens": null, "retries": null}\n'
    )
    result = ingest(str(log))
    assert len(result) == 1
    assert result[0].total_tokens == 0
    assert result[0].retries == 0


# ===========================================================================
# SCENARIO 8: ingest handles empty file (just whitespace)
# ===========================================================================
def test_ingest_handles_empty_file(tmp_path: Path):
    """An empty file produces no entries."""
    from skill_governance.runtime_metrics import ingest
    log = tmp_path / "log.jsonl"
    log.write_text("")
    result = ingest(str(log))
    assert result == [], f"empty file should produce [], got {result}"


# ===========================================================================
# SCENARIO 9: ingest accepts a list of paths (not just one)
# ===========================================================================
def test_ingest_accepts_list_of_paths(tmp_path: Path):
    """ingest() accepts a list of paths and merges results."""
    from skill_governance.runtime_metrics import ingest
    log_a = tmp_path / "a.jsonl"
    log_a.write_text('{"artifact_name": "x", "total_tokens": 100}\n')
    log_b = tmp_path / "b.jsonl"
    log_b.write_text('{"artifact_name": "y", "total_tokens": 200}\n')
    result = ingest([str(log_a), str(log_b)])
    names = {r.artifact_name for r in result}
    assert names == {"x", "y"}, f"expected x and y, got {names}"


# ===========================================================================
# SCENARIO 10: ingest handles OSError on read (e.g. permission denied)
# ===========================================================================
def test_ingest_handles_oserror_silently(tmp_path: Path, monkeypatch):
    """An OSError during read is silently handled (returns what was read so far)."""
    from skill_governance import runtime_metrics
    log = tmp_path / "log.jsonl"
    log.write_text('{"artifact_name": "x", "total_tokens": 100}\n')

    def _raise(*args, **kwargs):
        raise OSError("simulated read failure")

    monkeypatch.setattr("pathlib.Path.read_text", _raise)
    # Should not raise; returns whatever was read so far (empty)
    result = runtime_metrics.ingest(str(log))
    assert result == [], f"OSError should be handled, got {result}"
