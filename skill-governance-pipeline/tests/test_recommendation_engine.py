"""Tests for the recommendation engine (CR 11)."""
from __future__ import annotations

from skill_governance.models import (
    Decision,
    Finding,
    OverlapPair,
    OverlapRecommendation,
    ResponsibilityFlag,
    ResponsibilityReport,
    Severity,
)
from skill_governance.recommendation_engine import generate


def test_recommendation_for_blocking_finding():
    """A blocking finding produces a non-KEEP recommendation."""
    f = Finding(
        finding_id="x",
        artifact_name="bad-skill",
        severity=Severity.BLOCKING,
        category="metadata",
        message="missing",
    )
    recs = generate([f])
    assert len(recs) == 1
    assert recs[0].affected_artifacts == ["bad-skill"]
    assert recs[0].decision != Decision.KEEP
    assert "blocking" in recs[0].evidence


def test_merge_recommendation_from_overlap_pair():
    """An overlap pair with score >= 85 produces a merge recommendation."""
    p = OverlapPair(
        artifact_a="skills/alpha",
        artifact_b="skills/beta",
        overlap_score=90,
        rationale="high overlap",
        recommendation=OverlapRecommendation.MERGE,
    )
    recs = generate([], overlap_pairs=[p])
    assert any(r.decision == Decision.MERGE for r in recs)
    merge_rec = next(r for r in recs if r.decision == Decision.MERGE)
    assert "skills/alpha" in merge_rec.affected_artifacts
    assert "skills/beta" in merge_rec.affected_artifacts


def test_split_recommendation_from_over_broad():
    """An over-broad responsibility produces a split recommendation."""
    r = ResponsibilityReport(
        artifact_name="skills/do-everything",
        responsibility_score=20,
        flag=ResponsibilityFlag.OVER_BROAD,
        rationale="too many actions",
    )
    recs = generate([], responsibility=[r])
    assert any(rec.decision == Decision.SPLIT for rec in recs)
    split_rec = next(rec for rec in recs if rec.decision == Decision.SPLIT)
    assert "skills/do-everything" in split_rec.affected_artifacts


def test_recommendation_has_all_required_fields():
    """Every recommendation has all 11 required fields per CR 11."""
    f = Finding(
        finding_id="x",
        artifact_name="a",
        severity=Severity.BLOCKING,
        category="x",
        message="x",
    )
    recs = generate([f])
    r = recs[0]
    for field in [
        "recommendation_id",
        "affected_artifacts",
        "decision",
        "priority",
        "rationale",
        "evidence",
        "estimated_token_impact",
        "estimated_quality_impact",
        "implementation_effort",
        "risk",
        "ci_impact",
        "proposed_next_action",
    ]:
        assert hasattr(r, field), f"Missing field: {field}"


def test_recommendations_sorted_by_priority():
    """Recommendations come back in priority order (1 = highest)."""
    f_high = Finding(
        finding_id="high", artifact_name="a",
        severity=Severity.BLOCKING, category="x", message="x",
    )
    f_warn = Finding(
        finding_id="warn", artifact_name="b",
        severity=Severity.WARNING, category="x", message="x",
    )
    recs = generate([f_high, f_warn])
    priorities = [r.priority for r in recs]
    assert priorities == sorted(priorities)
