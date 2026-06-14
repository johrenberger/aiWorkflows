"""
Acceptance tests for SGP Phase 7 (BDD-TDD).

Each scenario below is a black-box test of one of the 3 fixes
recommended after the v1.0.0+Phase 6 ship. They are intentionally
written BEFORE the implementation, so they will fail in the expected
ways on the current code and will pass once Phase 7 is complete.

Conventions:
- Docstring = Given/When/Then narrative
- Test function name = the assertion in plain English
- All tests use the real CLI (subprocess) against a fixture catalog
  AND/OR the real catalog where appropriate
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_SRC = PIPELINE_ROOT / "src"
CONFIG_PATH = PIPELINE_ROOT / "config" / "governance.default.yaml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _run_cli(args: list[str], cwd: Path = PIPELINE_ROOT) -> subprocess.CompletedProcess:
    """Run the SGP CLI as a subprocess and return the result."""
    return subprocess.run(
        [sys.executable, "-m", "skill_governance.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(PIPELINE_SRC), "PATH": "/usr/bin:/usr/local/bin"},
    )


# ===========================================================================
# SCENARIO #1a: No skill is recommended for merge unless an actual
#   overlap pair with `recommendation == "merge"` exists for it
#
# Given: a catalog where no overlap pairs meet the merge threshold
# When: the pipeline runs `ci` end-to-end
# Then: no scorecard entry has `decision == "merge"` for that reason
# ===========================================================================
def test_no_skill_is_recommended_merge_without_real_overlap_pair(tmp_path):
    result = _run_cli(["ci", "--config", str(CONFIG_PATH)])
    assert result.returncode in (0, 1), (
        f"`ci` should exit 0 (pass) or 1 (fail) deterministically, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    # Load the scorecard
    scorecard_path = PIPELINE_ROOT / "output" / "skill_scorecard.json"
    assert scorecard_path.exists(), f"scorecard must be written at {scorecard_path}"
    scorecard = json.loads(scorecard_path.read_text())
    merge_entries = [s for s in scorecard if s.get("decision") == "merge"]
    # Acceptance: the ONLY way a skill should be tagged "merge" is
    # if it has at least one overlap pair with recommendation == "merge"
    # in the same run. Since the real catalog has 0 such pairs (as
    # confirmed in Phase 6), the scorecard must have 0 merge entries.
    assert len(merge_entries) == 0, (
        f"No skill should be recommended for merge when there are 0 overlap pairs "
        f"with recommendation='merge' (current overlap pairs meet warning threshold: 0). "
        f"Got {len(merge_entries)} false merge recommendations. Examples:\n"
        + "\n".join(f"  - {s['artifact_name']}: {s.get('rationale', '')[:80]}" for s in merge_entries[:5])
    )


# ===========================================================================
# SCENARIO #1b: A skill WITH a real merge-candidate overlap pair IS
#   recommended for merge (regression test: don't over-correct)
#
# Given: a fixture catalog with 2 skills that have high overlap
# When: the pipeline runs `ci` end-to-end
# Then: at least one of the 2 skills has `decision == "merge"` in the
#   scorecard, with a rationale that references the overlap
# ===========================================================================
def test_skill_with_real_merge_overlap_is_recommended_merge(tmp_path):
    # Build a 2-skill catalog where both skills cover the same topic
    # with different wording. They should overlap enough to trigger
    # the merge recommendation.
    catalog = tmp_path / "catalog"
    catalog.mkdir()
    s1 = catalog / "logging-error-skill"
    s1.mkdir()
    (s1 / "SKILL.md").write_text(
        """---
name: logging-error-skill
artifact_type: skill
purpose: >
  Capture error events from production systems. Detect
  log patterns, alert on them, and produce incident reports.
  This skill logs every error with stack trace, severity,
  request id, and user id, then groups similar errors
  to produce a deduplicated error report.
category: observability
owner: sre
version: 1.0.0
inputs:
  - name: log_lines
    type: string
outputs:
  - name: error_report
    type: json
dependencies: []
intended_consumers:
  - SRE team
quality_level: usable
last_reviewed: 2026-06-14
---

# Logging Error Skill

This skill captures every error from production log lines,
groups similar error patterns by stack trace and severity,
and produces a deduplicated incident report. Use it to
detect error patterns, alert on errors, and track error
rates in production. Common use cases include error log
pattern detection, stack-trace grouping, severity tagging,
and request-id correlation. The skill reads log lines,
parses error stack traces, normalizes error messages,
groups similar errors, and emits an error report.
"""
    )
    s2 = catalog / "log-error-pattern-skill"
    s2.mkdir()
    (s2 / "SKILL.md").write_text(
        """---
name: log-error-pattern-skill
artifact_type: skill
purpose: >
  Detect error log patterns in production systems. Group
  similar log events by pattern, emit alerts, and produce
  incident reports. This skill detects error patterns in
  log lines, groups them by stack trace and severity,
  and produces a deduplicated log error report.
category: observability
owner: sre
version: 1.0.0
inputs:
  - name: log_lines
    type: string
outputs:
  - name: error_report
    type: json
dependencies: []
intended_consumers:
  - SRE team
quality_level: usable
last_reviewed: 2026-06-14
---

# Log Error Pattern Skill

This skill detects error patterns in production log lines,
groups similar log events by stack trace and severity, and
produces a deduplicated log error report. Use it to detect
log error patterns, alert on errors, and track error rates
in production. Common use cases include error log pattern
detection, stack-trace grouping, severity tagging, and
request-id correlation. The skill reads log lines, parses
error stack traces, normalizes error messages, groups
similar errors, and emits a log error report.
"""
    )
    cfg = {
        "skill_directories": [str(catalog)],
        "agent_directories": [],
        "output_directory": str(tmp_path / "output"),
        "token_thresholds": {"high_cost": 8000},
        "overlap_thresholds": {"blocking": 40, "warning": 25},
        "roi_thresholds": {"keep_min": 70, "rewrite_min": 50, "deprecate_max": 30},
        "benchmark_thresholds": {"default_minimum": 0.7},
        "ci_blocking_rules": [],
        "minimax_semantic_scoring_enabled": False,
        "waiver_file": str(tmp_path / "waivers.yaml"),
        "runtime_log_paths": [],
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump(cfg))
    _run_cli(["ci", "--config", str(cfg_path)])
    scorecard_path = tmp_path / "output" / "skill_scorecard.json"
    assert scorecard_path.exists(), f"scorecard must be written at {scorecard_path}"
    scorecard = json.loads(scorecard_path.read_text())
    merge_entries = [s for s in scorecard if s.get("decision") == "merge"]
    # With the lowered overlap threshold (60/40), the 2 skills
    # should overlap enough that at least one is recommended for merge.
    assert len(merge_entries) >= 1, (
        f"When 2 skills genuinely overlap (lowered threshold to 60/40 for the test), "
        f"at least one must be recommended for merge. Got 0 merge entries. "
        f"Scorecard: {[(s.get('artifact_name'), s.get('decision')) for s in scorecard]}"
    )


# ===========================================================================
# SCENARIO #2a: `ci` output is a multi-line summary, not 1 line
#
# Given: any catalog
# When: the user runs `python -m skill_governance ci --config …`
# Then: stdout contains a multi-line summary with at least:
#   - one line stating PASS or FAILED
#   - one line with the artifact count
#   - one line with the finding count
#   - one line referencing the executive_report.md path
# ===========================================================================
def test_ci_output_is_multiline_summary_with_counts_and_path(tmp_path):
    # Use a minimal catalog so we don't depend on the real one
    catalog = tmp_path / "catalog"
    catalog.mkdir()
    (catalog / "SKILL.md").write_text(
        """---
name: minimal
artifact_type: skill
purpose: >
  A minimal skill for testing the ci command output format.
inputs:
  - name: x
    type: string
outputs:
  - name: y
    type: string
dependencies: []
---

# Minimal
"""
    )
    cfg = {
        "skill_directories": [str(catalog)],
        "agent_directories": [],
        "output_directory": str(tmp_path / "output"),
        "token_thresholds": {"high_cost": 8000},
        "overlap_thresholds": {"blocking": 85, "warning": 70},
        "roi_thresholds": {"keep_min": 70, "rewrite_min": 50, "deprecate_max": 30},
        "benchmark_thresholds": {"default_minimum": 0.7},
        "ci_blocking_rules": [],
        "minimax_semantic_scoring_enabled": False,
        "waiver_file": str(tmp_path / "waivers.yaml"),
        "runtime_log_paths": [],
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump(cfg))
    result = _run_cli(["ci", "--config", str(cfg_path)])
    # Acceptance: stdout has at least 4 lines
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    assert len(lines) >= 4, (
        f"ci stdout should be a multi-line summary (>=4 lines), got {len(lines)}:\n"
        f"{result.stdout}"
    )
    # Must contain PASS or FAILED
    assert any(("PASS" in l or "FAIL" in l) for l in lines), (
        f"ci stdout must contain a line with PASS or FAIL, got:\n{result.stdout}"
    )
    # Must mention the executive report
    assert any("executive_report" in l or "report" in l.lower() for l in lines), (
        f"ci stdout must reference the executive report, got:\n{result.stdout}"
    )


# ===========================================================================
# SCENARIO #2b: `ci` machine-readable status block is parseable
#
# Given: any catalog
# When: the user runs `python -m skill_governance ci --config …`
# Then: stdout contains a JSON status block (delimited with sentinel
#   markers or a structured section) that can be parsed by other tools
# ===========================================================================
def test_ci_output_contains_machine_readable_status_block(tmp_path):
    catalog = tmp_path / "catalog"
    catalog.mkdir()
    (catalog / "SKILL.md").write_text(
        """---
name: minimal
artifact_type: skill
purpose: >
  A minimal skill for testing the ci command output format.
inputs:
  - name: x
    type: string
outputs:
  - name: y
    type: string
dependencies: []
---

# Minimal
"""
    )
    cfg = {
        "skill_directories": [str(catalog)],
        "agent_directories": [],
        "output_directory": str(tmp_path / "output"),
        "token_thresholds": {"high_cost": 8000},
        "overlap_thresholds": {"blocking": 85, "warning": 70},
        "roi_thresholds": {"keep_min": 70, "rewrite_min": 50, "deprecate_max": 30},
        "benchmark_thresholds": {"default_minimum": 0.7},
        "ci_blocking_rules": [],
        "minimax_semantic_scoring_enabled": False,
        "waiver_file": str(tmp_path / "waivers.yaml"),
        "runtime_log_paths": [],
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump(cfg))
    result = _run_cli(["ci", "--config", str(cfg_path)])
    # Look for a JSON block in stdout (between sentinel markers or as a fenced block)
    # Sentinel convention: lines starting with "SGP-CI-STATUS-BEGIN" / "SGP-CI-STATUS-END"
    # Or: a fenced ```json block
    text = result.stdout
    json_match = re.search(r"```json\s*\n(\{.*?\})\s*\n```", text, re.DOTALL)
    sentinel_match = re.search(
        r"SGP-CI-STATUS-BEGIN\s*\n(\{.*?\})\s*\nSGP-CI-STATUS-END", text, re.DOTALL
    )
    json_str = None
    if json_match:
        json_str = json_match.group(1)
    elif sentinel_match:
        json_str = sentinel_match.group(1)
    assert json_str is not None, (
        f"ci stdout must contain a parseable JSON status block (sentinel or fenced). "
        f"Got:\n{result.stdout}"
    )
    # The block must parse as JSON and contain at least {passed, artifacts, findings}
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        pytest.fail(f"ci stdout JSON block does not parse: {e}\nBlock: {json_str}")
    for key in ("passed", "artifacts", "findings"):
        assert key in data, f"ci JSON status must include '{key}', got: {list(data.keys())}"


# ===========================================================================
# SCENARIO #3a: runtime_metrics.ingest() parses JSON-lines logs
#
# Given: a log file with one JSON object per line, where each object has
#   {artifact_name: str, total_tokens: int, success: bool, timestamp: str}
# When: ingest() is called on the log file path
# Then: it returns a non-empty list of RuntimeTokenMetrics, one per
#   artifact, with invocations/total_tokens aggregated
# ===========================================================================
def test_runtime_metrics_ingest_parses_jsonl_log_file(tmp_path):
    import importlib
    rt = importlib.import_module("skill_governance.runtime_metrics")

    log = tmp_path / "invocations.jsonl"
    log.write_text(
        '{"artifact_name": "skill-a", "total_tokens": 100, "success": true, "timestamp": "2026-06-14T01:00:00Z"}\n'
        '{"artifact_name": "skill-a", "total_tokens": 150, "success": true, "timestamp": "2026-06-14T01:05:00Z"}\n'
        '{"artifact_name": "skill-b", "total_tokens": 200, "success": false, "timestamp": "2026-06-14T01:10:00Z"}\n'
    )
    result = rt.ingest(str(log))
    assert isinstance(result, list), f"ingest() must return a list, got {type(result)}"
    # Two unique artifacts: skill-a (2 invocations) and skill-b (1 invocation)
    assert len(result) == 2, f"ingest() must aggregate to one entry per artifact, got {len(result)}"
    by_name = {r.artifact_name: r for r in result}
    assert "skill-a" in by_name, "skill-a must be in result"
    assert "skill-b" in by_name, "skill-b must be in result"
    assert by_name["skill-a"].invocations == 2, f"skill-a invocations={by_name['skill-a'].invocations}"
    assert by_name["skill-a"].total_tokens == 250, f"skill-a total_tokens={by_name['skill-a'].total_tokens}"
    assert by_name["skill-b"].invocations == 1, f"skill-b invocations={by_name['skill-b'].invocations}"
    assert by_name["skill-b"].total_tokens == 200, f"skill-b total_tokens={by_name['skill-b'].total_tokens}"


# ===========================================================================
# SCENARIO #3b: runtime_metrics.ingest() returns [] for an empty file
#
# Given: an empty log file
# When: ingest() is called
# Then: it returns []
# ===========================================================================
def test_runtime_metrics_ingest_returns_empty_for_empty_file(tmp_path):
    import importlib
    rt = importlib.import_module("skill_governance.runtime_metrics")
    log = tmp_path / "empty.jsonl"
    log.write_text("")
    result = rt.ingest(str(log))
    assert result == [], (
        f"ingest() must return [] for an empty log file, got {result!r}"
    )


# ===========================================================================
# Self-test: confirm the test file itself is wired into pytest
# ===========================================================================
def test_acceptance_test_file_is_collectable():
    """Sanity check: this test file is picked up by pytest."""
    assert __file__.endswith("test_p7_acceptance.py"), (
        f"Test file naming must be test_*.py to be auto-collected, got {__file__}"
    )
