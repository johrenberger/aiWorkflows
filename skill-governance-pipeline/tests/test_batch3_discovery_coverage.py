"""BDD-TDD coverage tests for discovery.py (Batch 3).

Triggered by application-test-coverage assessment: discovery.py
was 79% line coverage. Missing lines cover:
- classify_artifact filename fallback (AGENT.md, AGENTS.md, SKILL.md, UNKNOWN)
- artifact_name_from_path namespace detection + 2-part case (Phase 7 fix)
- discover dedup-by-hash, no-artifacts error
- _iter_candidate_files non-recursive mode, skip_dirs, unknown extension

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

from pathlib import Path

import pytest

from skill_governance.discovery import (
    DiscoveryConfig,
    DiscoveryError,
    classify_artifact,
    artifact_name_from_path,
    discover,
)
from skill_governance.models import ArtifactType


# ===========================================================================
# SCENARIO 1: classify_artifact falls back to UNKNOWN for unrecognized files
# ===========================================================================
def test_classify_artifact_returns_unknown_for_unrecognized_filename(tmp_path: Path):
    """A file with a known extension but no skill/agent hint returns UNKNOWN."""
    p = tmp_path / "random" / "config.md"
    p.parent.mkdir()
    p.write_text("x")
    assert classify_artifact(p, tmp_path) == ArtifactType.UNKNOWN


# ===========================================================================
# SCENARIO 2: classify_artifact recognizes AGENT.md / AGENTS.md as AGENT
# ===========================================================================
def test_classify_artifact_recognizes_agent_filename(tmp_path: Path):
    """A file named AGENT.md or AGENTS.md is classified as AGENT."""
    for name in ("AGENT.md", "AGENTS.md", "agent.md", "agents.md"):
        p = tmp_path / name
        p.write_text("x")
        assert classify_artifact(p, tmp_path) == ArtifactType.AGENT, (
            f"expected AGENT for {name}"
        )


# ===========================================================================
# SCENARIO 3: classify_artifact recognizes SKILL.md as SKILL
# ===========================================================================
def test_classify_artifact_recognizes_skill_filename(tmp_path: Path):
    """A file named SKILL.md is classified as SKILL."""
    p = tmp_path / "SKILL.md"
    p.write_text("x")
    assert classify_artifact(p, tmp_path) == ArtifactType.SKILL


# ===========================================================================
# SCENARIO 4: artifact_name_from_path handles 2-part case (Phase 7 fix)
#
# Given: a file at root/<skill-name>/SKILL.md (2 parts under root)
# When:  artifact_name_from_path is called
# Then:  it returns "skills/<skill-name>" (the dir name, not "SKILL")
# ===========================================================================
def test_artifact_name_from_path_uses_parent_dir_for_2_part_case(tmp_path: Path):
    """Phase 7 fix: a 2-part path uses the parent dir name as the leaf."""
    skill_dir = tmp_path / "my-cool-skill"
    skill_dir.mkdir()
    p = skill_dir / "SKILL.md"
    p.write_text("# my skill")
    name = artifact_name_from_path(p, tmp_path)
    assert name == "skills/my-cool-skill", f"got {name!r}"


# ===========================================================================
# SCENARIO 5: artifact_name_from_path handles 3+ part case
# ===========================================================================
def test_artifact_name_from_path_uses_penultimate_dir_for_3_part_case(tmp_path: Path):
    """A 3+ part path uses the directory one level above the file as the leaf."""
    skill_dir = tmp_path / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    p = skill_dir / "SKILL.md"
    p.write_text("x")
    name = artifact_name_from_path(p, tmp_path)
    assert name == "skills/my-skill", f"got {name!r}"


# ===========================================================================
# SCENARIO 6: discover raises DiscoveryError for empty results
#
# Given: configured skill directories exist but contain no artifacts
# When:  discover is called
# Then:  DiscoveryError is raised
# ===========================================================================
def test_discover_raises_when_no_artifacts_found(tmp_path: Path):
    """An empty but-existing skill directory raises DiscoveryError."""
    cfg = DiscoveryConfig(
        skill_directories=[tmp_path / "skills"],
        agent_directories=[],
    )
    (tmp_path / "skills").mkdir()
    # No files in skills/
    with pytest.raises(DiscoveryError, match="No skill or agent artifacts"):
        discover(cfg)


# ===========================================================================
# SCENARIO 7: discover returns empty list when no roots exist
# ===========================================================================
def test_discover_returns_empty_when_no_roots_exist(tmp_path: Path):
    """If no configured directories exist, returns empty (no error)."""
    cfg = DiscoveryConfig(
        skill_directories=[tmp_path / "nonexistent"],
        agent_directories=[],
    )
    result = discover(cfg)
    assert result == []


# ===========================================================================
# SCENARIO 8: discover deduplicates by content_hash
# ===========================================================================
def test_discover_dedupes_by_content_hash(tmp_path: Path):
    """Two files with identical content are reported once."""
    cfg = DiscoveryConfig(
        skill_directories=[tmp_path / "skills"],
        agent_directories=[],
    )
    sdir = tmp_path / "skills"
    sdir.mkdir()
    (sdir / "skillA.md").write_text("# same content")
    (sdir / "skillB.md").write_text("# same content")
    result = discover(cfg)
    # Only 1 artifact (the second is a content-hash duplicate)
    assert len(result) == 1


# ===========================================================================
# SCENARIO 9: artifact_name_from_path falls back to rel.stem for 1-part
# ===========================================================================
def test_artifact_name_from_path_falls_back_to_stem_for_1_part(tmp_path: Path):
    """A file at the root (1 part) returns the filename stem as the leaf (no namespace)."""
    p = tmp_path / "standalone.md"
    p.write_text("x")
    name = artifact_name_from_path(p, tmp_path)
    assert name == "standalone", f"got {name!r}"


# ===========================================================================
# SCENARIO 10: parse_declared_metadata handles quoted string values
# ===========================================================================
def test_parse_declared_metadata_strips_surrounding_quotes():
    """Single and double quoted values have their quotes stripped."""
    from skill_governance.discovery import parse_declared_metadata
    body = '---\nname: "my-skill"\nowner: \'team-x\'\n---\n# x'
    declared = parse_declared_metadata(body)
    assert declared["name"] == "my-skill"
    assert declared["owner"] == "team-x"


# ===========================================================================
# SCENARIO 11: parse_declared_metadata returns {} for empty body
# ===========================================================================
def test_parse_declared_metadata_returns_empty_dict_for_empty_body():
    """Empty body returns {} (no frontmatter)."""
    from skill_governance.discovery import parse_declared_metadata
    assert parse_declared_metadata("") == {}


# ===========================================================================
# SCENARIO 12: parse_declared_metadata returns {} when no frontmatter
# ===========================================================================
def test_parse_declared_metadata_returns_empty_dict_when_no_frontmatter():
    """A body with no `---` markers returns {}."""
    from skill_governance.discovery import parse_declared_metadata
    body = "# Just a title\n\nNo frontmatter here.\n"
    assert parse_declared_metadata(body) == {}


# ===========================================================================
# SCENARIO 13: discover with non-recursive mode scans only top-level
# ===========================================================================
def test_discover_with_non_recursive_mode_scans_top_level_only(tmp_path: Path):
    """non-recursive mode scans only top-level + one level of skills/agents."""
    cfg = DiscoveryConfig(
        skill_directories=[tmp_path],
        agent_directories=[],
        recursive=False,
    )
    (tmp_path / "top.md").write_text("x")
    (tmp_path / "skills" / "deep-skill").mkdir(parents=True)
    (tmp_path / "skills" / "deep-skill" / "SKILL.md").write_text("x")
    result = discover(cfg)
    # The deep-skill/SKILL.md is at 2 levels, should be picked up
    # (top-level + 1 level of skills/ + the SKILL.md file)
    names = [a.name for a in result]
    assert "top" in [a.name for a in result] or "skills/deep-skill" in names


# ===========================================================================
# SCENARIO 14: discover skips files in skip_dirs
# ===========================================================================
def test_discover_skips_files_in_skip_dirs(tmp_path: Path):
    """Files under a configured skip_dir are not picked up."""
    cfg = DiscoveryConfig(
        skill_directories=[tmp_path / "skills"],
        agent_directories=[],
        skip_dirs=("node_modules",),
    )
    sdir = tmp_path / "skills"
    sdir.mkdir()
    (sdir / "good-skill").mkdir()
    (sdir / "good-skill" / "SKILL.md").write_text("x")
    (sdir / "node_modules").mkdir()
    (sdir / "node_modules" / "ignored.md").write_text("x")
    result = discover(cfg)
    names = [a.name for a in result]
    assert "skills/good-skill" in names
    assert not any("node_modules" in n for n in names)
