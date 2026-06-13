"""Story 031: split unmeasurable from measurable-zero in zero-coverage queue.

The story 024 contract was: 'zero_coverage' bool annotation on every
queue item, where True means "line=0 and (branch=None or branch=0)".
This conflated two different conditions:
  - measured_zero: line=0, branch=0 (analyzed, no tests hit)
  - unmeasurable: line=0, branch=None (analysis didn't run)

Story 031 introduces a three-state `coverage_status` field that
distinguishes them, and a separate `unmeasurable_queue.json`
artifact. This file tests the new helper and the new artifact.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from test_factory.analyzers.risk_scorer import (
    COVERAGE_STATUS_MEASURED_NONZERO,
    COVERAGE_STATUS_MEASURED_ZERO,
    COVERAGE_STATUS_UNMEASURABLE,
    coverage_status,
    is_zero_coverage,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from test_factory.orchestrator import TestFactoryOrchestrator  # noqa: E402


# --------------------------------------------------------------------------
# coverage_status() helper
# --------------------------------------------------------------------------

def test_coverage_status_measured_zero_for_line_zero_branch_zero():
    assert coverage_status(0.0, 0.0) == COVERAGE_STATUS_MEASURED_ZERO


def test_coverage_status_unmeasurable_for_line_zero_branch_none():
    assert coverage_status(0.0, None) == COVERAGE_STATUS_UNMEASURABLE


def test_coverage_status_measured_nonzero_for_nonzero_line():
    assert coverage_status(50.0, 25.0) == COVERAGE_STATUS_MEASURED_NONZERO
    assert coverage_status(0.001, 0.0) == COVERAGE_STATUS_MEASURED_NONZERO


def test_coverage_status_measured_nonzero_for_line_zero_with_nonzero_branch():
    """Edge case: line=0 but branch>0. Possible if a class has no
    line-instrumented code but has analyzable branches (e.g.
    abstract methods or constant-only fields). Treat as nonzero
    since SOME measurement happened."""
    assert coverage_status(0.0, 50.0) == COVERAGE_STATUS_MEASURED_NONZERO


def test_coverage_status_distinguishes_measured_zero_from_unmeasurable():
    """The KEY behavior of story 031: a class that has
    line=0, branch=0 is NOT the same as a class with
    line=0, branch=None. is_zero_coverage() returns True for
    both (preserved for backward compat); coverage_status()
    returns different strings.
    """
    measured = coverage_status(0.0, 0.0)
    unmeasurable = coverage_status(0.0, None)
    assert measured != unmeasurable
    assert measured == "measured_zero"
    assert unmeasurable == "unmeasurable"
    # And the legacy is_zero_coverage returns True for both:
    assert is_zero_coverage(0.0, 0.0) is True
    assert is_zero_coverage(0.0, None) is True


# --------------------------------------------------------------------------
# queue() artifact split
# --------------------------------------------------------------------------

def _build_fake_risk_scores_split(artifacts_dir: Path) -> None:
    """Same fixture as test_024 but with a third item: e (measured_nonzero
    but line=0 with branch>0). And another for the pure nonzero case.
    """
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    risk_scores = [
        {
            "path": "package/a.py",  # unmeasurable
            "module": "package",
            "line_coverage": 0.0,
            "branch_coverage": None,
            "coverage_gap": 180.0,
            "risk_score": 100.0,
            "complexity": 1.0,
        },
        {
            "path": "package/b.py",  # low coverage
            "module": "package",
            "line_coverage": 30.0,
            "branch_coverage": 25.0,
            "coverage_gap": 155.0,
            "risk_score": 200.0,
            "complexity": 1.0,
        },
        {
            "path": "package/d.py",  # measured zero
            "module": "package",
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "coverage_gap": 180.0,
            "risk_score": 900.0,
            "complexity": 1.0,
        },
        {
            "path": "package/e.py",  # nonzero
            "module": "package",
            "line_coverage": 95.0,
            "branch_coverage": 90.0,
            "coverage_gap": 0.0,
            "risk_score": 300.0,
            "complexity": 1.0,
        },
    ]
    (artifacts_dir / "risk_scores.json").write_text(json.dumps(risk_scores), encoding="utf-8")
    inventory = [
        {
            "path": f"package/{letter}.py",
            "language": "python",
            "module": "package",
            "size": 100,
            "sha256": "0" * 64,
            "is_test": False,
            "is_generated": False,
            "is_excluded": False,
            "exclusion_reason": "",
        }
        for letter in ["a", "b", "d", "e"]
    ]
    (artifacts_dir / "repo_inventory.json").write_text(json.dumps(inventory), encoding="utf-8")


def _init_orchestrator_split(tmp_path: Path) -> TestFactoryOrchestrator:
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    out = tmp_path / "analysis-artifacts"
    out.mkdir()
    _build_fake_risk_scores_split(out)
    (out / "coverage_baseline.json").write_text("[]", encoding="utf-8")
    return TestFactoryOrchestrator(str(repo), str(out))


def test_zero_coverage_queue_contains_only_measured_zero(tmp_path):
    """Story 031: zero_coverage_queue.json contains only items
    where coverage_status == 'measured_zero'."""
    orch = _init_orchestrator_split(tmp_path)
    try:
        orch.queue()
        items = json.loads((tmp_path / "analysis-artifacts" / "zero_coverage_queue.json").read_text())
        assert len(items) == 1
        assert items[0]["path"] == "package/d.py"
        assert items[0]["coverage_status"] == "measured_zero"
    finally:
        orch.close()


def test_unmeasurable_queue_contains_only_unmeasurable(tmp_path):
    """Story 031: unmeasurable_queue.json contains only items
    where coverage_status == 'unmeasurable'."""
    orch = _init_orchestrator_split(tmp_path)
    try:
        orch.queue()
        items = json.loads((tmp_path / "analysis-artifacts" / "unmeasurable_queue.json").read_text())
        assert len(items) == 1
        assert items[0]["path"] == "package/a.py"
        assert items[0]["coverage_status"] == "unmeasurable"
    finally:
        orch.close()


def test_measured_nonzero_items_are_in_neither_queue(tmp_path):
    """Story 031: items with coverage_status='measured_nonzero'
    are in test_gap_queue.json (the regular queue) but not in
    either of the two zero-coverage artifacts.
    """
    orch = _init_orchestrator_split(tmp_path)
    try:
        orch.queue()
        zero_q = json.loads((tmp_path / "analysis-artifacts" / "zero_coverage_queue.json").read_text())
        unme_q = json.loads((tmp_path / "analysis-artifacts" / "unmeasurable_queue.json").read_text())
        zero_paths = {item["path"] for item in zero_q}
        unme_paths = {item["path"] for item in unme_q}
        # e.py (95% line, 90% branch) is nonzero and in neither
        assert "package/e.py" not in zero_paths
        assert "package/e.py" not in unme_paths
        # b.py (30% line) is also nonzero
        assert "package/b.py" not in zero_paths
        assert "package/b.py" not in unme_paths
    finally:
        orch.close()


def test_each_queue_item_has_coverage_status_annotation(tmp_path):
    """Story 031: every item in the regular test_gap_queue.json
    should have a coverage_status annotation (in addition to the
    legacy zero_coverage bool)."""
    orch = _init_orchestrator_split(tmp_path)
    try:
        queue = orch.queue()
        for item in queue:
            assert "coverage_status" in item
            assert item["coverage_status"] in (
                "measured_zero",
                "unmeasurable",
                "measured_nonzero",
            )
            # The legacy `zero_coverage` bool is still set.
            assert "zero_coverage" in item
            assert isinstance(item["zero_coverage"], bool)
    finally:
        orch.close()


# --------------------------------------------------------------------------
# CLI --unmeasurable-only
# --------------------------------------------------------------------------

def _run_cli(*args, cwd: Path) -> subprocess.CompletedProcess:
    """Run the test-factory CLI in a subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "test_factory.cli", *args],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=cwd,
    )


def test_cli_queue_unmeasurable_only_filters_stdout(tmp_path):
    """Story 031: test-factory queue --unmeasurable-only returns
    only the unmeasurable items in stdout."""
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    out = tmp_path / "analysis-artifacts"
    out.mkdir()
    _build_fake_risk_scores_split(out)
    (out / "coverage_baseline.json").write_text("[]", encoding="utf-8")

    result = _run_cli(
        "queue", "--repo", str(repo), "--out", str(out),
        "--unmeasurable-only", cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    items = json.loads(result.stdout)
    assert len(items) == 1
    assert items[0]["path"] == "package/a.py"
    assert items[0]["coverage_status"] == "unmeasurable"
