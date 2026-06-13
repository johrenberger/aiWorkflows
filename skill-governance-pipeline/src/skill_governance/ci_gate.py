"""CI gate: enforce governance quality gates.

Implements Core Requirement 12.

Default CI blockers:
- missing required metadata
- missing input/output contracts
- missing dependency
- circular dependency
- benchmark failure
- high-overlap duplicate without waiver
- critical low ROI
- invalid proposed new skill
- malformed configuration

Support waivers with explicit rationale.
"""
from __future__ import annotations

from .models import Finding, PipelineResult, Severity, Waiver


def evaluate(result: PipelineResult, waivers: list[Waiver] | None = None) -> bool:
    """Return True if the pipeline result passes the CI gate.

    A passing gate means no blocking findings exist that are
    not covered by a valid waiver.
    """
    waivers = waivers or []
    waived_ids = {w.finding_id for w in waivers}

    for f in result.findings:
        if f.severity == Severity.BLOCKING and f.finding_id not in waived_ids:
            return False
    return True


def count_blocking(result: PipelineResult) -> int:
    """Return the number of blocking findings (waivers not applied)."""
    return sum(1 for f in result.findings if f.severity == Severity.BLOCKING)
