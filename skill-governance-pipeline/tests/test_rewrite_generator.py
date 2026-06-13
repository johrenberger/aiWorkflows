"""Tests for the rewrite generator (CR 10)."""
from __future__ import annotations

from skill_governance.models import (
    ArtifactType,
    Decision,
    Finding,
    ScorecardEntry,
    Severity,
    SkillArtifact,
)
from skill_governance.rewrite_generator import (
    generate_rewrite,
    generate_rewrites,
)


def _artifact(name: str, body: str = "x" * 100) -> SkillArtifact:
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


def test_rewrite_is_none_when_no_triggers():
    """A clean artifact gets no rewrite."""
    a = _artifact("clean")
    assert generate_rewrite(a, findings=[]) is None


def test_rewrite_triggered_by_missing_metadata():
    """A metadata finding triggers a rewrite."""
    a = _artifact("needs-metadata")
    f = Finding(
        finding_id="x",
        artifact_name="needs-metadata",
        severity=Severity.BLOCKING,
        category="metadata",
        message="missing",
    )
    rw = generate_rewrite(a, findings=[f])
    assert rw is not None
    # Must contain all the required sections per CR 10
    for section in [
        "name:",
        "artifact_type:",
        "purpose:",
        "inputs:",
        "outputs:",
        "dependencies:",
        "Compatibility",
        "Validation expectations",
        "Token efficiency",
    ]:
        assert section in rw, f"Missing section: {section}"


def test_rewrite_triggered_by_vague_contract():
    """A contract finding triggers a rewrite."""
    a = _artifact("vague")
    f = Finding(
        finding_id="x",
        artifact_name="vague",
        severity=Severity.BLOCKING,
        category="contract",
        message="vague output",
    )
    rw = generate_rewrite(a, findings=[f])
    assert rw is not None
    assert "vague-contracts" in rw or "contract" in rw.lower()


def test_rewrite_triggered_by_high_token_cost():
    """Estimated tokens >= 8000 triggers a rewrite."""
    big_body = "x" * 40000  # ~10000 tokens
    a = _artifact("huge", body=big_body)
    rw = generate_rewrite(a, findings=[])
    assert rw is not None
    assert "high-token-cost" in rw


def test_rewrite_triggered_by_roi_decision():
    """A scorecard with decision=REWRITE triggers a rewrite."""
    a = _artifact("weak")
    sc = ScorecardEntry(
        artifact_name="weak",
        roi_score=40,
        decision=Decision.REWRITE,
        rationale="low score",
    )
    rw = generate_rewrite(a, findings=[], scorecard=sc)
    assert rw is not None


def test_generate_rewrites_writes_to_disk(tmp_path):
    """Rewrites land in proposed_rewrites/."""
    a = _artifact("needs-metadata")
    f = Finding(
        finding_id="x",
        artifact_name="needs-metadata",
        severity=Severity.BLOCKING,
        category="metadata",
        message="missing",
    )
    out = tmp_path / "output"
    rewrites = generate_rewrites([a], findings=[f], output_dir=out)
    assert "needs-metadata" in rewrites
    files = list((out / "proposed_rewrites").iterdir())
    assert len(files) == 1
    assert files[0].name.endswith(".rewrite.md")
