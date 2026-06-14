"""Dependency analyzer: build a cross-skill dependency graph.

Implements Core Requirement 4.

Detects:
- missing dependencies (skill A references skill Z, but Z doesn't exist)
- circular dependencies (A -> B -> A)
- unused dependencies (declared in metadata but never referenced
  in any other artifact's body)
- implicit dependency references in body content
- excessive dependency chains (cycles are the primary signal)

Output: dependency_graph.json

The analyzer:
1. Parses `dependencies` from each artifact's metadata (already
   done by metadata_parser; the dependency list lives in the
   SkillArtifact's declared metadata or in the body content).
2. Detects implicit references in body excerpts using a simple
   tokenization heuristic.
3. Builds a graph, runs DFS to find cycles, and emits findings
   for missing/circular/unused dependencies.
"""
from __future__ import annotations

import re
from pathlib import Path

from .metadata_parser import parse_metadata
from .models import (
    ArtifactType,
    DependencyGraph,
    DependencyNode,
    Finding,
    Severity,
    SkillArtifact,
)
from .utils import read_text_safe

# Heuristic: a "name" token we look for in body text
# Format: word chars and dashes, at least 3 chars
NAME_TOKEN = re.compile(r"\b([a-z][a-z0-9-]{2,40})\b", re.IGNORECASE)


def _normalize_name(s: str) -> str:
    """Normalize an artifact name for comparison."""
    return s.strip().lower().replace("_", "-")


def _build_name_index(artifacts: list[SkillArtifact]) -> dict[str, str]:
    """Map every plausible form of an artifact name to its canonical name."""
    idx: dict[str, str] = {}
    for a in artifacts:
        idx[_normalize_name(a.name)] = a.name
        # also map the bare stem (last component)
        idx[_normalize_name(a.name.split("/")[-1])] = a.name
    return idx


def _extract_body_references(body: str, name_index: dict[str, str]) -> set[str]:
    """Find artifact names that are mentioned in the body text.

    We tokenize the body and look for any token (or its plural
    form) that matches a known artifact name. This catches
    implicit dependencies that weren't declared in metadata.
    """
    if not body:
        return set()
    found: set[str] = set()
    body_lc = body.lower()
    for needle in name_index:
        # Match as a whole word
        if re.search(rf"\b{re.escape(needle)}s?\b", body_lc):
            found.add(name_index[needle])
    return found


def _declared_dependencies(artifact: SkillArtifact, roots: list[Path]) -> list[str]:
    """Extract the declared dependency list from an artifact's metadata.

    The artifact's `path` is forward-slash relative to one of
    `roots`. We try each root until we find a file that
    exists; if none exist, we return an empty list.
    """
    for root in roots:
        try:
            path = root / artifact.path
        except (TypeError, ValueError):
            continue
        try:
            if not path.exists() or path.is_dir():
                continue
            metadata = parse_metadata(path)
            return list(metadata.dependencies or [])
        except Exception:
            continue
    return []


def _build_graph(
    artifacts: list[SkillArtifact], name_index: dict[str, str], roots: list[Path]
) -> dict[str, DependencyNode]:
    """Build the dependency graph from declared + implicit deps."""
    nodes: dict[str, DependencyNode] = {}
    body_excerpts: dict[str, str] = {
        a.name: a.body_excerpt for a in artifacts
    }
    for a in artifacts:
        nodes[a.name] = DependencyNode(
            name=a.name,
            artifact_type=a.artifact_type,
            depends_on=[],
            depended_on_by=[],
        )
    # Declared
    for a in artifacts:
        for dep_name in _declared_dependencies(a, roots):
            target = name_index.get(_normalize_name(dep_name))
            if target is None or target == a.name:
                continue  # missing or self-reference; handled separately
            if target not in nodes[a.name].depends_on:
                nodes[a.name].depends_on.append(target)
    # Implicit (from body)
    for a in artifacts:
        body = body_excerpts.get(a.name, "")
        for ref in _extract_body_references(body, name_index):
            if ref == a.name:
                continue
            if ref not in nodes[a.name].depends_on:
                nodes[a.name].depends_on.append(ref)
    # Reverse edges
    for name, node in nodes.items():
        for dep in node.depends_on:
            if dep in nodes and name not in nodes[dep].depended_on_by:
                nodes[dep].depended_on_by.append(name)
    return nodes


def _find_cycles(nodes: dict[str, DependencyNode]) -> list[list[str]]:
    """Find all simple cycles in the dependency graph using DFS.

    Returns a list of cycles, where each cycle is a list of
    node names forming the cycle (with the starting node repeated
    at the end for clarity, e.g. ['A', 'B', 'C', 'A']).
    """
    cycles: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()

    def dfs(start: str, current: str, path: list[str], visited: set[str]) -> None:
        for nxt in nodes[current].depends_on:
            if nxt == start and len(path) >= 2:
                cycle = path + [start]
                key = tuple(sorted(set(cycle)))
                if key not in seen:
                    seen.add(key)
                    cycles.append(cycle)
            elif nxt in nodes and nxt not in visited:
                visited.add(nxt)
                dfs(start, nxt, path + [nxt], visited)
                visited.discard(nxt)

    for name in nodes:
        dfs(name, name, [name], {name})
    return cycles


def _find_missing(
    artifacts: list[SkillArtifact], name_index: dict[str, str], roots: list[Path]
) -> list[tuple[str, str]]:
    """Return (artifact, missing_dep) pairs where the dep doesn't exist."""
    missing: list[tuple[str, str]] = []
    for a in artifacts:
        for dep_name in _declared_dependencies(a, roots):
            target = name_index.get(_normalize_name(dep_name))
            if target is None:
                missing.append((a.name, dep_name))
    return missing


def _find_unused(
    artifacts: list[SkillArtifact], name_index: dict[str, str], roots: list[Path]
) -> list[tuple[str, str]]:
    """Return (artifact, dep) pairs where the declared dep is never
    referenced in any other artifact's body and not in any other
    artifact's `dependencies` list.

    Note: this is a conservative "fully unused" check. A dep
    that is used by some other artifact is NOT unused.
    """
    # Collect every dependency reference (declared OR implicit)
    all_refs: set[tuple[str, str]] = set()
    for a in artifacts:
        # Declared
        for d in _declared_dependencies(a, roots):
            target = name_index.get(_normalize_name(d), d)
            all_refs.add((a.name, target))
        # Implicit
        for ref in _extract_body_references(a.body_excerpt, name_index):
            all_refs.add((a.name, ref))

    unused: list[tuple[str, str]] = []
    for a in artifacts:
        for dep_name in _declared_dependencies(a, roots):
            target = name_index.get(_normalize_name(dep_name), dep_name)
            # Is anyone besides `a` referencing `target`?
            other_refs = {src for (src, tgt) in all_refs if tgt == target and src != a.name}
            if not other_refs:
                unused.append((a.name, dep_name))
    return unused


def analyze(artifacts: list[SkillArtifact], roots: list[Path] | None = None) -> DependencyGraph:
    """Build the dependency graph and detect issues.

    Returns a `DependencyGraph` containing nodes, missing
    dependencies, circular dependencies, and unused dependencies.

    `roots` are the discovery roots used to resolve relative
    artifact paths. If omitted, the analyzer uses the
    filesystem CWD (best-effort).
    """
    roots = roots or [Path.cwd()]
    name_index = _build_name_index(artifacts)
    nodes = _build_graph(artifacts, name_index, roots)
    missing = _find_missing(artifacts, name_index, roots)
    cycles = _find_cycles(nodes)
    unused = _find_unused(artifacts, name_index, roots)
    return DependencyGraph(
        nodes=nodes,
        missing_dependencies=missing,
        circular_dependencies=cycles,
        unused_dependencies=unused,
    )


def graph_to_findings(graph: DependencyGraph) -> list[Finding]:
    """Convert a dependency graph to a list of governance findings."""
    findings: list[Finding] = []
    for src, missing in graph.missing_dependencies:
        findings.append(
            Finding(
                finding_id=f"dependency.missing.{src}.{missing}",
                artifact_name=src,
                severity=Severity.BLOCKING,
                category="missing-dependency",
                message=f"Missing dependency: '{missing}' is referenced but does not exist.",
                evidence={"from": src, "to": missing},
                suggestion=f"Create a skill/agent named '{missing}', or remove it from the dependencies list.",
            )
        )
    for cycle in graph.circular_dependencies:
        findings.append(
            Finding(
                finding_id=f"dependency.circular.{'-'.join(cycle)}",
                artifact_name=cycle[0],
                severity=Severity.BLOCKING,
                category="circular-dependency",
                message=f"Circular dependency: {' -> '.join(cycle)}",
                evidence={"cycle": cycle},
                suggestion="Break the cycle by extracting a shared helper, or use a one-way dependency direction.",
            )
        )
    for src, dep in graph.unused_dependencies:
        findings.append(
            Finding(
                finding_id=f"dependency.unused.{src}.{dep}",
                artifact_name=src,
                severity=Severity.WARNING,
                category="unused-dependency",
                message=f"Unused dependency: '{dep}' is declared by '{src}' but never referenced elsewhere.",
                evidence={"from": src, "to": dep},
                suggestion=f"Remove '{dep}' from the dependencies list, or document why it's needed.",
            )
        )
    return findings
