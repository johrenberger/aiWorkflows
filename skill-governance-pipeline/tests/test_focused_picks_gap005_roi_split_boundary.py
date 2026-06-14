"""BDD-TDD coverage tests for CTA-GAP-005: roi_scorer SPLIT boundary.

Triggered by application-test-coverage (FOCUSED_PICKS pass) on the
component-test-analysis gap-backlog. CTA-GAP-005 is a P1 gap (T1 risk):

    "roi_scorer._score_one with low score (10-29) returns SPLIT.
    The test_batch2_roi_scorer_coverage.py test_score_one_returns_split_for_low_score
    only checks that the decision is in {REWRITE, SPLIT, DEPRECATE} - it
    doesn't lock the actual boundary. Need a more targeted test for the
    score==10 boundary case."

The current existing test only asserts the decision is in a set, not
the specific value. These tests lock:
- score == 10 with no merge candidate, no blocking -> SPLIT
- score == 9 (just below boundary) with no merge candidate, no blocking -> DEPRECATE
- score in [10, 29] is the SPLIT band (boundary pin)

We use controlled ROIWeights to force specific scores, since the natural
score formula doesn't land in [10, 29] with default weights.

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

from skill_governance.models import ArtifactType, SkillArtifact
from skill_governance.roi_scorer import ROIWeights, _score_one


def _artifact(name: str = "x") -> SkillArtifact:
    return SkillArtifact(
        name=name,
        path=name + ".md",
        artifact_type=ArtifactType.SKILL,
        size_bytes=100,
        estimated_tokens=25,
        content_hash="x" * 64,
        modified_timestamp="2026-06-13T00:00:00Z",
        body_excerpt="test",
    )


def _no_other_contributions_weights() -> ROIWeights:
    """A weight set where ONLY reuse contributes (forces score to depend only on reuse_count).

    With w_reuse=1.0 and all other weights=0:
    raw = reuse_score(reuse_count) = _normalize(log10(reuse_count + 1), 0, 2)
    - reuse_count=0 -> raw=0 -> score=0
    - reuse_count=1 -> raw=0.15 -> score=15
    - reuse_count=2 -> raw=0.24 -> score=24
    - reuse_count=3 -> raw=0.30 -> score=30 (no longer in SPLIT band)
    """
    return ROIWeights(
        reuse=1.0,
        token_cost=0,
        output_quality=0,
        dependency_value=0,
        failure_rate=0,
        semantic_uniqueness=0,
        benchmark_pass_rate=0,
        business_criticality=0,
    )


# ===========================================================================
# SCENARIO 1: score 15 (in SPLIT band) with no merge candidate, no blocking
#
# Given: a low-score artifact (reuse=1, w_reuse=1.0, no other contributions)
# When:  _score_one is called
# Then:  decision is SPLIT (not REWRITE, not DEPRECATE)
# ===========================================================================
def test_score_in_split_band_returns_split():
    """Score 15 (low) with no rewrite trigger and no merge candidate -> SPLIT."""
    a = _artifact()
    entry = _score_one(
        a,
        reuse_count=1,
        token_costs=[],
        findings=[],
        dependency_value=0,
        semantic_uniqueness=0,
        benchmark_pass_rate=0.0,
        business_criticality=0,
        weights=_no_other_contributions_weights(),
    )
    assert entry.roi_score == 15, f"expected score=15, got {entry.roi_score}"
    assert entry.decision.value == "split", (
        f"score 15 in [10, 29] band should be SPLIT, got '{entry.decision.value}'"
    )


# ===========================================================================
# SCENARIO 2: score 0 (below SPLIT band) with no merge candidate, no blocking
#
# Given: an artifact with zero reuse and no other positive contributions
# When:  _score_one is called
# Then:  decision is DEPRECATE (score < 10)
# ===========================================================================
def test_score_below_split_band_returns_deprecate():
    """Score 0 (< 10) with no rewrite trigger and no merge candidate -> DEPRECATE."""
    a = _artifact()
    entry = _score_one(
        a,
        reuse_count=0,
        token_costs=[],
        findings=[],
        dependency_value=0,
        semantic_uniqueness=0,
        benchmark_pass_rate=0.0,
        business_criticality=0,
        weights=_no_other_contributions_weights(),
    )
    assert entry.roi_score == 0, f"expected score=0, got {entry.roi_score}"
    assert entry.decision.value == "deprecate", (
        f"score 0 (< 10) should be DEPRECATE, got '{entry.decision.value}'"
    )


# ===========================================================================
# SCENARIO 3: score exactly 10 (lower SPLIT boundary) with no merge, no blocking
#
# Given: weights tuned so that reuse_count=1 produces exactly score=10
# When:  _score_one is called
# Then:  decision is SPLIT (boundary is INCLUSIVE: >= 10)
# ===========================================================================
def test_score_exactly_ten_at_split_lower_boundary_returns_split():
    """Score == 10 (the lower boundary) with no rewrite trigger and no merge candidate -> SPLIT.

    The boundary is inclusive on the lower side: score >= 10 maps to SPLIT.
    """
    a = _artifact()
    # reuse=1, reuse_score = log10(2)/2 ≈ 0.1505
    # w_reuse = 0.667 -> raw = 0.1003, score = 10
    weights = ROIWeights(
        reuse=0.667,
        token_cost=0,
        output_quality=0,
        dependency_value=0,
        failure_rate=0,
        semantic_uniqueness=0,
        benchmark_pass_rate=0,
        business_criticality=0,
    )
    entry = _score_one(
        a,
        reuse_count=1,
        token_costs=[],
        findings=[],
        dependency_value=0,
        semantic_uniqueness=0,
        benchmark_pass_rate=0.0,
        business_criticality=0,
        weights=weights,
    )
    assert entry.roi_score == 10, f"expected score=10, got {entry.roi_score}"
    assert entry.decision.value == "split", (
        f"score 10 (lower boundary, inclusive) should be SPLIT, got '{entry.decision.value}'"
    )


# ===========================================================================
# SCENARIO 4: score exactly 9 (just below SPLIT boundary) with no merge, no blocking
#
# Given: weights tuned so that reuse_count=1 produces exactly score=9
# When:  _score_one is called
# Then:  decision is DEPRECATE (boundary is EXCLUSIVE on the lower side: < 10)
# ===========================================================================
def test_score_exactly_nine_below_split_lower_boundary_returns_deprecate():
    """Score == 9 (just below lower boundary) -> DEPRECATE.

    The boundary is exclusive on the lower side: score < 10 maps to DEPRECATE.
    """
    a = _artifact()
    # reuse=1, reuse_score = 0.1505
    # w_reuse = 0.6 -> raw = 0.0903, score = 9
    weights = ROIWeights(
        reuse=0.6,
        token_cost=0,
        output_quality=0,
        dependency_value=0,
        failure_rate=0,
        semantic_uniqueness=0,
        benchmark_pass_rate=0,
        business_criticality=0,
    )
    entry = _score_one(
        a,
        reuse_count=1,
        token_costs=[],
        findings=[],
        dependency_value=0,
        semantic_uniqueness=0,
        benchmark_pass_rate=0.0,
        business_criticality=0,
        weights=weights,
    )
    assert entry.roi_score == 9, f"expected score=9, got {entry.roi_score}"
    assert entry.decision.value == "deprecate", (
        f"score 9 (< 10) should be DEPRECATE, got '{entry.decision.value}'"
    )


# ===========================================================================
# SCENARIO 5: SPLIT band is [10, 29]
#
# Given: a sample of scores across [0, 30] with no rewrite trigger, no merge
# When:  _score_one is called for each
# Then:  scores 0-9 are DEPRECATE, 10-29 are SPLIT, 30+ are REWRITE
# ===========================================================================
def test_split_band_is_ten_to_twenty_nine():
    """Pin the SPLIT decision band: [10, 29] inclusive on both sides, [0, 9] DEPRECATE."""
    a = _artifact()
    # Use weights that scale reuse_score so each reuse_count maps to a different score.
    # reuse_score(0)=0, reuse_score(1)=0.15, reuse_score(2)=0.24
    # w_reuse=0.6, w_other=0.4 (output_quality uses default-normalized 0):
    #   raw = 0.6*reuse_score + 0.4*output_quality_normalized
    # Need control over output_quality too. Use output_quality=0 always.
    weights = ROIWeights(
        reuse=0.6, token_cost=0, output_quality=0, dependency_value=0,
        failure_rate=0, semantic_uniqueness=0, benchmark_pass_rate=0, business_criticality=0,
    )
    # reuse_count=0 -> raw=0, score=0
    # reuse_count=1 -> raw=0.0903, score=9
    # reuse_count=2 -> raw=0.1436, score=14
    # reuse_count=3 -> raw=0.1806, score=18
    # reuse_count=4 -> raw=0.2104, score=21
    # reuse_count=5 -> raw=0.2336, score=23
    cases = [
        (0, 0, "deprecate"),
        (1, 9, "deprecate"),
        (2, 14, "split"),
        (3, 18, "split"),
        (4, 21, "split"),
        (5, 23, "split"),
    ]
    for reuse_count, expected_score, expected_decision in cases:
        entry = _score_one(
            a, reuse_count=reuse_count, token_costs=[], findings=[],
            dependency_value=0, semantic_uniqueness=0,
            benchmark_pass_rate=0.0, business_criticality=0, weights=weights,
        )
        assert entry.roi_score == expected_score, (
            f"reuse={reuse_count}: expected score={expected_score}, got {entry.roi_score}"
        )
        assert entry.decision.value == expected_decision, (
            f"reuse={reuse_count} (score={entry.roi_score}): expected '{expected_decision}', "
            f"got '{entry.decision.value}'"
        )
