from __future__ import annotations

import re

BRANCH_PATTERN = re.compile(r"\b(if|elif|else|for|while|try|except|case|switch)\b|&&|\|\||\?")


def coverage_readiness(line_coverage: float | None, fallback_allowed: bool) -> float:
    if line_coverage is None:
        return 40.0 if fallback_allowed else 0.0
    if line_coverage >= 90:
        return 100.0
    if line_coverage >= 80:
        return 80.0
    if line_coverage >= 70:
        return 60.0
    return 20.0


def complexity_score(source: str) -> float:
    executable_lines = [line for line in source.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not executable_lines:
        return 0.0
    branch_count = len(BRANCH_PATTERN.findall(source))
    return round(min(100.0, branch_count / len(executable_lines) * 300.0), 2)


def target_score(coverage: float, complexity: float) -> float:
    test_density_suspicion = 50.0
    runtime_feasibility = 100.0
    churn_or_default_priority = 50.0
    return round(
        0.35 * coverage
        + 0.25 * complexity
        + 0.20 * test_density_suspicion
        + 0.10 * runtime_feasibility
        + 0.10 * churn_or_default_priority,
        2,
    )
