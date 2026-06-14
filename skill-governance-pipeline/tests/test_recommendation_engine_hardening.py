"""BDD-TDD tests for recommendation_engine.py scorecard integration.

Triggered by gap scan: the existing 5 tests for recommendation_engine
cover findings, overlap_pairs, and responsibility paths, but NONE
cover the scorecard integration path. The scorecard path is exactly
where the original 64-false-merge bug lived (the path the Phase 7
fix touched). This file locks in the Phase 7 fix and catches future
regressions in the integration.

Method: BDD-TDD
- Given/When/Then in each docstring
- Function name = assertion
- All tests include a finding alongside the scorecard (the scorecard
  only activates the recommendation path when there's also a finding
  for that artifact — this is the current contract, and these tests
  lock it in)
"""
from __future__ import annotations

from skill_governance.models import (
    Decision,
    Finding,
    OverlapPair,
    OverlapRecommendation,
    ResponsibilityFlag,
    ResponsibilityReport,
    ScorecardEntry,
    Severity,
)
from skill_governance.recommendation_engine import generate


def _finding(artifact: str) -> Finding:
    return Finding(
        finding_id=f"f-{artifact}",
        artifact_name=artifact,
        severity=Severity.BLOCKING,
        category="metadata",
        message="missing field",
    )


# ===========================================================================
# SCENARIO 1: scorecard KEEP + finding -> recommendation KEEP
#
# Given: a scorecard with decision=KEEP for artifact-a AND a BLOCKING
#        finding for artifact-a
# When:  generate is called
# Then:  the recommendation has decision=KEEP (scorecard wins over
#        the finding-derived REWRITE)
# ===========================================================================
def test_scorecard_keep_decision_overrides_finding_derived_rewrite():
    """Scorecard KEEP wins over finding-derived REWRITE."""
    sc = ScorecardEntry(artifact_name="artifact-a", roi_score=80, decision=Decision.KEEP, rationale="strong")
    recs = generate([_finding("artifact-a")], scorecards=[sc])
    assert len(recs) == 1
    assert recs[0].decision == Decision.KEEP, (
        f"Scorecard KEEP should win over finding-derived REWRITE, got {recs[0].decision}"
    )


# ===========================================================================
# SCENARIO 2: scorecard REWRITE + finding -> recommendation REWRITE
#
# Given: a scorecard with decision=REWRITE for artifact-a AND a finding
# When:  generate is called
# Then:  the recommendation has decision=REWRITE
# ===========================================================================
def test_scorecard_rewrite_decision_propagates():
    """Scorecard REWRITE propagates to the recommendation."""
    sc = ScorecardEntry(artifact_name="artifact-a", roi_score=40, decision=Decision.REWRITE, rationale="needs work")
    recs = generate([_finding("artifact-a")], scorecards=[sc])
    assert len(recs) == 1
    assert recs[0].decision == Decision.REWRITE, (
        f"Scorecard REWRITE should produce REWRITE rec, got {recs[0].decision}"
    )


# ===========================================================================
# SCENARIO 3: scorecard MERGE + finding -> recommendation MERGE
# (locks in Phase 7 fix: the integration that prevented the 64-false-merge bug)
# ===========================================================================
def test_scorecard_merge_decision_propagates_phase7_fix():
    """Scorecard MERGE propagates to a MERGE recommendation (Phase 7 integration)."""
    sc = ScorecardEntry(artifact_name="artifact-a", roi_score=25, decision=Decision.MERGE, rationale="overlapping")
    recs = generate([_finding("artifact-a")], scorecards=[sc])
    assert len(recs) == 1
    assert recs[0].decision == Decision.MERGE, (
        f"Scorecard MERGE should produce MERGE rec (Phase 7 fix), got {recs[0].decision}"
    )
    assert "artifact-a" in recs[0].affected_artifacts


# ===========================================================================
# SCENARIO 4: scorecard MERGE + overlap pair -> 2 distinct recommendations
# (no false dedup; both are surfaced)
# ===========================================================================
def test_scorecard_merge_and_overlap_pair_produce_distinct_recommendations():
    """Scorecard MERGE + overlap pair both produce recommendations (no false dedup)."""
    sc = ScorecardEntry(artifact_name="artifact-a", roi_score=25, decision=Decision.MERGE, rationale="overlap")
    pair = OverlapPair(
        artifact_a="artifact-a",
        artifact_b="artifact-b",
        overlap_score=92,
        rationale="high overlap",
        recommendation=OverlapRecommendation.MERGE,
    )
    recs = generate([_finding("artifact-a")], scorecards=[sc], overlap_pairs=[pair])
    # 1 from finding+scorecard, 1 from overlap pair
    assert len(recs) == 2, f"Expected 2 recommendations (scorecard + overlap), got {len(recs)}"
    decisions = {r.decision for r in recs}
    assert decisions == {Decision.MERGE}, f"Both should be MERGE, got {decisions}"


# ===========================================================================
# SCENARIO 5: scorecard DEPRECATE + finding -> recommendation DEPRECATE
# ===========================================================================
def test_scorecard_deprecate_decision_propagates():
    """Scorecard DEPRECATE propagates to the recommendation."""
    sc = ScorecardEntry(artifact_name="artifact-a", roi_score=10, decision=Decision.DEPRECATE, rationale="obsolete")
    recs = generate([_finding("artifact-a")], scorecards=[sc])
    assert len(recs) == 1
    assert recs[0].decision == Decision.DEPRECATE, (
        f"Scorecard DEPRECATE should produce DEPRECATE rec, got {recs[0].decision}"
    )


# ===========================================================================
# SCENARIO 6: priority field reflects blocking + decision
# ===========================================================================
def test_recommendation_priority_uses_blocking_count():
    """A scorecard with MERGE decision and 1 blocking finding gets priority 2."""
    sc = ScorecardEntry(artifact_name="artifact-a", roi_score=25, decision=Decision.MERGE, rationale="overlap")
    recs = generate([_finding("artifact-a")], scorecards=[sc])
    assert len(recs) == 1
    # MERGE with blocking = priority 2
    assert recs[0].priority == 2, f"Expected priority 2, got {recs[0].priority}"
