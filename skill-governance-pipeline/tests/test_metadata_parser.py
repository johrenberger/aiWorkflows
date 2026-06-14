"""Tests for the metadata parser (CR 2)."""
from __future__ import annotations

from pathlib import Path

from skill_governance.metadata_parser import parse_metadata

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_complete_frontmatter():
    """A file with all required fields parses cleanly."""
    md = parse_metadata(FIXTURES / "sample_skills/valid/SKILL.md")
    assert md.name == "valid-skill"
    assert md.artifact_type == "skill"
    assert md.purpose and len(md.purpose) > 20
    assert md.category == "validation"
    assert md.owner == "justin"
    assert md.version == "1.0.0"
    assert isinstance(md.inputs, list)
    assert isinstance(md.outputs, dict)
    assert md.dependencies == ["test-factory"]
    assert md.quality_level == "usable"
    assert md.last_reviewed == "2026-06-13"
    assert md.missing_fields() == []


def test_missing_file_returns_empty_metadata():
    """A file with no frontmatter returns empty metadata."""
    md = parse_metadata(FIXTURES / "sample_skills/missing-metadata/SKILL.md")
    assert md.name is None
    assert md.purpose is None
    missing = md.missing_fields()
    assert "name" in missing
    assert "purpose" in missing
    assert "outputs" in missing
    assert md.is_purpose_vague() is True


def test_purpose_vagueness_detection():
    """Short or generic purposes are flagged as vague."""
    from skill_governance.metadata_parser import parse_metadata
    # Use the valid file and confirm its purpose is NOT vague
    md = parse_metadata(FIXTURES / "sample_skills/valid/SKILL.md")
    assert md.is_purpose_vague() is False


def test_string_dependencies_are_split():
    """A comma-separated string in `dependencies` becomes a list."""
    import tempfile

    from skill_governance.metadata_parser import parse_metadata
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("---\nname: t\nartifact_type: skill\npurpose: a sufficiently long and meaningful purpose text.\ncategory: test\nowner: me\nversion: '1.0'\ninputs:\n  - x\noutputs:\n  format: json\ndependencies: a, b, c\nintended_consumers: d\nquality_level: draft\nlast_reviewed: 2026-06-13\n---\n# body\n")
        f.flush()
        md = parse_metadata(Path(f.name))
    assert md.dependencies == ["a", "b", "c"]


def test_has_structured_contracts_only_when_dict_or_list():
    """Structured contracts are dicts or lists, not free-text strings."""
    import tempfile

    from skill_governance.metadata_parser import parse_metadata
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("---\nname: t\nartifact_type: skill\npurpose: a sufficiently long and meaningful purpose text.\ncategory: test\nowner: me\nversion: '1.0'\ninputs: 'some file'\noutputs: 'a report'\ndependencies: []\nintended_consumers: []\nquality_level: draft\nlast_reviewed: 2026-06-13\n---\n# body\n")
        f.flush()
        md = parse_metadata(Path(f.name))
    assert md.has_structured_contracts() is False
