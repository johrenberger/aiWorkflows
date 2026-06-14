"""BDD-TDD tests for report_generator.py.

Triggered by gap scan: report_generator.py (227 lines) had 0 tests
despite being the user-facing output of the entire pipeline.

Method: BDD-TDD
- Given/When/Then in each docstring
- Function name = assertion
- Each test asserts on a specific structural property of the
  generated report so a format change breaks the test
"""
from __future__ import annotations

from pathlib import Path

from skill_governance.models import (
    ArtifactType,
    Decision,
    Finding,
    PipelineResult,
    ScorecardEntry,
    Severity,
    SkillArtifact,
)


def _artifact(name: str, artifact_type=ArtifactType.SKILL) -> SkillArtifact:
    return SkillArtifact(
        name=name,
        path=name + ".md",
        artifact_type=artifact_type,
        size_bytes=100,
        estimated_tokens=25,
        content_hash="x" * 64,
        modified_timestamp="2026-06-13T00:00:00Z",
        body_excerpt="test",
    )


def _finding(artifact: str, severity: Severity = Severity.BLOCKING) -> Finding:
    return Finding(
        finding_id=f"f-{artifact}",
        artifact_name=artifact,
        severity=severity,
        category="metadata",
        message=f"missing field on {artifact}",
    )


def _empty_result() -> PipelineResult:
    return PipelineResult(
        started_at="2026-06-13T00:00:00Z",
        finished_at="2026-06-13T00:01:00Z",
        ci_passed=True,
        health_score=85,
    )


# ===========================================================================
# SCENARIO 1: write_reports returns the 5 expected report paths
#
# Given: an empty PipelineResult
# When:  write_reports is called
# Then:  the returned dict has 5 entries: executive, technical, backlog,
#        scorecard, findings
# ===========================================================================
def test_write_reports_returns_five_paths(tmp_path: Path):
    """write_reports returns 5 paths for the 5 report files."""
    from skill_governance.report_generator import write_reports

    paths = write_reports(_empty_result(), tmp_path)
    assert set(paths.keys()) == {
        "executive",
        "technical",
        "backlog",
        "scorecard",
        "findings",
    }, f"Expected 5 paths, got {set(paths.keys())}"


# ===========================================================================
# SCENARIO 2: all 5 report files are created on disk
#
# Given: an empty PipelineResult and a tmp directory
# When:  write_reports is called
# Then:  all 5 files exist on disk
# ===========================================================================
def test_write_reports_creates_five_files_on_disk(tmp_path: Path):
    """write_reports writes 5 files to disk."""
    from skill_governance.report_generator import write_reports

    paths = write_reports(_empty_result(), tmp_path)
    for name, path in paths.items():
        assert path.exists(), f"Report {name} not written: {path}"
        assert path.stat().st_size > 0, f"Report {name} is empty: {path}"


# ===========================================================================
# SCENARIO 3: executive report contains health score and CI status
#
# Given: a PipelineResult with health_score=85 and ci_passed=True
# When:  write_reports is called
# Then:  the executive report contains "Health score: 85/100" and
#        "CI status: PASS"
# ===========================================================================
def test_executive_report_includes_health_score_and_ci_status(tmp_path: Path):
    """Executive report shows health score and CI status."""
    from skill_governance.report_generator import write_reports

    paths = write_reports(_empty_result(), tmp_path)
    text = paths["executive"].read_text()
    assert "85/100" in text, f"Health score 85/100 missing from executive: {text[:500]}"
    assert "PASS" in text, f"CI status PASS missing from executive: {text[:500]}"


# ===========================================================================
# SCENARIO 4: executive report counts skills and agents separately
#
# Given: a PipelineResult with 2 skills and 1 agent
# When:  write_reports is called
# Then:  the executive report contains "Total skills: 2" and
#        "Total agents: 1"
# ===========================================================================
def test_executive_report_counts_skills_and_agents_separately(tmp_path: Path):
    """Executive report counts skills and agents separately."""
    from skill_governance.report_generator import write_reports

    result = _empty_result()
    result.inventory = [
        _artifact("skill-a", ArtifactType.SKILL),
        _artifact("skill-b", ArtifactType.SKILL),
        _artifact("agent-x", ArtifactType.AGENT),
    ]
    paths = write_reports(result, tmp_path)
    text = paths["executive"].read_text()
    assert "Total skills:** 2" in text, f"Expected 'Total skills:** 2' in executive: {text[:500]}"
    assert "Total agents:** 1" in text, f"Expected 'Total agents:** 1' in executive: {text[:500]}"


# ===========================================================================
# SCENARIO 5: technical report lists all findings in a table
#
# Given: a PipelineResult with 2 findings
# When:  write_reports is called
# Then:  the technical report contains a "Findings" section with
#        one row per finding, including severity and message
# ===========================================================================
def test_technical_report_lists_findings_in_table(tmp_path: Path):
    """Technical report renders findings in a markdown table."""
    from skill_governance.report_generator import write_reports

    result = _empty_result()
    result.findings = [
        _finding("skill-a", Severity.BLOCKING),
        _finding("skill-b", Severity.WARNING),
    ]
    paths = write_reports(result, tmp_path)
    text = paths["technical"].read_text()
    assert "## Findings" in text, f"Expected '## Findings' section in technical: {text[:500]}"
    assert "blocking" in text, "Expected 'blocking' in technical report"
    assert "warning" in text, "Expected 'warning' in technical report"
    assert "skill-a" in text, "Expected 'skill-a' in technical report"
    assert "skill-b" in text, "Expected 'skill-b' in technical report"


# ===========================================================================
# SCENARIO 6: technical report renders inventory as a table
#
# Given: a PipelineResult with 2 artifacts
# When:  write_reports is called
# Then:  the technical report contains a "Inventory" section listing
#        both artifacts by name, with their artifact_type
# ===========================================================================
def test_technical_report_renders_inventory_table(tmp_path: Path):
    """Technical report renders inventory as a markdown table."""
    from skill_governance.report_generator import write_reports

    result = _empty_result()
    result.inventory = [
        _artifact("alpha", ArtifactType.SKILL),
        _artifact("beta", ArtifactType.AGENT),
    ]
    paths = write_reports(result, tmp_path)
    text = paths["technical"].read_text()
    assert "## Inventory" in text, f"Expected '## Inventory' section in technical: {text[:500]}"
    assert "alpha" in text, "Expected 'alpha' in inventory"
    assert "beta" in text, "Expected 'beta' in inventory"
    assert "skill" in text, "Expected 'skill' (artifact type) in inventory"
    assert "agent" in text, "Expected 'agent' (artifact type) in inventory"


# ===========================================================================
# SCENARIO 7: backlog sorts recommendations by priority (1 = highest)
#
# Given: a PipelineResult with 3 recommendations at different priorities
# When:  write_reports is called
# Then:  the backlog file lists them in priority order with the
#        highest-priority item first
# ===========================================================================
def test_remediation_backlog_sorts_by_priority(tmp_path: Path):
    """Backlog sorts recommendations by priority (1=highest)."""
    from skill_governance.models import Recommendation
    from skill_governance.report_generator import write_reports

    result = _empty_result()
    result.recommendations = [
        Recommendation(
            recommendation_id="rec-low",
            affected_artifacts=["z"],
            decision=Decision.KEEP,
            priority=5,
            rationale="low",
            evidence={},
            estimated_token_impact=0,
            estimated_quality_impact=0,
            implementation_effort="S",
            risk="low",
            ci_impact="warning",
            proposed_next_action="later",
        ),
        Recommendation(
            recommendation_id="rec-high",
            affected_artifacts=["a"],
            decision=Decision.REWRITE,
            priority=1,
            rationale="high",
            evidence={},
            estimated_token_impact=0,
            estimated_quality_impact=10,
            implementation_effort="L",
            risk="high",
            ci_impact="blocking",
            proposed_next_action="now",
        ),
    ]
    paths = write_reports(result, tmp_path)
    text = paths["backlog"].read_text()
    # High-priority should appear before low-priority in the file
    pos_high = text.find("rec-high")
    pos_low = text.find("rec-low")
    assert pos_high >= 0, "rec-high not in backlog"
    assert pos_low >= 0, "rec-low not in backlog"
    assert pos_high < pos_low, "Expected rec-high before rec-low (by priority)"


# ===========================================================================
# SCENARIO 8: skill_scorecard.json contains all scorecards
#
# Given: a PipelineResult with 2 scorecards
# When:  write_reports is called
# Then:  the skill_scorecard.json file is valid JSON with 2 entries
# ===========================================================================
def test_skill_scorecard_json_contains_all_scorecards(tmp_path: Path):
    """skill_scorecard.json has one entry per ScorecardEntry."""
    import json

    from skill_governance.report_generator import write_reports

    result = _empty_result()
    result.scorecards = [
        ScorecardEntry(
            artifact_name="skill-a", roi_score=80, decision=Decision.KEEP, rationale="good"
        ),
        ScorecardEntry(
            artifact_name="skill-b", roi_score=20, decision=Decision.DEPRECATE, rationale="bad"
        ),
    ]
    paths = write_reports(result, tmp_path)
    data = json.loads(paths["scorecard"].read_text())
    assert isinstance(data, list), f"Expected list in scorecard JSON, got {type(data)}"
    assert len(data) == 2, f"Expected 2 scorecard entries, got {len(data)}"
    names = {e.get("artifact_name") for e in data}
    assert names == {"skill-a", "skill-b"}, f"Expected both scorecards, got {names}"
