"""Tests for the discovery module (CR 1).

BDD coverage:
- Given a directory contains skill and agent files
  When discovery runs
  Then every artifact is listed
- Given no artifacts are found
  When discovery runs
  Then the pipeline fails with a CI-blocking error
"""
from __future__ import annotations

from pathlib import Path

import pytest

from skill_governance.discovery import (
    DiscoveryConfig,
    DiscoveryError,
    classify_artifact,
    discover,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_discovers_all_skill_and_agent_files():
    """Given a directory of mixed skills+agents, every artifact is listed."""
    config = DiscoveryConfig(
        skill_directories=[FIXTURES],
        agent_directories=[FIXTURES],
    )
    artifacts = discover(config)
    names = {a.name for a in artifacts}
    # Should find at least these 5 from fixtures
    assert "skills/valid" in names
    assert "skills/missing-metadata" in names
    assert "skills/vague-output" in names
    assert "agents/summarizer" in names
    assert "agents/missing-metadata-agent" in names
    assert len(artifacts) >= 5


def test_artifact_records_have_required_fields():
    """Every discovered artifact has name, path, type, size, hash, timestamp."""
    config = DiscoveryConfig(
        skill_directories=[FIXTURES],
        agent_directories=[FIXTURES],
    )
    artifacts = discover(config)
    for a in artifacts:
        assert a.name
        assert a.path
        assert a.artifact_type.value in ("skill", "agent", "unknown")
        assert a.size_bytes > 0
        assert len(a.content_hash) == 64  # sha256 hex
        assert a.modified_timestamp.endswith("Z")
        assert a.estimated_tokens > 0


def test_missing_directory_does_not_raise():
    """A configured but non-existent directory is silently skipped."""
    config = DiscoveryConfig(
        skill_directories=[Path("/nonexistent/path")],
        agent_directories=[FIXTURES],
    )
    artifacts = discover(config)
    # Should still find the agents
    assert any(a.name.startswith("agents/") for a in artifacts)


def test_no_artifacts_raises_blocking_error():
    """Given an existing but empty directory, discovery fails CI-blockingly."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        empty = Path(tmp) / "skills"
        empty.mkdir()
        config = DiscoveryConfig(skill_directories=[empty], agent_directories=[])
        with pytest.raises(DiscoveryError):
            discover(config)


def test_classify_artifact_by_path():
    """Skills/agents are classified by directory name."""
    assert classify_artifact(FIXTURES / "sample_skills/valid/SKILL.md", FIXTURES).value == "skill"
    assert classify_artifact(FIXTURES / "sample_agents/summarizer/AGENT.md", FIXTURES).value == "agent"


def test_dedup_across_directories():
    """An artifact listed in two roots appears only once."""
    config = DiscoveryConfig(
        skill_directories=[FIXTURES, FIXTURES],
        agent_directories=[],
    )
    artifacts = discover(config)
    paths = [a.path for a in artifacts]
    assert len(paths) == len(set(paths))
