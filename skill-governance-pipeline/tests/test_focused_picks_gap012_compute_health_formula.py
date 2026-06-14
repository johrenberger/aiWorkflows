"""BDD-TDD coverage tests for CTA-GAP-012: cli._compute_health formula.

Triggered by application-test-coverage (FOCUSED_PICKS pass) on the
component-test-analysis gap-backlog. CTA-GAP-012 is a P1 gap (T1 risk):

    "cli._compute_health returns (clean_count, broken_count) but the
    per-artifact health formula is computed inside, not extracted.
    Need tests that exercise the formula directly."

The current `_compute_health` returns `(health_score, blocking_count)`.
The formula is:
    score = round(100 * clean/n + 80 * ugly/n + 30 * broken/n)
where:
    - clean = artifacts with no findings
    - ugly  = artifacts with findings, but no structural blocking
    - broken = artifacts with at least one structural blocking finding
    (structural = category NOT in {metadata, discovery})
    - n = total artifacts

These tests pin the formula for known inputs so a future refactor
that extracts the formula can't silently change the shape.

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

from pathlib import Path

from skill_governance.cli import _compute_health
from skill_governance.config_loader import load_config
from skill_governance.discovery import DiscoveryConfig, discover
from skill_governance.models import (
    ArtifactType,
    Finding,
    PipelineResult,
    Severity,
    SkillArtifact,
)


def _artifact(name: str, path: str) -> SkillArtifact:
    return SkillArtifact(
        name=name,
        path=path,
        artifact_type=ArtifactType.SKILL,
        size_bytes=100,
        estimated_tokens=25,
        content_hash="x" * 64,
        modified_timestamp="2026-06-13T00:00:00Z",
        body_excerpt="test",
    )


def _make_result(artifacts: list[SkillArtifact], findings: list[Finding]) -> PipelineResult:
    return PipelineResult(inventory=artifacts, findings=findings)


def _stub_config():
    """A minimal config object for _compute_health.

    _compute_health takes (result, active_waivers, config). It only uses
    the config to identify structural vs cosmetic categories (the same
    hardcoded list, 'metadata'/'discovery', is the truth source for
    cosmetic). So an empty config object is fine for the formula test.
    """
    return type("StubConfig", (), {})()


# ===========================================================================
# SCENARIO 1: empty catalog -> health 100, blocking 0
#
# Given: an empty inventory (n=0)
# When:  _compute_health is called
# Then:  it returns (100, 0) (no artifacts, no findings, full health)
# ===========================================================================
def test_empty_catalog_returns_perfect_health():
    """n=0 -> health=100, blocking=0 (no catalog to grade)."""
    result = _make_result([], [])
    score, blocking = _compute_health(result, [], _stub_config())
    assert score == 100, f"empty catalog should have health=100, got {score}"
    assert blocking == 0, f"empty catalog should have blocking=0, got {blocking}"


# ===========================================================================
# SCENARIO 2: all-clean catalog -> health 100, blocking 0
#
# Given: N artifacts, no findings
# When:  _compute_health is called
# Then:  it returns (100, 0) (all clean)
# ===========================================================================
def test_all_clean_catalog_returns_perfect_health():
    """All artifacts clean -> health=100, blocking=0."""
    artifacts = [
        _artifact("a", "skills/a.md"),
        _artifact("b", "skills/b.md"),
        _artifact("c", "skills/c.md"),
    ]
    result = _make_result(artifacts, [])
    score, blocking = _compute_health(result, [], _stub_config())
    assert score == 100, f"all-clean catalog should have health=100, got {score}"
    assert blocking == 0, f"all-clean catalog should have blocking=0, got {blocking}"


# ===========================================================================
# SCENARIO 3: all-broken catalog -> health 30, blocking N
#
# Given: N artifacts, each with one structural blocking finding
# When:  _compute_health is called
# Then:  it returns (30, N) (all broken -> 100*0 + 80*0 + 30*1 = 30)
# ===========================================================================
def test_all_broken_catalog_returns_low_health():
    """All artifacts have one structural blocking finding -> health=30, blocking=N."""
    artifacts = [
        _artifact("a", "skills/a.md"),
        _artifact("b", "skills/b.md"),
    ]
    findings = [
        Finding(
            finding_id=f"contract.broken.{a.name}",
            artifact_name=a.name,
            artifact_path=a.path,
            severity=Severity.BLOCKING,
            category="contract",  # structural (not metadata/discovery)
            message=f"{a.name} is broken",
        )
        for a in artifacts
    ]
    result = _make_result(artifacts, findings)
    score, blocking = _compute_health(result, [], _stub_config())
    assert score == 30, f"all-broken catalog should have health=30, got {score}"
    assert blocking == 2, f"all-broken catalog should have blocking=2, got {blocking}"


# ===========================================================================
# SCENARIO 4: all-ugly catalog (cosmetic findings only) -> health 80
#
# Given: N artifacts, each with one cosmetic finding (metadata or discovery)
# When:  _compute_health is called
# Then:  it returns (80, N) (all ugly -> 100*0 + 80*1 + 30*0 = 80)
# ===========================================================================
def test_all_ugly_cosmetic_catalog_returns_eighty_health():
    """All artifacts have a cosmetic blocking finding (metadata) -> health=80, blocking=N."""
    artifacts = [
        _artifact("a", "skills/a.md"),
        _artifact("b", "skills/b.md"),
    ]
    findings = [
        Finding(
            finding_id=f"metadata.missing.{a.name}",
            artifact_name=a.name,
            artifact_path=a.path,
            severity=Severity.BLOCKING,
            category="metadata",  # cosmetic
            message=f"{a.name} missing fields",
        )
        for a in artifacts
    ]
    result = _make_result(artifacts, findings)
    score, blocking = _compute_health(result, [], _stub_config())
    assert score == 80, f"all-ugly catalog should have health=80, got {score}"
    assert blocking == 2, f"blocking count is independent of category, got {blocking}"


# ===========================================================================
# SCENARIO 5: mixed catalog with known weights
#
# Given: 3 artifacts: 1 clean, 1 ugly (cosmetic), 1 broken (structural)
# When:  _compute_health is called
# Then:  score = round(100*1/3 + 80*1/3 + 30*1/3) = round(70) = 70
# ===========================================================================
def test_mixed_catalog_weighted_score():
    """1 clean + 1 ugly + 1 broken -> score=round((100+80+30)/3)=70."""
    a_clean = _artifact("clean", "skills/clean.md")
    a_ugly = _artifact("ugly", "skills/ugly.md")
    a_broken = _artifact("broken", "skills/broken.md")
    artifacts = [a_clean, a_ugly, a_broken]
    findings = [
        Finding(
            finding_id="metadata.missing.ugly",
            artifact_name="ugly",
            artifact_path="skills/ugly.md",
            severity=Severity.BLOCKING,
            category="metadata",
            message="ugly",
        ),
        Finding(
            finding_id="contract.broken.broken",
            artifact_name="broken",
            artifact_path="skills/broken.md",
            severity=Severity.BLOCKING,
            category="contract",
            message="broken",
        ),
    ]
    result = _make_result(artifacts, findings)
    score, blocking = _compute_health(result, [], _stub_config())
    # 1 clean (100), 1 ugly (80), 1 broken (30) -> avg = 70
    assert score == 70, f"expected health=70 for (1,1,1) split, got {score}"
    assert blocking == 2, f"expected 2 blocking findings, got {blocking}"


# ===========================================================================
# SCENARIO 6: warnings don't shift the artifact's bucket (ugly vs broken)
#
# Given: 2 artifacts: 1 with a structural WARNING, 1 with a cosmetic WARNING
# When:  _compute_health is called
# Then:  both are 'ugly' (no structural blocking) -> health=80
# ===========================================================================
def test_warnings_dont_promote_to_broken_bucket():
    """Warnings (non-blocking) keep the artifact in the 'ugly' bucket, not 'broken'."""
    a1 = _artifact("w1", "skills/w1.md")
    a2 = _artifact("w2", "skills/w2.md")
    artifacts = [a1, a2]
    findings = [
        Finding(
            finding_id="contract.warning.w1",
            artifact_name="w1",
            artifact_path="skills/w1.md",
            severity=Severity.WARNING,
            category="contract",
            message="warned but not broken",
        ),
        Finding(
            finding_id="metadata.warning.w2",
            artifact_name="w2",
            artifact_path="skills/w2.md",
            severity=Severity.WARNING,
            category="metadata",
            message="cosmetic warning",
        ),
    ]
    result = _make_result(artifacts, findings)
    score, blocking = _compute_health(result, [], _stub_config())
    # Both ugly (no blocking structural) -> 100*0 + 80*2/2 + 30*0 = 80
    assert score == 80, f"warnings shouldn't promote to broken; expected 80, got {score}"
    assert blocking == 0, f"warnings are not blocking; expected 0, got {blocking}"


# ===========================================================================
# SCENARIO 7: discovery-category blocking findings are also 'ugly' (cosmetic)
#
# Given: 1 artifact with one discovery-category BLOCKING finding
# When:  _compute_health is called
# Then:  the artifact is 'ugly' (not 'broken') -> health=80
# ===========================================================================
def test_discovery_category_blocking_is_cosmetic():
    """Blocking findings in 'discovery' category are treated as cosmetic (ugly, not broken)."""
    a = _artifact("a", "skills/a.md")
    artifacts = [a]
    findings = [
        Finding(
            finding_id="untyped.skipped.a",
            artifact_name="a",
            artifact_path="skills/a.md",
            severity=Severity.BLOCKING,
            category="discovery",  # cosmetic
            message="untyped",
        ),
    ]
    result = _make_result(artifacts, findings)
    score, blocking = _compute_health(result, [], _stub_config())
    assert score == 80, f"discovery-category blocking should be 'ugly'; expected 80, got {score}"
    assert blocking == 1, f"blocking count is per-finding, expected 1, got {blocking}"


# ===========================================================================
# SCENARIO 8: waived findings reduce the blocking count
#
# Given: 1 artifact with a structural blocking finding that is waived
# When:  _compute_health is called with an active waiver matching the finding_id
# Then:  the blocking count is reduced (effective blocking = 0)
#         [Note: current code reduces the blocking COUNT but does NOT
#          reclassify the artifact's bucket. The score remains 30 because
#          the bucket classification in _compute_health iterates over
#          all findings without filtering waived ones. The docstring
#          implies waivers should drag the score down, but the
#          implementation only adjusts the count. This test locks the
#          current count-based behavior; a future fix could align the
#          bucket classification with the docstring.]
# ===========================================================================
def test_waived_findings_reduce_blocking_count():
    """Waivers reduce the effective blocking count (the score's bucket classification is a separate concern)."""
    from skill_governance.models import Waiver

    a = _artifact("a", "skills/a.md")
    artifacts = [a]
    findings = [
        Finding(
            finding_id="contract.broken.a",
            artifact_name="a",
            artifact_path="skills/a.md",
            severity=Severity.BLOCKING,
            category="contract",
            message="broken but waived",
        ),
    ]
    waiver = Waiver(
        waiver_id="w-1",
        finding_id="contract.broken.a",
        owner="test",
        expiration_date="2099-01-01",
        rationale="test waiver",
        approved_by="test",
    )
    result = _make_result(artifacts, findings)
    score, blocking = _compute_health(result, [waiver], _stub_config())
    # The blocking count is reduced: 0 effective blocking findings
    assert blocking == 0, f"waived finding should reduce blocking; expected 0, got {blocking}"
    # Score remains 30 (artifact classified as 'broken' because the bucket
    # classification does not filter waived findings). This is the
    # current behavior; see the test docstring for context.
    assert score == 30, f"current code keeps score=30 even with waiver; expected 30, got {score}"
