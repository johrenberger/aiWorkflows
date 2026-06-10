from __future__ import annotations

from test_factory.models import RiskScoreRecord
from test_factory.validators.coverage_gate import coverage_improved


def test_coverage_gate_requires_strict_line_improvement():
    before = RiskScoreRecord(path="package/foo.py", module="package", line_coverage=50.0, branch_coverage=50.0)
    improved, reason = coverage_improved(before, 50.0, 100.0)
    assert improved is False
    assert reason == "line coverage did not improve"


def test_coverage_gate_requires_branch_evidence_when_baseline_has_branch_coverage():
    before = RiskScoreRecord(path="package/foo.py", module="package", line_coverage=50.0, branch_coverage=50.0)
    improved, reason = coverage_improved(before, 100.0, None)
    assert improved is False
    assert reason == "branch coverage evidence missing after validation"
