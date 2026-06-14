"""BDD-TDD coverage tests for roi_scorer.py (Batch 2).

Triggered by application-test-coverage assessment: roi_scorer.py
was 83% line coverage. 17 statements uncovered across several
branches in _score_one (the central scoring function) and edge
cases in _normalize and _token_cost_score.

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

from skill_governance.models import (
    ArtifactType,
    Decision,
    Finding,
    OverlapPair,
    OverlapRecommendation,
    ScorecardEntry,
    Severity,
    SkillArtifact,
)
from skill_governance.roi_scorer import (
    _normalize,
    _token_cost_score,
    _score_one,
    score,
    ROIWeights,
)


def _artifact(name: str) -> SkillArtifact:
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


# ===========================================================================
# SCENARIO 1: _normalize returns 0.0 when hi <= lo
# ===========================================================================
def test_normalize_returns_zero_when_hi_le_lo():
    """_normalize returns 0.0 when the range is degenerate."""
    assert _normalize(50.0, lo=100.0, hi=50.0) == 0.0
    assert _normalize(50.0, lo=100.0, hi=99.0) == 0.0


# ===========================================================================
# SCENARIO 2: _token_cost_score returns 1.0 when high_cost <= 0
# ===========================================================================
def test_token_cost_score_returns_one_for_zero_high_cost():
    """high_cost <= 0 means no cost concern, score is 1.0."""
    assert _token_cost_score(100, high_cost=0) == 1.0
    assert _token_cost_score(100, high_cost=-1) == 1.0


# ===========================================================================
# SCENARIO 3: _token_cost_score returns 1.0 for zero tokens
# ===========================================================================
def test_token_cost_score_returns_one_for_zero_tokens():
    """Zero estimated_tokens is treated as zero cost."""
    assert _token_cost_score(0, high_cost=8000) == 1.0


# ===========================================================================
# SCENARIO 4: _score_one returns KEEP for high score with no rewrite trigger
# ===========================================================================
def test_score_one_returns_keep_for_high_score_no_rewrite():
    """High score, no blocking, no warnings -> KEEP."""
    artifact = _artifact("strong")
    weights = ROIWeights()  # defaults
    entry = _score_one(
        artifact,
        reuse_count=10,
        token_costs=[],
        findings=[],
        dependency_value=80,
        semantic_uniqueness=80,
        benchmark_pass_rate=1.0,
        business_criticality=80,
        weights=weights,
        overlap_pairs=[],
    )
    assert entry.decision == Decision.KEEP, f"expected KEEP, got {entry.decision}"
    assert entry.roi_score >= 70


# ===========================================================================
# SCENARIO 5: _score_one returns MERGE when overlap pair recommends merge
# ===========================================================================
def test_score_one_returns_merge_when_overlap_pair_says_merge():
    """A MERGE overlap pair makes the decision MERGE (Phase 7 fix)."""
    artifact = _artifact("x")
    pair = OverlapPair(
        artifact_a="x", artifact_b="y",
        overlap_score=92, rationale="high",
        recommendation=OverlapRecommendation.MERGE,
    )
    weights = ROIWeights()
    entry = _score_one(
        artifact,
        reuse_count=0,
        token_costs=[],
        findings=[],
        dependency_value=0,
        semantic_uniqueness=0,
        benchmark_pass_rate=0.5,
        business_criticality=0,
        weights=weights,
        overlap_pairs=[pair],
    )
    assert entry.decision == Decision.MERGE, f"expected MERGE, got {entry.decision}"


# ===========================================================================
# SCENARIO 6: _score_one returns REWRITE for blocking findings
# ===========================================================================
def test_score_one_returns_rewrite_for_blocking_findings():
    """Blocking findings trigger REWRITE."""
    artifact = _artifact("x")
    findings = [
        Finding(finding_id="f1", artifact_name="x", severity=Severity.BLOCKING, category="contract", message="bad"),
    ]
    weights = ROIWeights()
    entry = _score_one(
        artifact,
        reuse_count=0,
        token_costs=[],
        findings=findings,
        dependency_value=50,
        semantic_uniqueness=50,
        benchmark_pass_rate=0.5,
        business_criticality=50,
        weights=weights,
        overlap_pairs=[],
    )
    assert entry.decision == Decision.REWRITE, f"expected REWRITE, got {entry.decision}"


# ===========================================================================
# SCENARIO 7: score() with empty inputs returns empty list
# ===========================================================================
def test_score_empty_input_returns_empty_list():
    """An empty input list returns an empty scorecard list."""
    result = score([], findings=[], token_costs=[])
    assert result == [], f"expected empty list, got {result}"


# ===========================================================================
# SCENARIO 8: score() with no overlap pairs falls back to score-only path
# ===========================================================================
def test_score_handles_no_overlap_pairs():
    """score() works when overlap_pairs is omitted (default [])."""
    artifacts = [_artifact("a"), _artifact("b")]
    result = score(artifacts, findings=[], token_costs=[])
    assert len(result) == 2
    for entry in result:
        assert isinstance(entry, ScorecardEntry)
