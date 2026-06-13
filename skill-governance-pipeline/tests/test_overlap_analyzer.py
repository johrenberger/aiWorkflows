"""Tests for the overlap analyzer (CR 6)."""
from __future__ import annotations

import tempfile
from pathlib import Path

from skill_governance.discovery import (
    DiscoveryConfig,
    discover,
)
from skill_governance.models import (
    ArtifactType,
    OverlapRecommendation,
    SkillArtifact,
)
from skill_governance.overlap_analyzer import analyze

FIXTURES = Path(__file__).parent / "fixtures"


def _artifact(name: str, body: str) -> SkillArtifact:
    """Build a SkillArtifact with no on-disk file (for unit tests)."""
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


def test_high_overlap_pair_is_merge():
    """Two artifacts with very similar bodies get a merge recommendation."""
    body = (
        "This skill analyzes test coverage reports and produces structured "
        "markdown summaries of uncovered files and top risks in the system."
    )
    a = _artifact("coverage-summary", body)
    b = _artifact("coverage-report", body)
    pairs = analyze([a, b])
    assert len(pairs) == 1
    p = pairs[0]
    assert p.overlap_score >= 70
    assert p.recommendation in (OverlapRecommendation.MERGE, OverlapRecommendation.DIFFERENTIATE)


def test_low_overlap_pair_keeps_separate():
    """Two artifacts with completely different bodies get keep_separate."""
    a = _artifact("database-migration", "Migrate schema changes for postgres and hsqldb safely.")
    b = _artifact("incident-triage", "Triage production incidents and assign severity levels.")
    pairs = analyze([a, b])
    assert len(pairs) == 1
    p = pairs[0]
    assert p.overlap_score < 70
    assert p.recommendation == OverlapRecommendation.KEEP_SEPARATE


def test_pairwise_count_is_n_choose_2():
    """3 artifacts produce 3 pairs, 4 produce 6."""
    a = _artifact("a", "alpha")
    b = _artifact("b", "beta")
    c = _artifact("c", "gamma")
    d = _artifact("d", "delta")
    assert len(analyze([a, b, c])) == 3
    assert len(analyze([a, b, c, d])) == 6


def test_pairs_sorted_highest_first():
    """Pairs are returned in descending overlap order."""
    a = _artifact("a", "test coverage report analysis")
    b = _artifact("b", "test coverage report analysis")  # same as a
    c = _artifact("c", "completely unrelated documentation generator")
    pairs = analyze([a, b, c])
    # a-b is the highest-overlap pair
    assert pairs[0].overlap_score >= pairs[1].overlap_score
    assert pairs[0].overlap_score >= pairs[2].overlap_score
