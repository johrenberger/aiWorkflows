"""BDD-TDD coverage tests for CTA-GAP-013: Finding.artifact_path is set correctly.

Triggered by application-test-coverage (FOCUSED_PICKS pass) on the
component-test-analysis gap-backlog. CTA-GAP-013 is a P1 gap (T1 risk):

    "models.Finding has a Finding.artifact_path field (added in Phase 6)
    but no test asserts on the artifact_path being set correctly. Risk:
    downstream consumers (e.g. ci_gate, _compute_health, the JSON output
    files) rely on artifact_path to group findings by source file; if
    it's None or wrong, the grouping is broken."

The current behavior:
- cli._validate_one stamps artifact_path on every finding at the end.
- graph_to_findings (dependency_analyzer) does NOT stamp artifact_path.
- benchmark_findings (benchmark_runner) — check
- other analyzers — check

These tests lock the contract: every finding produced by the pipeline
should have a non-None artifact_path that matches the source artifact's
path (or be explicitly None for findings that don't originate from a
specific file, e.g. cross-artifact dependency findings).

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from skill_governance.cli import _validate_one
from skill_governance.contract_validator import validate_contract
from skill_governance.discovery import (
    DiscoveryConfig,
    discover,
)
from skill_governance.models import (
    ArtifactType,
    SkillArtifact,
)


def _make_skill(tmp_path: Path, name: str, body: str = "") -> Path:
    """Write a minimal skill file."""
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
        "outputs: {format: json, fields: []}\n"
        "dependencies: []\n"
        "intended_consumers: []\n"
        "quality_level: draft\n"
        "last_reviewed: 2026-06-13\n"
        "---\n"
        f"# {name}\n{body}\n"
    )
    f = p / "SKILL.md"
    f.write_text(text)
    return f


# ===========================================================================
# SCENARIO 1: validate_one stamps artifact_path on metadata findings
#
# Given: an artifact with missing required metadata fields
# When:  _validate_one is called
# Then:  the resulting 'metadata.missing' finding has artifact_path set
# ===========================================================================
def test_validate_one_stamps_artifact_path_on_metadata_finding():
    """A missing-fields finding produced by _validate_one has artifact_path set."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Write a file that is missing required frontmatter fields
        p = root / "skills" / "broken"
        p.mkdir(parents=True, exist_ok=True)
        (p / "SKILL.md").write_text("---\nname: broken\n---\n# broken\n")
        # Build the artifact as discovery would
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        assert len(artifacts) >= 1
        findings = _validate_one(artifacts[0], [root])
        # The missing-metadata finding should be present
        missing_findings = [f for f in findings if "metadata.missing" in f.finding_id]
        assert len(missing_findings) >= 1, "expected a missing-metadata finding"
        for f in missing_findings:
            assert f.artifact_path is not None, (
                "missing-metadata finding should have artifact_path set, got None"
            )
            assert f.artifact_path == artifacts[0].path, (
                f"artifact_path should match the source artifact; "
                f"expected '{artifacts[0].path}', got '{f.artifact_path}'"
            )


# ===========================================================================
# SCENARIO 2: validate_one stamps artifact_path on contract findings
#
# Given: a valid skill file
# When:  _validate_one is called
# Then:  contract findings (if any) have artifact_path set to the source path
# ===========================================================================
def test_validate_one_stamps_artifact_path_on_contract_findings():
    """Contract findings emitted by _validate_one have artifact_path set."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "alpha")
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        assert len(artifacts) >= 1
        findings = _validate_one(artifacts[0], [root])
        # If there are any findings at all, they should all have artifact_path
        for f in findings:
            assert f.artifact_path is not None, (
                f"finding '{f.finding_id}' should have artifact_path set, got None"
            )
            assert f.artifact_path == artifacts[0].path, (
                f"finding '{f.finding_id}' artifact_path mismatch; "
                f"expected '{artifacts[0].path}', got '{f.artifact_path}'"
            )


# ===========================================================================
# SCENARIO 3: validate_one stamps artifact_path on the 'untyped' (unknown) notice
#
# Given: an artifact whose path makes it 'unknown' type (e.g. README.md)
# When:  _validate_one is called
# Then:  the resulting 'untyped.skipped' finding has artifact_path set
# ===========================================================================
def test_validate_one_stamps_artifact_path_on_untyped_finding():
    """The 'untyped.skipped' informational finding has artifact_path set."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Create a README.md that discovery will classify as 'unknown'
        (root / "README.md").write_text("# Just a readme\n")
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        # Find the unknown artifact
        unknown = [a for a in artifacts if a.artifact_type == ArtifactType.UNKNOWN]
        assert len(unknown) >= 1, "expected at least one unknown-type artifact"
        findings = _validate_one(unknown[0], [root])
        untyped_findings = [f for f in findings if "untyped" in f.finding_id]
        assert len(untyped_findings) >= 1
        for f in untyped_findings:
            assert f.artifact_path is not None, (
                "untyped finding should have artifact_path set, got None"
            )
            assert f.artifact_path == unknown[0].path


# ===========================================================================
# SCENARIO 4: validate_one stamps artifact_path on the 'path.missing' notice
#
# Given: an artifact whose path doesn't exist in any known root
# When:  _validate_one is called
# Then:  the resulting 'path.missing' finding has artifact_path set
# ===========================================================================
def test_validate_one_stamps_artifact_path_on_path_missing_finding():
    """The 'path.missing' finding (path doesn't resolve in any root) has artifact_path set."""
    # Build an artifact whose .path doesn't exist on disk
    a = SkillArtifact(
        name="ghost",
        path="skills/ghost/SKILL.md",
        artifact_type=ArtifactType.SKILL,
        size_bytes=100,
        estimated_tokens=25,
        content_hash="x" * 64,
        modified_timestamp="2026-06-13T00:00:00Z",
        body_excerpt="",
    )
    with tempfile.TemporaryDirectory() as tmp:
        # Use a root that doesn't contain the artifact's path
        empty_root = Path(tmp)
        findings = _validate_one(a, [empty_root])
        path_missing = [f for f in findings if "path.missing" in f.finding_id]
        assert len(path_missing) >= 1
        for f in path_missing:
            assert f.artifact_path is not None, (
                "path.missing finding should have artifact_path set, got None"
            )
            assert f.artifact_path == a.path


# ===========================================================================
# SCENARIO 5: contract_validator findings (when called directly) have artifact_path
#
# Given: a valid skill file
# When:  validate_contract is called directly
# Then:  the resulting findings have artifact_path set
# ===========================================================================
def test_contract_validator_findings_have_artifact_path():
    """validate_contract() directly returns findings with artifact_path set (or None for cross-file)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "alpha")
        skill_path = root / "skills" / "alpha" / "SKILL.md"
        # Call validate_contract directly. The signature is (name, path).
        # If validate_contract doesn't set artifact_path, we have a regression.
        findings = validate_contract("skills/alpha", skill_path)
        for f in findings:
            # Either artifact_path is set, or it's a cross-file finding
            # (in which case None is acceptable). For now we assert that
            # contract findings have it set.
            if f.category == "contract":
                assert f.artifact_path is not None, (
                    f"contract finding '{f.finding_id}' should have artifact_path set"
                )
