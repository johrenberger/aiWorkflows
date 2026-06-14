"""BDD-TDD coverage tests for CTA-GAP-006: recommendation_engine scorecard-only input.

Triggered by application-test-coverage (FOCUSED_PICKS2 pass) on the
component-test-analysis gap-backlog. CTA-GAP-006 is a P2 gap (T2 risk):

    "recommendation_engine.generate() with a scorecard entry but no
    finding skips that artifact (does not emit a recommendation).
    The current tests in test_recommendation_engine_hardening.py all
    include BOTH scorecard AND finding. Need a test that locks this
    behavior: scorecard-only input -> no recommendation for that artifact."

The current code emits a recommendation only when there is a finding
for an artifact. A scorecard alone (with no finding) means the
artifact is clean from the validator's perspective; the scorecard's
decision is never used to trigger a recommendation. This is intentional
(the recommendation engine is finding-driven), and the gap is asking
for a test to lock that behavior.

These tests pin:
- scorecard-only input -> empty recommendations list (no entry for the artifact)
- KEEP scorecard + no finding -> no recommendation
- REWRITE scorecard + no finding -> STILL no recommendation (scorecard alone doesn't trigger)
- BLOCKING finding + no scorecard -> recommendation emitted (sanity)
- scorecard alone + finding for DIFFERENT artifact -> no recommendation for the scorecard-only artifact

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

from skill_governance.models import (
    Decision,
    Finding,
    ScorecardEntry,
    Severity,
)
from skill_governance.recommendation_engine import generate


def _scorecard(artifact_name: str, decision: Decision, score: int = 75) -> ScorecardEntry:
    """Build a minimal ScorecardEntry for tests."""
    return ScorecardEntry(
        artifact_name=artifact_name,
        decision=decision,
        roi_score=score,
        rationale="test scorecard",
    )


# ===========================================================================
# SCENARIO 1: scorecard-only input (no finding) -> no recommendation
#
# Given: a single KEEP scorecard entry, no findings, no overlap, no responsibility
# When:  generate() is called
# Then:  no recommendation is emitted (findings drive the loop)
# ===========================================================================
def test_scorecard_only_keep_input_emits_no_recommendation():
    """A KEEP scorecard with no finding produces no recommendation (findings drive the loop)."""
    recs = generate(
        findings=[],
        scorecards=[_scorecard("clean-artifact", Decision.KEEP)],
    )
    assert len(recs) == 0, (
        f"scorecard-only input should produce no recommendations; got {[(r.affected_artifacts, r.decision) for r in recs]}"
    )


# ===========================================================================
# SCENARIO 2: REWRITE scorecard alone (no finding) -> still no recommendation
#
# Given: a REWRITE scorecard, no findings
# When:  generate() is called
# Then:  no recommendation is emitted (the REWRITE decision is
#        scorecard's view; the recommendation engine only acts on findings)
# ===========================================================================
def test_scorecard_only_rewrite_input_emits_no_recommendation():
    """A REWRITE scorecard with no finding produces no recommendation."""
    recs = generate(
        findings=[],
        scorecards=[_scorecard("needs-rewrite", Decision.REWRITE)],
    )
    assert len(recs) == 0, (
        f"REWRITE scorecard with no finding should not produce a recommendation; got {recs}"
    )


# ===========================================================================
# SCENARIO 3: MERGE / SPLIT / DEPRECATE / RETIRE scorecards alone -> no recs
#
# Given: one scorecard of each non-KEEP decision, no findings
# When:  generate() is called
# Then:  no recommendations are emitted
# ===========================================================================
def test_all_non_keep_scorecards_alone_emit_no_recommendations():
    """All non-KEEP scorecards without findings produce no recommendations."""
    for decision in [Decision.REWRITE, Decision.MERGE, Decision.SPLIT, Decision.DEPRECATE, Decision.RETIRE]:
        recs = generate(
            findings=[],
            scorecards=[_scorecard(f"art-{decision.value}", decision)],
        )
        assert len(recs) == 0, (
            f"scorecard-only {decision.value} should not produce a rec; got {recs}"
        )


# ===========================================================================
# SCENARIO 4: scorecard + finding for SAME artifact -> recommendation emitted
#
# Given: a scorecard for "x" AND a BLOCKING finding for "x"
# When:  generate() is called
# Then:  one recommendation is emitted for "x" (with the scorecard's
#        decision, not the derived decision)
# ===========================================================================
def test_scorecard_plus_finding_emits_one_recommendation():
    """A scorecard + finding for the same artifact produces exactly one recommendation."""
    f = Finding(
        finding_id="x.blocker",
        artifact_name="x",
        severity=Severity.BLOCKING,
        category="contract",
        message="broken",
    )
    recs = generate(
        findings=[f],
        scorecards=[_scorecard("x", Decision.KEEP)],
    )
    assert len(recs) == 1
    assert recs[0].affected_artifacts == ["x"]
    # The recommendation uses the scorecard's decision (KEEP), not the
    # derived-from-finding decision (would be REWRITE)
    assert recs[0].decision == Decision.KEEP


# ===========================================================================
# SCENARIO 5: scorecard alone + finding for DIFFERENT artifact -> no rec
#        for the scorecard-only artifact
#
# Given: a scorecard for "x" AND a finding for "y"
# When:  generate() is called
# Then:  one recommendation for "y" is emitted; no recommendation
#        for "x" (scorecard alone doesn't trigger)
# ===========================================================================
def test_scorecard_alone_does_not_inherit_finding_from_other_artifact():
    """Scorecard for one artifact + finding for another emits rec only for the finding."""
    f = Finding(
        finding_id="y.blocker",
        artifact_name="y",
        severity=Severity.BLOCKING,
        category="contract",
        message="y is broken",
    )
    recs = generate(
        findings=[f],
        scorecards=[_scorecard("x", Decision.KEEP)],
    )
    assert len(recs) == 1
    assert recs[0].affected_artifacts == ["y"]
    # No recommendation for "x" because the finding loop only iterates
    # over findings, not scorecards
