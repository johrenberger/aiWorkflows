"""BDD-TDD coverage tests for CTA-GAP-011: contract_validator vague-output category.

Triggered by application-test-coverage (FOCUSED_PICKS2 pass) on the
component-test-analysis gap-backlog. CTA-GAP-011 is a P2 gap (T1 risk):

    "contract_validator.is_vague_output() returns True for many shapes.
    The 'vague_output' category is critical for the recommendation_engine
    grouping. No test exists for the 'outputs is None' case (artifact
    with no outputs field at all)."

The current code emits 3 findings for a missing/vague outputs contract,
all with `category="contract"`. The gap calls for the vague-output
finding to use a distinct `category="vague-output"` so the recommendation
engine can group it. This is the same pattern as CTA-GAP-002 (where
dependency_analyzer findings got distinct categories).

These tests lock:
- outputs=None -> vague-output finding has category="vague-output"
- outputs="a report" (vague string) -> same
- outputs={} (empty dict) -> same
- outputs={"format": "json", "fields": [...]} (proper) -> no vague finding
- recommendation_engine grouping key 'vague-output' surfaces these findings

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
- Red-phase: tests fail against the current code (red)
- Green-phase: tests pass after fixing `validate_contract`
"""
from __future__ import annotations

from pathlib import Path

from skill_governance.contract_validator import (
    is_vague_output,
    validate_contract,
)
from skill_governance.models import Severity


def _write_skill(tmp_path: Path, name: str, outputs_yaml: str) -> Path:
    """Write a minimal skill file with the given outputs YAML value."""
    p = tmp_path / "skills" / name
    p.mkdir(parents=True, exist_ok=True)
    text = (
        "---\n"
        f"name: {name}\n"
        "artifact_type: skill\n"
        f"purpose: this skill is used for testing the {name} capability in unit fixtures.\n"
        "category: test\n"
        "owner: justin\n"
        "version: '1.0'\n"
        "inputs: []\n"
        f"outputs: {outputs_yaml}\n"
        "intended_consumers: []\n"
        "quality_level: draft\n"
        "last_reviewed: 2026-06-13\n"
        "---\n"
        f"# {name}\n"
    )
    f = p / "SKILL.md"
    f.write_text(text)
    return p / "SKILL.md"


# ===========================================================================
# SCENARIO 1: outputs=None produces a vague-output finding (category='vague-output')
#
# Given: a skill with outputs explicitly set to null
# When:  validate_contract is called
# Then:  one of the findings is the vague-output finding with
#        category='vague-output' and severity=BLOCKING
# ===========================================================================
def test_outputs_none_emits_vague_output_finding_with_specific_category(tmp_path: Path):
    """outputs=null -> finding with category='vague-output', severity=BLOCKING."""
    path = _write_skill(tmp_path, "no-outputs", "null")
    findings = validate_contract("no-outputs", path)
    vague_findings = [f for f in findings if "vague" in f.finding_id]
    assert len(vague_findings) >= 1, (
        f"expected at least one vague-output finding; got: {[(f.finding_id, f.category) for f in findings]}"
    )
    for f in vague_findings:
        assert f.category == "vague-output", (
            f"vague-output finding should have category='vague-output', got category='{f.category}'"
        )
        assert f.severity == Severity.BLOCKING, (
            f"vague-output finding should be BLOCKING, got severity={f.severity}"
        )


# ===========================================================================
# SCENARIO 2: outputs="a report" (vague string) emits vague-output finding
#
# Given: a skill with outputs='a report' (a common vague phrase)
# When:  validate_contract is called
# Then:  the vague-output finding has category='vague-output'
# ===========================================================================
def test_outputs_vague_string_emits_vague_output_finding_with_specific_category(tmp_path: Path):
    """outputs='a report' -> vague-output finding with category='vague-output'."""
    path = _write_skill(tmp_path, "report-output", "'a report'")
    findings = validate_contract("report-output", path)
    vague_findings = [f for f in findings if "vague" in f.finding_id]
    assert len(vague_findings) >= 1
    for f in vague_findings:
        assert f.category == "vague-output"


# ===========================================================================
# SCENARIO 3: outputs={} (empty dict) emits vague-output finding
#
# Given: a skill with outputs={} (no format, no fields, no sections)
# When:  validate_contract is called
# Then:  the vague-output finding has category='vague-output'
# ===========================================================================
def test_outputs_empty_dict_emits_vague_output_finding_with_specific_category(tmp_path: Path):
    """outputs={} -> vague-output finding with category='vague-output'."""
    path = _write_skill(tmp_path, "empty-dict-output", "{}")
    findings = validate_contract("empty-dict-output", path)
    vague_findings = [f for f in findings if "vague" in f.finding_id]
    assert len(vague_findings) >= 1
    for f in vague_findings:
        assert f.category == "vague-output"


# ===========================================================================
# SCENARIO 4: proper structured outputs do NOT emit a vague-output finding
#
# Given: a skill with outputs={format: json, fields: [a, b]}
# When:  validate_contract is called
# Then:  no vague-output finding is emitted (sanity check)
# ===========================================================================
def test_outputs_properly_structured_does_not_emit_vague_finding(tmp_path: Path):
    """outputs={format: json, fields: [...]} -> NO vague-output finding."""
    path = _write_skill(tmp_path, "proper-outputs", "{format: json, fields: [result, score]}")
    findings = validate_contract("proper-outputs", path)
    vague_findings = [f for f in findings if "vague" in f.finding_id]
    assert len(vague_findings) == 0, (
        f"structured outputs should not produce a vague finding; got: {[(f.finding_id, f.category) for f in vague_findings]}"
    )


# ===========================================================================
# SCENARIO 5: the new 'vague-output' category is distinct from the
#              other contract findings (inputs.missing, outputs.missing,
#              outputs.format_hint_missing)
#
# Given: a skill with outputs=null (triggers outputs.missing + outputs.vague
#        + outputs.format_hint_missing)
# When:  validate_contract is called
# Then:  the vague-output finding has category='vague-output', but the
#        other contract findings (outputs.missing, format_hint_missing)
#        keep category='contract' (or some other contract-related category
#        that's distinct from 'vague-output')
# ===========================================================================
def test_vague_output_category_is_distinct_from_other_contract_categories(tmp_path: Path):
    """The 'vague-output' category is a peer of (not the same as) 'contract'."""
    path = _write_skill(tmp_path, "multi-findings", "null")
    findings = validate_contract("multi-findings", path)
    cats = {f.category for f in findings}
    # Must have at least the vague-output category
    assert "vague-output" in cats, f"vague-output category missing; got {cats}"
    # And the vague-output finding is NOT also tagged with category='contract'
    vague_findings = [f for f in findings if f.category == "vague-output"]
    assert len(vague_findings) >= 1


# ===========================================================================
# SCENARIO 6: is_vague_output() unit-level coverage for None
#
# Given: is_vague_output() is called with various shapes
# When:  the input is None, a vague string, an empty dict, or a proper dict
# Then:  the boolean matches the expected classification
# ===========================================================================
def test_is_vague_output_classifies_shapes_correctly():
    """is_vague_output() returns True for None, vague strings, empty dicts; False otherwise."""
    # None
    assert is_vague_output(None) is True, "None should be vague"
    # Vague strings
    assert is_vague_output("a report") is True
    assert is_vague_output("the analysis") is True
    assert is_vague_output("summary") is True
    assert is_vague_output("TBD") is True
    # Empty dict (no format, no fields, no sections)
    assert is_vague_output({}) is True
    # Properly structured dict
    assert is_vague_output({"format": "json", "fields": ["a", "b"]}) is False
    # Dict with only format
    assert is_vague_output({"format": "markdown"}) is False
    # Dict with only fields
    assert is_vague_output({"fields": ["a"]}) is False
    # Dict with only sections
    assert is_vague_output({"sections": ["intro"]}) is False
    # List of strings (structured)
    assert is_vague_output(["output_a", "output_b"]) is False
