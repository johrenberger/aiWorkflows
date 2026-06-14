"""Tests for the dependency analyzer (CR 4)."""
from __future__ import annotations

import tempfile
from pathlib import Path

from skill_governance.dependency_analyzer import (
    analyze,
    graph_to_findings,
)
from skill_governance.discovery import (
    DiscoveryConfig,
    discover,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _make_skill(tmp_path: Path, name: str, deps: list[str], body: str = "") -> Path:
    """Write a minimal skill file with the given declared deps."""
    p = tmp_path / "skills" / name
    p.mkdir(parents=True, exist_ok=True)
    deps_yaml = "\n".join(f"  - {d}" for d in deps) if deps else "  []"
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
        f"dependencies:\n{deps_yaml}\n"
        "intended_consumers: []\n"
        "quality_level: draft\n"
        "last_reviewed: 2026-06-13\n"
        "---\n"
        f"# {name}\n{body}\n"
    )
    f = p / "SKILL.md"
    f.write_text(text)
    return f


def test_simple_dependency_is_resolved():
    """A skill that depends on an existing skill is graph-valid."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "alpha", [])
        _make_skill(root, "beta", ["alpha"])
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        graph = analyze(artifacts, roots=[root])
        names = {n for n in graph.nodes}
        assert "skills/alpha" in names
        assert "skills/beta" in names
        assert "skills/alpha" in graph.nodes["skills/beta"].depends_on
        assert graph.missing_dependencies == []
        assert graph.circular_dependencies == []


def test_missing_dependency_is_detected():
    """A skill that depends on a non-existent skill is flagged as missing."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "alpha", ["ghost"])
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        graph = analyze(artifacts, roots=[root])
        assert ("skills/alpha", "ghost") in graph.missing_dependencies
        # Also surfaces as a finding
        findings = graph_to_findings(graph)
        # Phase 6+ fix: missing-dep findings are tagged with the specific
        # category "missing-dependency" (not the generic "dependency") so
        # downstream consumers can group by issue type. See CTA-GAP-002.
        assert any(
            f.category == "missing-dependency" and "missing" in f.message.lower()
            for f in findings
        )
        assert any(f.severity.value == "blocking" for f in findings)


def test_circular_dependency_is_detected():
    """A -> B -> A is detected as a cycle."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "alpha", ["beta"])
        _make_skill(root, "beta", ["alpha"])
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        graph = analyze(artifacts, roots=[root])
        assert len(graph.circular_dependencies) >= 1
        # At least one cycle contains both alpha and beta
        cycle_sets = [set(c) for c in graph.circular_dependencies]
        assert any({"skills/alpha", "skills/beta"} <= cs for cs in cycle_sets)


def test_unused_dependency_is_detected():
    """A declared dep that nobody else references is flagged as unused."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "alpha", [])
        _make_skill(root, "beta", ["alpha"])  # beta uses alpha
        _make_skill(root, "gamma", ["alpha"])  # gamma also "uses" alpha via dep list
        # Add an orphan: delta depends on alpha AND on something only it uses
        _make_skill(root, "delta", ["alpha", "ghost-unused"])
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        graph = analyze(artifacts, roots=[root])
        # 'ghost-unused' is missing AND unused
        missing = [m for m in graph.missing_dependencies if m[1] == "ghost-unused"]
        assert missing
        # alpha is used by beta and gamma, so should not be in unused
        unused_names = {d for _, d in graph.unused_dependencies}
        assert "alpha" not in unused_names
        # ghost-unused is unused
        assert "ghost-unused" in unused_names


def test_empty_graph_is_valid():
    """No artifacts = no graph = no findings."""
    graph = analyze([])
    assert graph.nodes == {}
    assert graph.missing_dependencies == []
    assert graph.circular_dependencies == []
    assert graph.unused_dependencies == []
