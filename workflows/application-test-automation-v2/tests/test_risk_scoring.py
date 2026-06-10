from __future__ import annotations

from test_factory.analyzers.risk_scorer import score_file, weighted_index
from test_factory.models import CoverageRecord


def test_risk_scoring_uses_gap_formula():
    coverage = CoverageRecord(path="src/foo.py", line_coverage=80.0, branch_coverage=70.0)
    score = score_file("src/foo.py", "src", coverage, complexity=2, churn=3, public_api_exposure=1, dependency_fan_in=1, defect_history=1, data_or_security_sensitivity=1)
    assert score.coverage_gap == 30.0
    assert score.risk_score == 2 * 3 + 3 * 2 + 1 * 5 + 1 * 3 + 1 * 4 + 1 * 5 + 30 * 4


def test_weighted_index_prefers_line_coverage_by_default():
    first = score_file("a.py", "m", CoverageRecord(path="a.py", line_coverage=90.0))
    second = score_file("b.py", "m", CoverageRecord(path="b.py", line_coverage=50.0))
    assert weighted_index([first, second]) <= 90.0
