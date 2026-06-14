"""BDD-TDD coverage tests for CTA-GAP-002: dependency_analyzer Finding category.

Triggered by application-test-coverage (FOCUSED_PICKS pass) on the
component-test-analysis gap-backlog. CTA-GAP-002 is a P1 gap (T2 risk):

    "dependency_analyzer._find_missing() should emit a Finding with
    category 'missing-dependency' but no test asserts on the Finding
    category, only on its severity. Risk: if the category string
    changes, the recommendation_engine grouping breaks silently."

The current code uses `category="dependency"` for ALL three finding
shapes (missing, circular, unused). The gap text calls for distinct
categories so downstream consumers can group by issue type. These
tests lock the desired shape: missing-dep findings get
`category="missing-dependency"`, circular-dep findings get
`category="circular-dependency"`, unused-dep findings get
`category="unused-dependency"`.

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
- Red-phase: tests must fail against the current code (red)
- Green-phase: tests pass after fixing `graph_to_findings`
"""
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


# ===========================================================================
# SCENARIO 1: missing-dependency finding uses category='missing-dependency'
#
# Given: an artifact A that declares a dependency on Z, but Z doesn't exist
# When:  graph_to_findings() is called on the resulting graph
# Then:  the emitted finding has category == 'missing-dependency'
# ===========================================================================
def test_missing_dependency_finding_uses_specific_category():
    """Missing-dep findings are tagged with 'missing-dependency' (not the generic 'dependency')."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "alpha", ["ghost"])
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        graph = analyze(artifacts, roots=[root])
        findings = graph_to_findings(graph)
        missing_findings = [f for f in findings if "missing" in f.message.lower()]
        assert len(missing_findings) >= 1, "expected at least one missing-dep finding"
        for f in missing_findings:
            assert f.category == "missing-dependency", (
                f"missing-dep finding should have category='missing-dependency', "
                f"got category='{f.category}'"
            )


# ===========================================================================
# SCENARIO 2: circular-dependency finding uses category='circular-dependency'
#
# Given: artifacts A and B that mutually declare each other as deps
# When:  graph_to_findings() is called
# Then:  the cycle finding has category == 'circular-dependency'
# ===========================================================================
def test_circular_dependency_finding_uses_specific_category():
    """Circular-dep findings are tagged with 'circular-dependency'."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "alpha", ["beta"])
        _make_skill(root, "beta", ["alpha"])
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        graph = analyze(artifacts, roots=[root])
        findings = graph_to_findings(graph)
        cycle_findings = [f for f in findings if "circular" in f.message.lower()]
        assert len(cycle_findings) >= 1, "expected at least one circular-dep finding"
        for f in cycle_findings:
            assert f.category == "circular-dependency", (
                f"circular-dep finding should have category='circular-dependency', "
                f"got category='{f.category}'"
            )


# ===========================================================================
# SCENARIO 3: unused-dependency finding uses category='unused-dependency'
#
# Given: an artifact A that declares a dep on B, and B is never referenced
#        by any other artifact
# When:  graph_to_findings() is called
# Then:  the unused finding has category == 'unused-dependency'
# ===========================================================================
def test_unused_dependency_finding_uses_specific_category():
    """Unused-dep findings are tagged with 'unused-dependency'."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # alpha declares dep on 'ghost-unused-only-by-alpha' which nobody uses.
        # Because the dep name doesn't match any artifact, it's BOTH missing
        # AND unused; the analyzer emits both findings. We filter for the
        # unused one by looking for the "Unused dependency:" prefix in the
        # message (substring 'unused' in dep names would give false matches).
        _make_skill(root, "alpha", ["ghost-unused-only-by-alpha"])
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        graph = analyze(artifacts, roots=[root])
        findings = graph_to_findings(graph)
        unused_findings = [
            f for f in findings if f.message.lower().startswith("unused dependency")
        ]
        assert len(unused_findings) >= 1, "expected at least one unused-dep finding"
        for f in unused_findings:
            assert f.category == "unused-dependency", (
                f"unused-dep finding should have category='unused-dependency', "
                f"got category='{f.category}'"
            )


# ===========================================================================
# SCENARIO 4: all three finding categories are distinct (no collisions)
#
# Given: a graph with all three issue shapes (missing, circular, unused)
# When:  graph_to_findings() is called
# Then:  the three category values are pairwise distinct
# ===========================================================================
def test_three_dep_finding_categories_are_distinct():
    """Missing, circular, and unused must have three distinct category strings."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Setup: alpha has a missing dep (ghost-missing)
        #        alpha <-> beta creates a cycle
        #        alpha declares ghost-unused which nobody else uses (unused)
        _make_skill(root, "alpha", ["beta", "ghost-missing", "ghost-unused"])
        _make_skill(root, "beta", ["alpha"])
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        graph = analyze(artifacts, roots=[root])
        findings = graph_to_findings(graph)
        cats = {f.category for f in findings}
        # We expect at least 3 distinct category values across the three shapes
        assert "missing-dependency" in cats, f"missing-dependency missing; got {cats}"
        assert "circular-dependency" in cats, f"circular-dependency missing; got {cats}"
        assert "unused-dependency" in cats, f"unused-dependency missing; got {cats}"
