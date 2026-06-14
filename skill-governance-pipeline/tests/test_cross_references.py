"""BDD-TDD tests for the agent↔skill cross-reference feature.

The cross-reference feature adds two new optional fields to the
skill/agent YAML frontmatter:

- ``uses_skills: list[str]`` (on agents) — names of skills the agent uses
- ``used_by_agents: list[str]`` (on skills) — names of agents that use this skill

The relationship is symmetric. The tests below lock in:
1. Parsing the new fields from YAML frontmatter
2. Storing them on the Metadata model
3. Surfacing them through the SkillArtifact (via discovery)
4. Detecting cross-reference inconsistencies
"""
from __future__ import annotations

import textwrap
from pathlib import Path

from skill_governance.metadata_parser import parse_metadata
from skill_governance.models import Metadata

# Test fixtures -------------------------------------------------------------


AGENT_YAML_WITH_USES_SKILLS = """\
---
name: test-automation-agent
artifact_type: agent
purpose: Validate code through comprehensive testing.
category: test-automation
owner: johrenberger
version: 1.0.0
inputs:
  - code context
outputs:
  - test plan
  - automation scripts
dependencies: none
intended_consumers:
  - Clawdexter
  - software-engineer-agent
quality_level: draft
last_reviewed: 2026-06-14
uses_skills:
  - test-generation
  - test-gap-analysis
  - validation-runner
---
"""


SKILL_YAML_WITH_USED_BY_AGENTS = """\
---
name: test-generation
artifact_type: skill
purpose: Generate or update tests in the project's test framework.
category: test-automation
owner: johrenberger
version: 1.0.0
inputs:
  - test-gap-report
outputs:
  - new tests
dependencies: test-gap-analysis
intended_consumers:
  - test-automation-agent
quality_level: usable
last_reviewed: 2026-06-14
used_by_agents:
  - test-automation-agent
---
"""


# 1. Parsing -----------------------------------------------------------------


class TestMetadataParserCrossReferenceFields:
    """The metadata parser must extract the new fields from YAML."""

    def test_parse_uses_skills_from_agent_frontmatter(self, tmp_path: Path) -> None:
        """Given an agent's YAML frontmatter with `uses_skills:`
        When the metadata block is parsed
        Then Metadata.uses_skills contains the listed skills.
        """
        f = tmp_path / "AGENT.md"
        f.write_text(AGENT_YAML_WITH_USES_SKILLS, encoding="utf-8")
        metadata = parse_metadata(f)
        assert metadata.uses_skills == [
            "test-generation",
            "test-gap-analysis",
            "validation-runner",
        ], (
            f"Expected Metadata.uses_skills to be ['test-generation', "
            f"'test-gap-analysis', 'validation-runner'], got {metadata.uses_skills}"
        )

    def test_parse_used_by_agents_from_skill_frontmatter(self, tmp_path: Path) -> None:
        """Given a skill's YAML frontmatter with `used_by_agents:`
        When the metadata block is parsed
        Then Metadata.used_by_agents contains the listed agents.
        """
        f = tmp_path / "SKILL.md"
        f.write_text(SKILL_YAML_WITH_USED_BY_AGENTS, encoding="utf-8")
        metadata = parse_metadata(f)
        assert metadata.used_by_agents == ["test-automation-agent"], (
            f"Expected Metadata.used_by_agents to be ['test-automation-agent'], "
            f"got {metadata.used_by_agents}"
        )

    def test_uses_skills_default_to_empty_list_when_missing(self, tmp_path: Path) -> None:
        """Given a YAML block with no `uses_skills` field
        When the metadata block is parsed
        Then Metadata.uses_skills is an empty list (not None).
        """
        yaml = textwrap.dedent(
            """\
            ---
            name: minimal-agent
            artifact_type: agent
            purpose: Minimal agent for testing.
            category: operations
            owner: johrenberger
            version: 1.0.0
            inputs: []
            outputs: []
            dependencies: none
            intended_consumers: []
            quality_level: draft
            last_reviewed: 2026-06-14
            ---
            """
        )
        f = tmp_path / "AGENT.md"
        f.write_text(yaml, encoding="utf-8")
        metadata = parse_metadata(f)
        assert metadata.uses_skills == [], (
            f"Expected default uses_skills=[], got {metadata.uses_skills}"
        )

    def test_used_by_agents_default_to_empty_list_when_missing(self, tmp_path: Path) -> None:
        """Given a YAML block with no `used_by_agents` field
        When the metadata block is parsed
        Then Metadata.used_by_agents is an empty list (not None).
        """
        yaml = textwrap.dedent(
            """\
            ---
            name: minimal-skill
            artifact_type: skill
            purpose: Minimal skill for testing.
            category: operations
            owner: johrenberger
            version: 1.0.0
            inputs: []
            outputs: []
            dependencies: none
            intended_consumers: []
            quality_level: draft
            last_reviewed: 2026-06-14
            ---
            """
        )
        f = tmp_path / "SKILL.md"
        f.write_text(yaml, encoding="utf-8")
        metadata = parse_metadata(f)
        assert metadata.used_by_agents == [], (
            f"Expected default used_by_agents=[], got {metadata.used_by_agents}"
        )


# 2. Model -------------------------------------------------------------------


class TestMetadataModelCrossReferenceFields:
    """The Metadata dataclass must declare the new fields with correct defaults."""

    def test_metadata_has_uses_skills_field(self) -> None:
        """Given a fresh Metadata instance
        When the attributes are inspected
        Then `uses_skills` exists and defaults to [].
        """
        m = Metadata(raw={})
        assert hasattr(m, "uses_skills"), (
            "Metadata must have a `uses_skills` field for cross-references"
        )
        assert m.uses_skills == [], (
            f"Expected default uses_skills=[], got {m.uses_skills}"
        )

    def test_metadata_has_used_by_agents_field(self) -> None:
        """Given a fresh Metadata instance
        When the attributes are inspected
        Then `used_by_agents` exists and defaults to [].
        """
        m = Metadata(raw={})
        assert hasattr(m, "used_by_agents"), (
            "Metadata must have a `used_by_agents` field for cross-references"
        )
        assert m.used_by_agents == [], (
            f"Expected default used_by_agents=[], got {m.used_by_agents}"
        )

    def test_cross_reference_fields_are_not_required(self) -> None:
        """Given a Metadata instance with no cross-references
        When missing_fields() is called
        Then the cross-reference fields are NOT in the missing list
            (they are optional, not required metadata).
        """
        m = Metadata(
            raw={},
            name="test",
            artifact_type="agent",
            purpose="A test",
            category="test",
            owner="johrenberger",
            version="1.0.0",
            inputs="x",
            outputs="y",
            dependencies="none",
            intended_consumers=[],
            quality_level="draft",
            last_reviewed="2026-06-14",
        )
        # uses_skills and used_by_agents are not in REQUIRED_METADATA_FIELDS
        # so they should never appear in missing_fields()
        assert "uses_skills" not in m.missing_fields()
        assert "used_by_agents" not in m.missing_fields()


# 3. Cross-reference consistency --------------------------------------------


class TestCrossReferenceConsistency:
    """A bidirectional validation rule must catch inconsistent cross-references.

    If agent A lists `uses_skills: [B]`, then skill B should list
    `used_by_agents: [A]`. If not, it's an inconsistency.
    """

    def test_consistent_cross_reference_passes(self) -> None:
        """Given agent A uses_skill=[B] and skill B used_by_agents=[A]
        When the cross-references are checked
        Then no inconsistency is reported.
        """
        from skill_governance.cross_references import check_consistency

        artifacts = [
            ("test-automation-agent", "agent", ["test-generation"], []),
            ("test-generation", "skill", [], ["test-automation-agent"]),
        ]
        inconsistencies = check_consistency(artifacts)
        assert inconsistencies == [], (
            f"Expected no inconsistencies, got {inconsistencies}"
        )

    def test_missing_inverse_relationship_is_an_inconsistency(self) -> None:
        """Given agent A uses_skill=[B] but skill B does NOT list A in used_by_agents
        When the cross-references are checked
        Then an inconsistency is reported.
        """
        from skill_governance.cross_references import check_consistency

        # Agent uses skill, but skill doesn't list agent
        artifacts = [
            ("test-automation-agent", "agent", ["test-generation"], []),
            ("test-generation", "skill", [], []),  # missing 'test-automation-agent'
        ]
        inconsistencies = check_consistency(artifacts)
        assert len(inconsistencies) == 1, (
            f"Expected 1 inconsistency, got {len(inconsistencies)}: {inconsistencies}"
        )
        assert inconsistencies[0].artifact == "test-generation"
        assert inconsistencies[0].referenced_by == "test-automation-agent"
        assert inconsistencies[0].missing_inverse is True

    def test_stale_inverse_relationship_is_an_inconsistency(self) -> None:
        """Given skill B used_by_agents=[A] but agent A does NOT list B in uses_skills
        When the cross-references are checked
        Then an inconsistency is reported.
        """
        from skill_governance.cross_references import check_consistency

        # Skill claims an agent uses it, but the agent doesn't agree
        artifacts = [
            ("test-automation-agent", "agent", [], []),  # missing 'test-generation'
            ("test-generation", "skill", [], ["test-automation-agent"]),
        ]
        inconsistencies = check_consistency(artifacts)
        assert len(inconsistencies) == 1, (
            f"Expected 1 inconsistency, got {len(inconsistencies)}: {inconsistencies}"
        )
        assert inconsistencies[0].artifact == "test-automation-agent"
        assert inconsistencies[0].referenced_by == "test-generation"
        assert inconsistencies[0].missing_inverse is True
