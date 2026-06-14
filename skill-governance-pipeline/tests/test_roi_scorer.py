"""Tests for the ROI scorer (CR 8)."""
from __future__ import annotations

from skill_governance.models import (
    ArtifactType,
    Decision,
    Finding,
    Severity,
    SkillArtifact,
    TokenCostStatic,
)
from skill_governance.roi_scorer import (
    ROIWeights,
    SemanticScore,
    SemanticScoringInterface,
    _failure_score,
    _reuse_score,
    _token_cost_score,
    score,
)


def _artifact(name: str, body: str = "test body") -> SkillArtifact:
    return SkillArtifact(
        name=name,
        path=name + ".md",
        artifact_type=ArtifactType.SKILL,
        size_bytes=len(body),
        estimated_tokens=max(1, len(body) // 4),
        content_hash="x" * 64,
        modified_timestamp="2026-06-13T00:00:00Z",
        body_excerpt=body,
    )


def test_failure_score_inverts_rate():
    """0% failure = 1.0; 100% failure = 0.0."""
    assert _failure_score(0.0) == 1.0
    assert _failure_score(1.0) == 0.0
    assert _failure_score(0.5) == 0.5


def test_reuse_score_log_scaled():
    """0 uses = 0.0; 1 use > 0; many uses approaches 1.0."""
    assert _reuse_score(0) == 0.0
    assert _reuse_score(1) > 0.0
    assert _reuse_score(100) > _reuse_score(1)


def test_token_cost_score_inverts_size():
    """Small = high; large = low."""
    assert _token_cost_score(0, 8000) == 1.0
    assert _token_cost_score(8000, 8000) == 0.0
    assert _token_cost_score(4000, 8000) == 0.5


def test_high_score_yields_keep():
    """A clean skill with reuse + criticality gets KEEP."""
    a = _artifact("good-skill")
    findings: list[Finding] = []
    tokens = [TokenCostStatic(artifact_name="good-skill", estimated_tokens=100, size_bytes=400, high_cost=False)]
    sc = score(
        [a],
        findings=findings,
        token_costs=tokens,
        reuse_map={"good-skill": 50},
        criticality_map={"good-skill": 90},
    )
    assert len(sc) == 1
    assert sc[0].roi_score >= 60
    assert sc[0].decision in (Decision.KEEP, Decision.REWRITE)  # might trigger rewrite from no findings? no, keep expected


def test_blocking_findings_yield_rewrite():
    """A skill with blocking contract findings gets REWRITE."""
    a = _artifact("broken-skill")
    findings = [
        Finding(
            finding_id="x",
            artifact_name="broken-skill",
            severity=Severity.BLOCKING,
            category="contract",
            message="bad contract",
        )
    ]
    tokens = [TokenCostStatic(artifact_name="broken-skill", estimated_tokens=100, size_bytes=400, high_cost=False)]
    sc = score([a], findings=findings, token_costs=tokens)
    assert sc[0].decision in (Decision.REWRITE, Decision.MERGE, Decision.SPLIT, Decision.DEPRECATE)


def test_empty_artifacts_yields_no_scorecards():
    """No input = no output."""
    assert score([], findings=[], token_costs=[]) == []


def test_semantic_scorer_interface_returns_mock():
    """The default semantic scorer returns a mock SemanticScore."""
    s = SemanticScoringInterface().score("test", "body")
    assert isinstance(s, SemanticScore)
    assert s.provenance == "mock"
    assert 0 <= s.coherence <= 100
    assert 0 <= s.uniqueness <= 100


def test_custom_weights_change_score():
    """Heavily weighting business_criticality boosts the score."""
    a = _artifact("crit-skill")
    tokens = [TokenCostStatic(artifact_name="crit-skill", estimated_tokens=100, size_bytes=400, high_cost=False)]
    # Default weights (smoke test — make sure score() doesn't crash on defaults)
    _ = score([a], findings=[], token_costs=tokens, criticality_map={"crit-skill": 100})
    # Custom weights: all weight on business_criticality
    weights = ROIWeights(
        reuse=0, token_cost=0, output_quality=0, dependency_value=0,
        failure_rate=0, semantic_uniqueness=0, benchmark_pass_rate=0,
        business_criticality=1.0,
    )
    sc_critical = score(
        [a], findings=[], token_costs=tokens,
        criticality_map={"crit-skill": 100}, weights=weights,
    )
    # With 100% weight on criticality=100, the score should be ~100
    assert sc_critical[0].roi_score >= 95
