from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..models import CoverageRecord, RiskScoreRecord


def is_zero_coverage(
    line_coverage: float,
    branch_coverage: float | None = None,
) -> bool:
    """True when a file has *no* test coverage at all.

    A file is "zero coverage" when:
      - `line_coverage` is 0.0 (no lines hit by tests), AND
      - `branch_coverage` is either None (no branch data reported) or
        0.0 (branch data was reported but no branches hit).

    This matches the user-visible concept of "completely untested":
    the file may have been analyzed (line_coverage is a number, not
    missing) but no test exercised it, OR the file wasn't analyzed
    at all (line_coverage defaults to 0.0 in that case — see
    `score_file`). Both cases are surfaced in the zero-coverage
    queue.

    Story 024: previously zero-coverage files were mixed in with
    low-coverage files in `test_gap_queue.json`; the user had to
    filter manually. This helper powers a `zero_coverage: bool`
    annotation on every queue item and a separate
    `zero_coverage_queue.json` artifact.
    """
    if line_coverage != 0.0:
        return False
    if branch_coverage is None:
        return True
    return branch_coverage == 0.0


def score_file(
    path: str,
    module: str,
    coverage: CoverageRecord | None = None,
    *,
    language: str = "unknown",
    complexity: float = 0.0,
    churn: float = 0.0,
    public_api_exposure: float = 0.0,
    dependency_fan_in: float = 0.0,
    defect_history: float = 0.0,
    data_or_security_sensitivity: float = 0.0,
    missing_evidence: list[str] | None = None,
    line_threshold: float = 90.0,
    branch_threshold: float = 90.0,
) -> RiskScoreRecord:
    line_coverage = coverage.line_coverage if coverage else 0.0
    branch_coverage = coverage.branch_coverage if coverage else None
    line_gap = max(0.0, line_threshold - line_coverage)
    branch_gap = max(0.0, branch_threshold - branch_coverage) if branch_coverage is not None else 0.0
    coverage_gap = line_gap + branch_gap
    risk_score = (
        complexity * 3
        + churn * 2
        + public_api_exposure * 5
        + dependency_fan_in * 3
        + defect_history * 4
        + data_or_security_sensitivity * 5
        + coverage_gap * 4
    )
    missing = list(missing_evidence or [])
    if coverage is None:
        missing.append("coverage")
    return RiskScoreRecord(
        path=path,
        module=module,
        line_coverage=line_coverage,
        branch_coverage=branch_coverage,
        language=language,
        complexity=complexity,
        churn=churn,
        public_api_exposure=public_api_exposure,
        dependency_fan_in=dependency_fan_in,
        defect_history=defect_history,
        data_or_security_sensitivity=data_or_security_sensitivity,
        coverage_gap=coverage_gap,
        risk_score=risk_score,
        missing_evidence=missing,
    )


def weighted_index(records: list[RiskScoreRecord], use_branch: bool = False) -> float:
    numerator = 0.0
    denominator = 0.0
    for record in records:
        weight = record.risk_score
        if weight <= 0:
            continue
        coverage = record.branch_coverage if use_branch and record.branch_coverage is not None else record.line_coverage
        numerator += coverage * weight
        denominator += weight
    return round(numerator / denominator, 2) if denominator else 0.0


def priority(record: RiskScoreRecord) -> float:
    return record.risk_score * record.coverage_gap
