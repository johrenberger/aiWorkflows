"""Story 024: surface zero-coverage files as a separate artifact and CLI flag.

These tests verify the behavior of:
  1. `is_zero_coverage()` helper in `analyzers.risk_scorer`
  2. `queue()` annotates every item with `zero_coverage: bool`
  3. `zero_coverage_queue.json` is written and sorted by risk_score desc
  4. `queue(zero_coverage_only=True)` returns only zero-coverage items
  5. The CLI `--zero-coverage-only` flag on `queue` and `run`
  6. `final_report.md` includes a "Zero-Coverage Files" section

The queue() and report() end-to-end tests build a synthetic
risk_scores.json with three records (zero / low / high coverage)
plus a fourth zero-coverage record with the highest risk_score,
to verify sort order and filtering.
"""
from __future__ import annotations

import json
import shutil
import sys
import subprocess
from pathlib import Path

import pytest

from test_factory.analyzers.risk_scorer import is_zero_coverage
from test_factory.orchestrator import TestFactoryOrchestrator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_REPO = PROJECT_ROOT / "tests" / "fixtures" / "sample-repo"


# --------------------------------------------------------------------------
# is_zero_coverage() helper
# --------------------------------------------------------------------------

def test_is_zero_coverage_returns_true_for_zero_zero():
    assert is_zero_coverage(0.0) is True


def test_is_zero_coverage_returns_true_for_zero_zero_with_none_branch():
    assert is_zero_coverage(0.0, None) is True


def test_is_zero_coverage_returns_true_for_zero_zero_with_zero_branch():
    assert is_zero_coverage(0.0, 0.0) is True


def test_is_zero_coverage_returns_false_for_nonzero_line():
    assert is_zero_coverage(50.0) is False
    assert is_zero_coverage(50.0, 0.0) is False  # nonzero line always wins
    assert is_zero_coverage(0.5) is False


def test_is_zero_coverage_returns_false_for_nonzero_branch_with_zero_line():
    """A line_coverage of 0.0 but branch_coverage of 50% is treated
    as nonzero (some coverage was reported). This is the edge case
    where JaCoCo reports branch data even when no lines were hit —
    rare, but we want to flag those as 'has some coverage' so they
    show up in the regular queue, not the zero-coverage one."""
    assert is_zero_coverage(0.0, 50.0) is False


# --------------------------------------------------------------------------
# queue() annotation + zero_coverage_queue.json artifact
# --------------------------------------------------------------------------

def _build_fake_risk_scores(artifacts_dir: Path) -> None:
    """Write a risk_scores.json with four records:
      - package/a.java: zero coverage, risk_score 100
      - package/b.java: low coverage (30%), risk_score 200
      - package/c.java: high coverage (95%), risk_score 300
      - package/d.java: zero coverage, risk_score 900 (highest)
    Plus a high-coverage record to ensure the regular queue still
    contains it.
    """
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    risk_scores = [
        {
            "path": "package/a.py",
            "module": "package",
            "line_coverage": 0.0,
            "branch_coverage": None,
            "coverage_gap": 180.0,
            "risk_score": 100.0,
            "complexity": 1.0,
            "public_api_exposure": 0.0,
            "data_or_security_sensitivity": 0.0,
        },
        {
            "path": "package/b.py",
            "module": "package",
            "line_coverage": 30.0,
            "branch_coverage": 25.0,
            "coverage_gap": 90.0 + 65.0,
            "risk_score": 200.0,
            "complexity": 1.0,
            "public_api_exposure": 0.0,
            "data_or_security_sensitivity": 0.0,
        },
        {
            "path": "package/c.py",
            "module": "package",
            "line_coverage": 95.0,
            "branch_coverage": 90.0,
            "coverage_gap": 0.0,
            "risk_score": 300.0,
            "complexity": 1.0,
            "public_api_exposure": 0.0,
            "data_or_security_sensitivity": 0.0,
        },
        {
            "path": "package/d.py",
            "module": "package",
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "coverage_gap": 180.0,
            "risk_score": 900.0,
            "complexity": 1.0,
            "public_api_exposure": 0.0,
            "data_or_security_sensitivity": 0.0,
        },
    ]
    (artifacts_dir / "risk_scores.json").write_text(json.dumps(risk_scores), encoding="utf-8")


def _make_inventory(artifacts_dir: Path) -> None:
    """Write a minimal repo_inventory.json so queue() can run without
    a real repo scan. The four files need to be present in the
    inventory for _module_matches_scope to let them through, but
    queue() doesn't actually open the source files."""
    inventory = []
    for letter in ["a", "b", "c", "d"]:
        inventory.append({
            "path": f"package/{letter}.py",
            "language": "python",
            "module": "package",
            "size": 100,
            "sha256": "0" * 64,
            "is_test": False,
            "is_generated": False,
            "is_excluded": False,
            "exclusion_reason": "",
        })
    (artifacts_dir / "repo_inventory.json").write_text(json.dumps(inventory), encoding="utf-8")


def _init_orchestrator_with_fake_risk_scores(tmp_path: Path) -> TestFactoryOrchestrator:
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    out = tmp_path / "analysis-artifacts"
    out.mkdir()
    _build_fake_risk_scores(out)
    _make_inventory(out)
    # Touch other artifacts queue() might load
    (out / "coverage_baseline.json").write_text("[]", encoding="utf-8")
    return TestFactoryOrchestrator(str(repo), str(out))


def test_queue_annotates_every_item_with_zero_coverage_flag(tmp_path):
    """Scenario 1: every queue item gets a `zero_coverage: bool` field."""
    orch = _init_orchestrator_with_fake_risk_scores(tmp_path)
    try:
        queue = orch.queue()
        paths = {item["path"]: item for item in queue}
        assert paths["package/a.py"]["zero_coverage"] is True
        assert paths["package/b.py"]["zero_coverage"] is False
        assert paths["package/c.py"]["zero_coverage"] is False
        assert paths["package/d.py"]["zero_coverage"] is True
    finally:
        orch.close()


def test_zero_coverage_queue_artifact_filtered_and_sorted_by_risk_score(tmp_path):
    """Scenario 2: zero_coverage_queue.json contains only the
    measured-zero subset of zero-coverage items (story 031).
    Sorted by risk_score desc (path is the deterministic tiebreak).
    In the test fixture, a.py is unmeasurable (branch_coverage=None)
    and d.py is measured-zero (branch_coverage=0.0). Only d.py is
    in zero_coverage_queue.json after story 031.
    """
    orch = _init_orchestrator_with_fake_risk_scores(tmp_path)
    try:
        orch.queue()
        artifact = tmp_path / "analysis-artifacts" / "zero_coverage_queue.json"
        assert artifact.exists(), "zero_coverage_queue.json should be written"
        items = json.loads(artifact.read_text(encoding="utf-8"))
        # Story 031: only the measured-zero subset. In the test
        # fixture, that's just d.py (a.py is unmeasurable).
        assert len(items) == 1, f"expected 1 measured-zero item, got {len(items)}: {[i['path'] for i in items]}"
        assert items[0]["path"] == "package/d.py"
        # Verify the coverage_status annotation is set.
        assert items[0]["coverage_status"] == "measured_zero"
    finally:
        orch.close()


def test_queue_with_zero_coverage_only_filter_returns_only_zero_coverage_items(tmp_path):
    """Scenario 3: orchestrator.queue(zero_coverage_only=True) returns
    only the MEASURED-zero subset (same content as the artifact).
    Story 031: previously this returned all `zero_coverage=True` items
    including unmeasurable; now it returns only measured-zero.
    """
    orch = _init_orchestrator_with_fake_risk_scores(tmp_path)
    try:
        result = orch.queue(zero_coverage_only=True)
        assert len(result) == 1
        # The legacy `zero_coverage` bool is still True (backward compat)
        assert all(item.get("zero_coverage") is True for item in result)
        # But the new `coverage_status` is specifically "measured_zero"
        assert all(item["coverage_status"] == "measured_zero" for item in result)
        assert all(item["line_coverage"] == 0.0 for item in result)
    finally:
        orch.close()


def test_test_gap_queue_artifact_unchanged_when_zero_coverage_only(tmp_path):
    """Scenario 3 (regression): --zero-coverage-only only filters the
    *return value* of queue(), it does not mutate the on-disk
    test_gap_queue.json artifact. Users who run a normal queue
    later should still see all 4 items."""
    orch = _init_orchestrator_with_fake_risk_scores(tmp_path)
    try:
        orch.queue(zero_coverage_only=True)
        full = json.loads(
            (tmp_path / "analysis-artifacts" / "test_gap_queue.json").read_text(encoding="utf-8")
        )
        assert len(full) == 4, f"test_gap_queue.json should still have 4 items, got {len(full)}"
    finally:
        orch.close()


# --------------------------------------------------------------------------
# CLI integration: --zero-coverage-only
# --------------------------------------------------------------------------

def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "test_factory.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_cli_queue_zero_coverage_only_filters_stdout(tmp_path):
    """Scenario 3 (CLI): test-factory queue --zero-coverage-only
    returns only the MEASURED-zero items in its stdout JSON output.
    (Story 031: unmeasurable items now have a separate
    --unmeasurable-only flag.)
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    out = tmp_path / "analysis-artifacts"
    out.mkdir()
    _build_fake_risk_scores(out)
    _make_inventory(out)
    (out / "coverage_baseline.json").write_text("[]", encoding="utf-8")

    result = _run_cli(
        "queue", "--repo", str(repo), "--out", str(out),
        "--zero-coverage-only", cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    items = json.loads(result.stdout)
    # Story 031: only measured-zero, not unmeasurable. In the test
    # fixture, that's just d.py.
    assert len(items) == 1
    assert items[0]["path"] == "package/d.py"
    assert items[0]["coverage_status"] == "measured_zero"


def test_cli_run_zero_coverage_only_writes_filtered_workitems(tmp_path):
    """Scenario 5: test-factory run --zero-coverage-only writes
    zero_coverage_queue.json and filters the workitems output.

    On the sample-repo fixture, the real coverage gives 50% line
    coverage to the 3 source files, so the zero-coverage queue is
    empty in that scenario. This test instead verifies the
    *mechanism*: that the flag flows through run() and the
    artifact is written (even if empty).
    """
    repo = tmp_path / "sample-repo"
    shutil.copytree(FIXTURE_REPO, repo)
    out = tmp_path / "analysis-artifacts"

    run_result = _run_cli(
        "run", "--repo", str(repo), "--out", str(out),
        "--zero-coverage-only", cwd=PROJECT_ROOT,
    )
    assert run_result.returncode == 0, f"run failed: {run_result.stderr}"

    # The artifact must be written even when the zero-coverage
    # subset is empty (so downstream consumers can rely on the
    # file existing).
    zero_q_path = out / "zero_coverage_queue.json"
    assert zero_q_path.exists(), "zero_coverage_queue.json should be written by run()"
    zero_q = json.loads(zero_q_path.read_text(encoding="utf-8"))
    # On sample-repo, all files have 50% line coverage, so the
    # zero-coverage queue is empty.
    assert zero_q == [], (
        f"expected zero_coverage_queue to be empty for sample-repo "
        f"(all files at 50%), got {zero_q}"
    )


# --------------------------------------------------------------------------
# final_report.md: Zero-Coverage Files section
# --------------------------------------------------------------------------

def test_final_report_includes_zero_coverage_section(tmp_path):
    """Scenario 4: final_report.md has a 'Zero-Coverage Files' section
    with the count and the top 10 zero-coverage items by risk_score."""
    from test_factory.reports.markdown_report import render_final_report

    out = tmp_path / "analysis-artifacts"
    out.mkdir()
    # Minimal artifacts that render_final_report() will read
    (out / "repo_inventory.json").write_text("[]", encoding="utf-8")
    (out / "coverage_baseline.json").write_text("[]", encoding="utf-8")
    (out / "exclusions.json").write_text("[]", encoding="utf-8")
    (out / "language_stack.json").write_text("{}", encoding="utf-8")
    (out / "module_graph.json").write_text("{}", encoding="utf-8")
    (out / "risk_weighted_coverage.json").write_text("{}", encoding="utf-8")
    (out / "component_test_candidates.json").write_text("[]", encoding="utf-8")
    (out / "adapter_detections.json").write_text("[]", encoding="utf-8")
    (out / "commands_discovered.json").write_text("[]", encoding="utf-8")
    # Two items in test_gap_queue, two in zero_coverage_queue
    test_gap = [
        {"path": "package/a.py", "line_coverage": 0.0, "branch_coverage": None,
         "priority": 18000.0, "risk_score": 100.0, "coverage_gap": 180.0},
        {"path": "package/d.py", "line_coverage": 0.0, "branch_coverage": 0.0,
         "priority": 162000.0, "risk_score": 900.0, "coverage_gap": 180.0},
    ]
    zero_q = [test_gap[1], test_gap[0]]  # already sorted by risk_score desc
    (out / "test_gap_queue.json").write_text(json.dumps(test_gap), encoding="utf-8")
    (out / "zero_coverage_queue.json").write_text(json.dumps(zero_q), encoding="utf-8")

    md = render_final_report(out)
    assert "## Zero-Coverage Files" in md, (
        f"final_report.md missing Zero-Coverage Files section.\nGot:\n{md}"
    )
    assert "Count: `2`" in md
    # The top 10 by risk_score: d (900) first, then a (100)
    assert "package/d.py" in md
    assert "package/a.py" in md
    # d.py's risk_score should appear before a.py's, but we have to
    # look only inside the Zero-Coverage section (otherwise other
    # sections may mention them in arbitrary order).
    zero_section = md.split("## Zero-Coverage Files")[1].split("## ")[0]
    d_idx = zero_section.index("package/d.py")
    a_idx = zero_section.index("package/a.py")
    assert d_idx < a_idx, (
        f"d.py (rs=900) should appear before a.py (rs=100) in the zero-coverage section.\n"
        f"Got section:\n{zero_section}"
    )
