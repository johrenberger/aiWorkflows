"""BDD-TDD coverage tests for CTA-GAP-003: overlap_analyzer threshold boundaries.

Triggered by application-test-coverage (FOCUSED_PICKS pass) on the
component-test-analysis gap-backlog. CTA-GAP-003 is a P1 gap (T1 risk):

    "overlap_analyzer._recommendation is parameterized on
    merge_threshold and differentiate_threshold. The defaults
    are 85/70. Need tests that exercise the boundary cases
    (score == 85, score == 70, score == 84) to lock in the
    off-by-one behavior."

The existing tests in test_overlap_analyzer.py cover the typical cases
but not the exact boundaries. These tests pin the off-by-one behavior:
- score == 85 with thresholds (85, 70) -> MERGE
- score == 84 with thresholds (85, 70) -> DIFFERENTIATE
- score == 70 with thresholds (85, 70) -> DIFFERENTIATE
- score == 69 with thresholds (85, 70) -> KEEP_SEPARATE

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

from skill_governance.overlap_analyzer import _recommendation
from skill_governance.models import OverlapRecommendation


# ===========================================================================
# SCENARIO 1: score exactly at merge_threshold maps to MERGE
#
# Given: default thresholds (merge=85, differentiate=70)
# When:  _recommendation is called with score=85
# Then:  it returns MERGE (the >= boundary is inclusive)
# ===========================================================================
def test_score_at_merge_threshold_returns_merge():
    """score == 85 (merge_threshold) is inclusive: returns MERGE."""
    assert _recommendation(85) == OverlapRecommendation.MERGE
    assert _recommendation(85, merge_threshold=85, differentiate_threshold=70) == OverlapRecommendation.MERGE


# ===========================================================================
# SCENARIO 2: score just below merge_threshold maps to DIFFERENTIATE
#
# Given: default thresholds (merge=85, differentiate=70)
# When:  _recommendation is called with score=84
# Then:  it returns DIFFERENTIATE (one below the >= boundary)
# ===========================================================================
def test_score_one_below_merge_threshold_returns_differentiate():
    """score == 84 is below the merge threshold: returns DIFFERENTIATE."""
    assert _recommendation(84) == OverlapRecommendation.DIFFERENTIATE
    assert _recommendation(84, merge_threshold=85, differentiate_threshold=70) == OverlapRecommendation.DIFFERENTIATE


# ===========================================================================
# SCENARIO 3: score exactly at differentiate_threshold maps to DIFFERENTIATE
#
# Given: default thresholds (merge=85, differentiate=70)
# When:  _recommendation is called with score=70
# Then:  it returns DIFFERENTIATE (the >= boundary is inclusive)
# ===========================================================================
def test_score_at_differentiate_threshold_returns_differentiate():
    """score == 70 (differentiate_threshold) is inclusive: returns DIFFERENTIATE."""
    assert _recommendation(70) == OverlapRecommendation.DIFFERENTIATE
    assert _recommendation(70, merge_threshold=85, differentiate_threshold=70) == OverlapRecommendation.DIFFERENTIATE


# ===========================================================================
# SCENARIO 4: score just below differentiate_threshold maps to KEEP_SEPARATE
#
# Given: default thresholds (merge=85, differentiate=70)
# When:  _recommendation is called with score=69
# Then:  it returns KEEP_SEPARATE (one below the >= boundary)
# ===========================================================================
def test_score_one_below_differentiate_threshold_returns_keep_separate():
    """score == 69 is below the differentiate threshold: returns KEEP_SEPARATE."""
    assert _recommendation(69) == OverlapRecommendation.KEEP_SEPARATE
    assert _recommendation(69, merge_threshold=85, differentiate_threshold=70) == OverlapRecommendation.KEEP_SEPARATE


# ===========================================================================
# SCENARIO 5: custom thresholds shift the boundaries predictably
#
# Given: lower thresholds (merge=50, differentiate=30) - e.g. for a noisy
#        catalog where "overlap" is more liberally defined
# When:  _recommendation is called with the custom thresholds
# Then:  the boundaries shift correctly (score=50 -> MERGE, 49 -> DIFFERENTIATE,
#        30 -> DIFFERENTIATE, 29 -> KEEP_SEPARATE)
# ===========================================================================
def test_custom_thresholds_shift_boundaries_predictably():
    """Lowered thresholds move both boundaries (50/30): 50->MERGE, 49->DIFFERENTIATE, 30->DIFFERENTIATE, 29->KEEP_SEPARATE."""
    assert _recommendation(50, merge_threshold=50, differentiate_threshold=30) == OverlapRecommendation.MERGE
    assert _recommendation(49, merge_threshold=50, differentiate_threshold=30) == OverlapRecommendation.DIFFERENTIATE
    assert _recommendation(30, merge_threshold=50, differentiate_threshold=30) == OverlapRecommendation.DIFFERENTIATE
    assert _recommendation(29, merge_threshold=50, differentiate_threshold=30) == OverlapRecommendation.KEEP_SEPARATE


# ===========================================================================
# SCENARIO 6: extreme scores map to extremes
#
# Given: thresholds (85, 70)
# When:  _recommendation is called with score=0 and score=100
# Then:  0 -> KEEP_SEPARATE, 100 -> MERGE
# ===========================================================================
def test_extreme_scores_map_to_extreme_recommendations():
    """Boundaries: 0 -> KEEP_SEPARATE (lowest), 100 -> MERGE (highest)."""
    assert _recommendation(0) == OverlapRecommendation.KEEP_SEPARATE
    assert _recommendation(100) == OverlapRecommendation.MERGE
