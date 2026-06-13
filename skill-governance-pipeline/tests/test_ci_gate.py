"""Tests for the CI gate (CR 12)."""
from __future__ import annotations

from skill_governance.ci_gate import count_blocking, evaluate
from skill_governance.models import (
    Finding,
    PipelineResult,
    Severity,
    Waiver,
)


def test_empty_result_passes():
    """No findings = pass."""
    result = PipelineResult()
    assert evaluate(result) is True
    assert count_blocking(result) == 0


def test_blocking_finding_fails_gate():
    """One blocking finding = fail."""
    result = PipelineResult(
        findings=[
            Finding(
                finding_id="x",
                artifact_name="a",
                severity=Severity.BLOCKING,
                category="metadata",
                message="bad",
            )
        ]
    )
    assert evaluate(result) is False
    assert count_blocking(result) == 1


def test_warning_does_not_fail_gate():
    """A warning alone does not fail CI."""
    result = PipelineResult(
        findings=[
            Finding(
                finding_id="x",
                artifact_name="a",
                severity=Severity.WARNING,
                category="metadata",
                message="warn",
            )
        ]
    )
    assert evaluate(result) is True
    assert count_blocking(result) == 0


def test_waiver_passes_blocking_finding():
    """A valid waiver for a blocking finding allows CI to pass."""
    result = PipelineResult(
        findings=[
            Finding(
                finding_id="x",
                artifact_name="a",
                severity=Severity.BLOCKING,
                category="metadata",
                message="bad",
            )
        ]
    )
    waivers = [
        Waiver(
            waiver_id="w1",
            finding_id="x",
            owner="justin",
            expiration_date="2099-01-01",
            rationale="accepted risk",
            approved_by="justin",
        )
    ]
    assert evaluate(result, waivers) is True
