"""BDD tests for A.2: filter 'unknown' artifacts from the dependency graph.

Bucket A.2 of the v1.0.0 follow-up push. The dependency analyzer
currently includes 'unknown'-type artifacts (templates, references,
READMEs) in the name index, so generic English words in artifact
bodies (e.g. 'task', 'validation') are matched against these template
files and create false-positive circular dependencies.

Real example from the test-repo catalog:
- task-state-management/templates/task.md (unknown, name='task')
- task-state-management/templates/validation-report.md (unknown, name='validation-report')
- The body of TEST_AUTOMATION_AGENT.md mentions 'task' generically
  -> matched to 'task' artifact -> cycle
- The body of SOFTWARE_ENGINEER_AGENT.md mentions 'task' generically
  -> matched to 'task' artifact -> cycle

Result: 6 false-positive cycles in the test-repo catalog.

The fix: filter 'unknown' artifacts out of the dependency graph.
This way, only real skills and agents participate in dependency
analysis. Templates and references are not 'dependencies' in the
governance sense — they're documentation artifacts.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from skill_governance.config_loader import load_config
from skill_governance.dependency_analyzer import analyze
from skill_governance.discovery import DiscoveryConfig, discover


class TestDependencyAnalyzerFiltersUnknownArtifacts:
    """The dependency analyzer must not treat 'unknown' artifacts as deps."""

    @pytest.fixture
    def catalog_with_cycles(
        self, tmp_path: Path
    ) -> tuple[Path, Path]:
        """Build a tiny catalog where the body of one artifact
        mentions a name that matches an 'unknown' template.

        Returns (config_path, tmp_root) so tests can read the
        analysis result.
        """
        agents = tmp_path / "agents"
        agents.mkdir(parents=True)
        # An agent whose body mentions 'task' generically
        (agents / "DEVOPS_AGENT.md").write_text(
            "---\nname: devops-agent\nartifact_type: agent\n"
            "purpose: DevOps engineer.\n"
            "category: operations\nowner: test\nversion: 1.0.0\n"
            "inputs: []\noutputs: []\ndependencies: none\n"
            "intended_consumers: []\nquality_level: usable\n"
            "last_reviewed: 2026-06-14\nuses_skills: []\n---\n"
            "# DevOps Agent\n\n"
            "When the team has a deployment task, this agent runs CI.\n",
            encoding="utf-8",
        )
        # A 'task' template (unknown type, name='task')
        templates = tmp_path / "skills" / "task-template" / "templates"
        templates.mkdir(parents=True)
        (templates / "task.md").write_text(
            "---\nname: task\nartifact_type: unknown\n"
            "purpose: A task template that references the devops agent.\n"
            "category: operations\nowner: test\nversion: 1.0.0\n"
            "inputs: []\noutputs: []\ndependencies: none\n"
            "intended_consumers: []\nquality_level: usable\n"
            "last_reviewed: 2026-06-14\n---\n"
            "# task template\n\n"
            "For deployment tasks, use the devops agent.\n",
            encoding="utf-8",
        )
        config = tmp_path / "config.yaml"
        config.write_text(
            f"agent_directories: [{agents}]\n"
            f"skill_directories: [{tmp_path / 'skills'}]\n"
            f"output_directory: {tmp_path}/output\n"
            "ci_blocking_categories: [metadata, contract]\n"
            "health_weights: {metadata: 1.0}\n"
            "inclusion_patterns: ['**/*AGENT.md', '**/SKILL.md']\n"
            "exclusion_patterns: []\n",
            encoding="utf-8",
        )
        return config, tmp_path

    def test_no_cycles_when_only_unknown_template_matches(
        self, catalog_with_cycles: tuple[Path, Path]
    ) -> None:
        """Given an agent whose body mentions 'task' generically
        AND a template file with name='task' (unknown type)
        When the dependency analyzer runs
        Then no cycles are reported (the unknown template
        is filtered out of the dep graph).
        """
        config_path, tmp_root = catalog_with_cycles
        config = load_config(config_path)
        dcfg = DiscoveryConfig(
            skill_directories=[Path(p) for p in config.skill_directories],
            agent_directories=[Path(p) for p in config.agent_directories],
        )
        inv = discover(dcfg)
        graph = analyze(inv)
        # Before the fix, this would be a cycle: devops-agent -> task -> devops-agent
        assert graph.circular_dependencies == [], (
            f"Expected no cycles (unknown template should be filtered), "
            f"got: {graph.circular_dependencies}"
        )

    def test_unknown_artifact_not_in_dep_nodes(
        self, catalog_with_cycles: tuple[Path, Path]
    ) -> None:
        """Given a catalog with an 'unknown' artifact
        When the dependency analyzer builds the graph
        Then the unknown artifact does not appear as a node
        (only skills and agents participate in dep analysis).
        """
        config_path, tmp_root = catalog_with_cycles
        config = load_config(config_path)
        dcfg = DiscoveryConfig(
            skill_directories=[Path(p) for p in config.skill_directories],
            agent_directories=[Path(p) for p in config.agent_directories],
        )
        inv = discover(dcfg)
        graph = analyze(inv)
        # The 'task' template should not be a node in the graph
        assert "task" not in graph.nodes, (
            f"Expected 'task' (unknown type) to be filtered out of "
            f"the dep graph, but it appears as a node. "
            f"Nodes: {list(graph.nodes.keys())}"
        )
