"""Tests for the contract validator (CR 3).

BDD:
- Given a skill defines structured inputs and outputs
  When contract validation runs
  Then it passes
- Given a skill says 'produce a report'
  When contract validation runs
  Then it fails contract validation
"""
from __future__ import annotations

from pathlib import Path

from skill_governance.contract_validator import (
    has_structured_format_hint,
    is_vague_output,
    validate_contract,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_skill_passes_contract_validation():
    """A well-structured skill produces no findings."""
    findings = validate_contract("valid", FIXTURES / "sample_skills/valid/SKILL.md")
    assert findings == []


def test_vague_output_is_blocking():
    """Outputs = 'a report' is vague and produces a BLOCKING finding."""
    findings = validate_contract("vague", FIXTURES / "sample_skills/vague-output/SKILL.md")
    msgs = [f.message for f in findings]
    assert any("vague" in m for m in msgs)
    # Vague output is blocking
    severities = [f.severity.value for f in findings]
    assert "blocking" in severities


def test_missing_outputs_is_blocking():
    """A skill with no outputs at all is BLOCKING."""
    findings = validate_contract("missing-outputs", FIXTURES / "sample_skills/missing-metadata/SKILL.md")
    assert any(f.severity.value == "blocking" for f in findings)


def test_vague_output_string_variants():
    """Common vague outputs are detected as vague."""
    for vague in ["a report", "the report", "analysis", "summary", "a summary", "TBD"]:
        assert is_vague_output(vague) is True, f"Failed to flag: {vague!r}"


def test_structured_output_passes_vague_check():
    """A dict with format + fields is not vague."""
    assert is_vague_output({"format": "json", "fields": ["a", "b"]}) is False
    assert is_vague_output(["output_a", "output_b"]) is False


def test_format_hint_required_for_dict_outputs():
    """A dict output without format/fields/sections is suspect."""
    assert has_structured_format_hint({"format": "json"}) is True
    assert has_structured_format_hint({"fields": ["a"]}) is True
    assert has_structured_format_hint({"sections": ["a"]}) is True
    assert has_structured_format_hint({}) is False
    assert has_structured_format_hint({"weird_key": "v"}) is False
