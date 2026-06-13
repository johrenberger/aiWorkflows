"""Tests for the CLI end-to-end (Phase 1 gate)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _make_config(tmp_path: Path) -> Path:
    """Generate a config pointing at the fixtures."""
    cfg = {
        "skill_directories": [str(FIXTURES)],
        "agent_directories": [str(FIXTURES)],
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
    p = tmp_path / "config.yaml"
    import yaml
    p.write_text(yaml.dump(cfg))
    return p


def test_scan_creates_inventory(tmp_path):
    """The scan command produces skill_inventory.json with at least 5 entries."""
    config = _make_config(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "skill_governance.cli", "scan", "--config", str(config)],
        capture_output=True, text=True, cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, result.stderr
    inv_path = tmp_path / "output" / "skill_inventory.json"
    assert inv_path.exists()
    data = json.loads(inv_path.read_text())
    assert len(data) >= 5
    for entry in data:
        assert "name" in entry
        assert "artifact_type" in entry
        assert "content_hash" in entry


def test_validate_runs_and_writes_findings(tmp_path):
    """The validate command produces governance_findings.json."""
    config = _make_config(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "skill_governance.cli", "validate", "--config", str(config)],
        capture_output=True, text=True, cwd=Path(__file__).parent.parent,
    )
    # exit 2 means blocking findings were found (expected for our fixture set)
    assert result.returncode in (0, 2)
    findings_path = tmp_path / "output" / "governance_findings.json"
    assert findings_path.exists()
    findings = json.loads(findings_path.read_text())
    # We have 2 intentionally bad fixtures
    blocking = [f for f in findings if f["severity"] == "blocking"]
    assert len(blocking) >= 2  # missing-metadata + vague-output


def test_ci_exits_nonzero_on_blocking(tmp_path):
    """CI mode exits 1 if there are blocking findings (waivers not applied)."""
    config = _make_config(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "skill_governance.cli", "ci", "--config", str(config)],
        capture_output=True, text=True, cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 1
    # Reports should still be written even on CI failure
    assert (tmp_path / "output" / "executive_report.md").exists()
    assert (tmp_path / "output" / "technical_report.md").exists()


def test_report_renders_executive_summary(tmp_path):
    """The report command produces an executive_report.md with key fields."""
    config = _make_config(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "skill_governance.cli", "report", "--config", str(config)],
        capture_output=True, text=True, cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, result.stderr
    out = (tmp_path / "output" / "executive_report.md").read_text()
    assert "Executive Report" in out
    assert "Health score" in out
    assert "Total skills" in out
