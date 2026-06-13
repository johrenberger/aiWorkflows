"""Responsibility analyzer: evaluate single-responsibility coherence.

Implements Core Requirement 5.

Uses deterministic heuristics plus a MiniMax semantic scoring
hook (interface only in Phase 2; real scoring in Phase 3).

Score: 0-100 responsibility_score.
Flag: over-broad, too-narrow, unclear, coherent.

Heuristic:
- Count "action" verbs in the body (a simple list).
- Count distinct verbs (actions); more distinct actions => more
  responsibilities => more over-broad.
- One or two actions with named outputs => coherent.
- Zero actions => unclear (or too narrow).
- Five or more actions => over-broad.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .models import ResponsibilityFlag, ResponsibilityReport, SkillArtifact

# Common action verbs that signal responsibilities.
# This is a deliberately small, conservative set; semantic
# scoring in Phase 3 will replace it.
ACTION_VERBS = frozenset(
    {
        "analyze",
        "validate",
        "generate",
        "report",
        "create",
        "build",
        "deploy",
        "test",
        "review",
        "audit",
        "summarize",
        "fix",
        "refactor",
        "rewrite",
        "merge",
        "split",
        "deprecate",
        "retire",
        "check",
        "verify",
        "extract",
        "transform",
        "convert",
        "compare",
        "score",
        "rank",
        "decide",
        "recommend",
        "detect",
        "find",
        "list",
        "scan",
        "discover",
        "design",
        "plan",
        "orchestrate",
        "monitor",
        "alert",
        "notify",
        "route",
        "dispatch",
        "schedule",
        "execute",
        "run",
        "ingest",
        "emit",
        "publish",
        "subscribe",
        "sync",
        "encrypt",
        "decrypt",
        "sign",
        "verify",
    }
)

# Match verbs in base form or -s/-ing/-ed
VERB_PATTERN = re.compile(
    r"\b(" + "|".join(sorted(ACTION_VERBS)) + r")(?:s|ing|ed|er)?\b",
    re.IGNORECASE,
)


def _extract_actions(body: str) -> list[str]:
    """Extract the action verbs that appear in the body."""
    if not body:
        return []
    return [m.group(1).lower() for m in VERB_PATTERN.finditer(body)]


def _score(actions: Counter[str], output_count: int, has_metadata: bool) -> tuple[int, ResponsibilityFlag, str]:
    """Compute a responsibility score and flag from action counts."""
    distinct = len(actions)
    if distinct == 0:
        if not has_metadata:
            return 30, ResponsibilityFlag.UNCLEAR, "No actions detected and no metadata; cannot assess responsibility."
        return 40, ResponsibilityFlag.TOO_NARROW, "No actions detected; skill may be too narrow or purely declarative."
    if distinct >= 6:
        return 25, ResponsibilityFlag.OVER_BROAD, (
            f"Detected {distinct} distinct actions: {', '.join(sorted(actions))}. "
            "Skill is over-broad; consider splitting."
        )
    if distinct >= 4:
        return 50, ResponsibilityFlag.OVER_BROAD, (
            f"Detected {distinct} distinct actions: {', '.join(sorted(actions))}. "
            "Skill may be over-broad; consider tightening scope."
        )
    if output_count == 0:
        return 60, ResponsibilityFlag.UNCLEAR, (
            f"Detected {distinct} action(s) but no declared outputs. "
            "Add a structured outputs contract."
        )
    return 90, ResponsibilityFlag.COHERENT, (
        f"Detected {distinct} action(s) and {output_count} declared output(s). "
        f"Coherent scope: {', '.join(sorted(actions))}."
    )


def analyze(
    artifacts: list[SkillArtifact], roots: list[Path] | None = None
) -> list[ResponsibilityReport]:
    """Analyze responsibility coherence for each artifact.

    Phase 2 uses deterministic heuristics. Phase 3 will add a
    MiniMax semantic scoring hook that refines the score for
    borderline cases (40-69).

    `roots` are the discovery roots used to resolve relative
    artifact paths. If omitted, the analyzer uses the
    filesystem CWD (best-effort).
    """
    from .metadata_parser import parse_metadata

    roots = roots or [Path.cwd()]
    reports: list[ResponsibilityReport] = []
    frontmatter_re = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)

    def _resolve_metadata(artifact: SkillArtifact):
        for root in roots:
            try:
                path = root / artifact.path
            except (TypeError, ValueError):
                continue
            try:
                if not path.exists() or path.is_dir():
                    continue
                return parse_metadata(path)
            except Exception:
                continue
        return None

    for a in artifacts:
        # Strip frontmatter from the body excerpt so metadata
        # tokens like 'test' (in quality_level: 'usable') don't
        # pollute the action count.
        body_only = frontmatter_re.sub("", a.body_excerpt or "")
        actions_counter: Counter[str] = Counter(_extract_actions(body_only))
        # Also pull from the purpose field if metadata exists
        metadata = _resolve_metadata(a)
        has_metadata = metadata is not None and metadata.purpose is not None
        if metadata and metadata.purpose:
            actions_counter.update(_extract_actions(metadata.purpose))
        # Count declared outputs
        output_count = 0
        if metadata and metadata.outputs is not None:
            outputs = metadata.outputs
            if isinstance(outputs, list):
                output_count = len(outputs)
            elif isinstance(outputs, dict):
                output_count = len(outputs.get("fields", [])) + len(outputs.get("sections", []))
                if not output_count and outputs.get("format"):
                    output_count = 1
        score, flag, rationale = _score(actions_counter, output_count, has_metadata)
        reports.append(
            ResponsibilityReport(
                artifact_name=a.name,
                responsibility_score=score,
                flag=flag,
                rationale=rationale,
                responsibilities=sorted(actions_counter),
            )
        )
    return reports
