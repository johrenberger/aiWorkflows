from __future__ import annotations

from ..models import RiskScoreRecord


def coverage_improved(before: RiskScoreRecord, after_line: float, after_branch: float | None = None) -> tuple[bool, str]:
    if after_line <= before.line_coverage:
        return False, "line coverage did not improve"
    if before.branch_coverage is not None and after_branch is None:
        return False, "branch coverage evidence missing after validation"
    if before.branch_coverage is not None and after_branch <= before.branch_coverage:
        return False, "branch coverage did not improve"
    return True, "coverage improved"
