"""BDD-TDD coverage tests for CTA-GAP-014: runtime_metrics partial results.

Triggered by application-test-coverage (FOCUSED_PICKS pass) on the
component-test-analysis gap-backlog. CTA-GAP-014 is a P1 gap (T1 risk):

    "runtime_metrics.ingest() has 5 failure-mode tests, but the case
    'malformed JSON returns partial results' is not tested. Risk: a
    regression that swallows ALL lines after a malformed one (instead
    of skipping the malformed line) would not be caught."

The existing tests in test_batch2_runtime_metrics_coverage.py cover:
- non-existent file (returns [])
- non-JSON line (1 valid + garbage -> 1 result)
- non-dict JSON (list/string/number/null -> skipped)
- lines without artifact_name (skipped)
- aggregation across multiple invocations
- missing optional fields (default to 0)
- None numeric fields
- empty file
- list of paths
- OSError on read

But the existing test_ingest_skips_non_json_lines only counts the
result count; it does NOT verify that:
1. ALL valid lines after a malformed one are still parsed
2. Aggregations across valid lines (tokens, retries) are correct
   when some lines are malformed

These tests pin the "partial results" contract: a file with a mix of
valid and malformed lines produces the correct aggregation of the
valid lines, with malformed lines skipped (not stopping parsing).

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

from pathlib import Path


# ===========================================================================
# SCENARIO 1: malformed line in the middle of valid lines doesn't stop parsing
#
# Given: a file with 3 valid lines and 1 malformed line in the middle
# When:  ingest() is called
# Then:  all 3 valid lines are aggregated into the result; the malformed
#        line is silently skipped (does not stop the parser)
# ===========================================================================
def test_malformed_line_in_middle_does_not_stop_parsing(tmp_path: Path):
    """A malformed line in the middle of the file doesn't stop parsing subsequent lines."""
    from skill_governance.runtime_metrics import ingest
    log = tmp_path / "log.jsonl"
    log.write_text(
        '{"artifact_name": "x", "total_tokens": 100, "retries": 1}\n'
        'this is not valid json at all\n'  # malformed in the middle
        '{"artifact_name": "x", "total_tokens": 200, "retries": 2}\n'
        '{"artifact_name": "y", "total_tokens": 50}\n'
    )
    result = ingest(str(log))
    by_name = {r.artifact_name: r for r in result}
    assert "x" in by_name, "artifact 'x' should still be in the results (malformed line was skipped)"
    assert "y" in by_name, "artifact 'y' (after the malformed line) should still be parsed"
    # x's aggregates should sum the two valid lines (100+200 tokens, 1+2 retries)
    assert by_name["x"].total_tokens == 300, (
        f"expected x.total_tokens=300 (sum of two valid lines), got {by_name['x'].total_tokens}"
    )
    assert by_name["x"].retries == 3, (
        f"expected x.retries=3 (sum of two valid lines), got {by_name['x'].retries}"
    )
    assert by_name["x"].invocations == 2, (
        f"expected x.invocations=2 (only valid lines counted), got {by_name['x'].invocations}"
    )


# ===========================================================================
# SCENARIO 2: file with many valid + many malformed lines returns the valid set
#
# Given: a file with 3 valid lines and 5 malformed lines (mixed)
# When:  ingest() is called
# Then:  exactly 1 result is returned (the 3 valid lines all aggregate
#        into the same artifact 'x'); the 5 malformed lines are skipped
# ===========================================================================
def test_partial_results_count_only_valid_lines(tmp_path: Path):
    """The result list length equals the number of unique artifact_names across VALID lines only."""
    from skill_governance.runtime_metrics import ingest
    log = tmp_path / "log.jsonl"
    log.write_text(
        '{"artifact_name": "x", "total_tokens": 100}\n'
        'garbage line 1\n'
        '{"artifact_name": "x", "total_tokens": 200}\n'
        '{not even close to json\n'
        '{"artifact_name": "x", "total_tokens": 300}\n'
        '[1, 2, 3]\n'  # valid JSON but not a dict
        '"a string"\n'  # valid JSON but not a dict
        'null\n'        # valid JSON but not a dict
    )
    result = ingest(str(log))
    assert len(result) == 1, f"expected 1 aggregated result, got {len(result)}: {result}"
    assert result[0].artifact_name == "x"
    assert result[0].invocations == 3, f"expected 3 invocations (valid lines only), got {result[0].invocations}"
    assert result[0].total_tokens == 600, f"expected 600 total tokens, got {result[0].total_tokens}"


# ===========================================================================
# SCENARIO 3: malformed line at the very end of the file doesn't break the last valid entry
#
# Given: a file with 2 valid lines and a malformed line at the end
# When:  ingest() is called
# Then:  the 2 valid lines are fully aggregated; the malformed line is skipped
# ===========================================================================
def test_malformed_line_at_end_does_not_truncate_previous_results(tmp_path: Path):
    """A malformed line at the end of the file doesn't lose the previous valid entries."""
    from skill_governance.runtime_metrics import ingest
    log = tmp_path / "log.jsonl"
    log.write_text(
        '{"artifact_name": "a", "total_tokens": 100, "retries": 5}\n'
        '{"artifact_name": "b", "total_tokens": 200, "retries": 10}\n'
        'trailing garbage\n'
    )
    result = ingest(str(log))
    by_name = {r.artifact_name: r for r in result}
    assert "a" in by_name and "b" in by_name
    assert by_name["a"].total_tokens == 100
    assert by_name["a"].retries == 5
    assert by_name["b"].total_tokens == 200
    assert by_name["b"].retries == 10


# ===========================================================================
# SCENARIO 4: truncated JSON line is treated as malformed
#
# Given: a file with one valid line and one truncated JSON line
# When:  ingest() is called
# Then:  only the valid line is parsed; the truncated one is skipped
# ===========================================================================
def test_truncated_json_line_is_treated_as_malformed(tmp_path: Path):
    """A line that starts as JSON but is incomplete (e.g. '{') is silently skipped."""
    from skill_governance.runtime_metrics import ingest
    log = tmp_path / "log.jsonl"
    log.write_text(
        '{\n'  # truncated JSON
        '{"artifact_name": "ok", "total_tokens": 42}\n'
    )
    result = ingest(str(log))
    assert len(result) == 1
    assert result[0].artifact_name == "ok"
    assert result[0].total_tokens == 42


# ===========================================================================
# SCENARIO 5: input/output tokens are also aggregated correctly across mixed valid/malformed lines
#
# Given: 2 valid lines for the same artifact with input/output splits
# When:  ingest() is called
# Then:  input_tokens and output_tokens are summed across the valid lines
# ===========================================================================
def test_partial_results_aggregate_input_output_tokens(tmp_path: Path):
    """Input/output token splits are aggregated across valid lines, ignoring malformed ones."""
    from skill_governance.runtime_metrics import ingest
    log = tmp_path / "log.jsonl"
    log.write_text(
        '{"artifact_name": "x", "total_tokens": 100, "input_tokens": 60, "output_tokens": 40}\n'
        'malformed line, please skip me\n'
        '{"artifact_name": "x", "total_tokens": 50, "input_tokens": 30, "output_tokens": 20}\n'
    )
    result = ingest(str(log))
    assert len(result) == 1
    assert result[0].total_tokens == 150
    assert result[0].total_input_tokens == 90
    assert result[0].total_output_tokens == 60
    assert result[0].invocations == 2


# ===========================================================================
# SCENARIO 6: multiple log files with mixed validity aggregate correctly
#
# Given: 2 log files; one is all-valid, the other is half-malformed
# When:  ingest() is called with both paths
# Then:  results from the all-valid file are present; results from
#        valid lines in the half-malformed file are also present
# ===========================================================================
def test_partial_results_across_multiple_files(tmp_path: Path):
    """A malformed line in one file doesn't prevent aggregation from other files."""
    from skill_governance.runtime_metrics import ingest
    log_a = tmp_path / "a.jsonl"
    log_a.write_text('{"artifact_name": "x", "total_tokens": 100}\n')
    log_b = tmp_path / "b.jsonl"
    log_b.write_text(
        'garbage\n'
        '{"artifact_name": "y", "total_tokens": 200}\n'
    )
    result = ingest([str(log_a), str(log_b)])
    by_name = {r.artifact_name: r for r in result}
    assert "x" in by_name and "y" in by_name, (
        f"expected both x and y; got {list(by_name)}"
    )
    assert by_name["x"].total_tokens == 100
    assert by_name["y"].total_tokens == 200
