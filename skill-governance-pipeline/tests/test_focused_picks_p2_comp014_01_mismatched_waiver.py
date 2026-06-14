"""BDD-TDD coverage tests for CTA-COMP-014-01: ci_gate.evaluate with mismatched waiver.

Triggered by application-test-coverage (FOCUSED_PICKS2 pass) on the
component-test-analysis gap-backlog. CTA-COMP-014-01 is a P2 gap (T2 risk):

    "ci_gate.evaluate() with an active waiver that doesn't actually
    match any finding ID is silently accepted. Need a test that asserts:
    a waiver for finding_id='non-existent' is allowed but doesn't
    suppress anything."

The current code:
    waived_ids = {w.finding_id for w in waivers}
    for f in result.findings:
        if f.severity == BLOCKING and f.finding_id not in waived_ids:
            return False
    return True

A waiver with a finding_id that doesn't match any actual finding is
silently ignored (its presence in `waived_ids` doesn't suppress anything
because no finding has that ID). The gap wants this behavior LOCKED:
a mismatched waiver doesn't suppress the actual blocker.

These tests pin:
- Mismatched waiver + blocking finding -> still fails (waiver is no-op)
- Matched waiver + blocking finding -> passes
- Multiple waivers, some matched some not -> matched ones suppress,
  the actual blocker still fails
- count_blocking() ignores waivers (returns the raw count)

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

from skill_governance.ci_gate import count_blocking, evaluate
from skill_governance.models import (
    Finding,
    PipelineResult,
    Severity,
    Waiver,
)


def _waiver(finding_id: str, waiver_id: str = "w1") -> Waiver:
    """Build a Waiver (with an active expiration)."""
    return Waiver(
        waiver_id=waiver_id,
        finding_id=finding_id,
        owner="justin",
        expiration_date="2099-01-01",
        rationale="accepted risk",
        approved_by="justin",
    )


def _blocking_finding(finding_id: str, artifact_name: str = "a") -> Finding:
    return Finding(
        finding_id=finding_id,
        artifact_name=artifact_name,
        severity=Severity.BLOCKING,
        category="metadata",
        message="bad",
    )


# ===========================================================================
# SCENARIO 1: Mismatched waiver (finding_id='non-existent') doesn't suppress
#        a real BLOCKING finding
#
# Given: a blocking finding with ID='real-bug' and a waiver for
#        finding_id='non-existent' (no such finding)
# When:  evaluate() is called
# Then:  returns False (the real bug still blocks; the mismatched
#        waiver is a no-op)
# ===========================================================================
def test_mismatched_waiver_does_not_suppress_real_blocking_finding():
    """A waiver for a non-existent finding_id does NOT suppress a real blocker."""
    result = PipelineResult(findings=[_blocking_finding("real-bug")])
    waivers = [_waiver("non-existent")]
    assert evaluate(result, waivers) is False, (
        "mismatched waiver should NOT suppress the real blocker; expected evaluate()=False"
    )


# ===========================================================================
# SCENARIO 2: Matched waiver (finding_id='real-bug') suppresses
#
# Given: a blocking finding 'real-bug' and a waiver for 'real-bug'
# When:  evaluate() is called
# Then:  returns True
# ===========================================================================
def test_matched_waiver_suppresses_real_blocking_finding():
    """A waiver whose finding_id matches the real blocker allows the gate to pass."""
    result = PipelineResult(findings=[_blocking_finding("real-bug")])
    waivers = [_waiver("real-bug")]
    assert evaluate(result, waivers) is True


# ===========================================================================
# SCENARIO 3: Mixed waivers — matched one suppresses its finding, the
#        actual blocker is the OTHER (unmatched) finding
#
# Given: two blocking findings ('A' and 'B'), a waiver for 'A' (matched)
#        and a waiver for 'non-existent' (mismatched)
# When:  evaluate() is called
# Then:  returns False (B is still blocking)
# ===========================================================================
def test_mismatched_waiver_does_not_save_a_different_real_finding():
    """Even with matched waivers for OTHER findings, an unmatched blocker still fails."""
    result = PipelineResult(findings=[
        _blocking_finding("A"),
        _blocking_finding("B"),
    ])
    waivers = [_waiver("A"), _waiver("non-existent")]
    assert evaluate(result, waivers) is False, (
        "B is still blocking; mismatched waiver doesn't help"
    )


# ===========================================================================
# SCENARIO 4: Empty waivers + blocking finding -> fails
#
# Given: blocking finding, no waivers
# When:  evaluate() is called
# Then:  returns False
# ===========================================================================
def test_empty_waivers_with_blocking_finding_fails():
    """A blocking finding with no waivers fails the gate."""
    result = PipelineResult(findings=[_blocking_finding("X")])
    assert evaluate(result) is False
    assert evaluate(result, []) is False


# ===========================================================================
# SCENARIO 5: count_blocking returns the raw count (no waivers param)
#
# Given: 2 blocking findings
# When:  count_blocking() is called
# Then:  returns 2 (raw count; the function takes no waivers arg)
# ===========================================================================
def test_count_blocking_returns_raw_count():
    """count_blocking() takes only the result; it returns the raw count of blocking findings."""
    result = PipelineResult(findings=[
        _blocking_finding("A"),
        _blocking_finding("B"),
    ])
    assert count_blocking(result) == 2, (
        f"count_blocking should return 2 (raw count), got {count_blocking(result)}"
    )


# ===========================================================================
# SCENARIO 6: warning findings are never blocked by waivers
#
# Given: a WARNING finding (not blocking) and a waiver for it
# When:  evaluate() is called
# Then:  returns True (warnings don't block; the waiver is irrelevant)
# ===========================================================================
def test_waivers_do_not_apply_to_warnings():
    """A waiver for a WARNING finding is a no-op (warnings don't block)."""
    warn = Finding(
        finding_id="W1",
        artifact_name="a",
        severity=Severity.WARNING,
        category="metadata",
        message="warn",
    )
    result = PipelineResult(findings=[warn])
    waivers = [_waiver("W1")]
    assert evaluate(result, waivers) is True
    assert evaluate(result) is True
