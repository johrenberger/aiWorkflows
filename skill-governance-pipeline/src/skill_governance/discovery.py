"""Discovery: scan directories for skills and agents.

Implements Core Requirement 1:
- Recursively scan configured skill and agent directories.
- Detect Markdown, YAML, JSON, and text-based prompt artifacts.
- Capture name, path, artifact_type, size, estimated tokens,
  content_hash, modified timestamp, declared version, owner,
  category.
- Output: skill_inventory.json

BDD:
- Given a directory contains skill and agent files
  When discovery runs
  Then every artifact is listed in skill_inventory.json
- Given no artifacts are found
  When discovery runs
  Then the pipeline fails with a CI-blocking error
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .models import ArtifactType, SkillArtifact
from .utils import (
    FileInfo,
    estimate_tokens_from_bytes,
    read_text_safe,
    relative_to_root,
    sha256_file,
    walk_files,
)

# Maximum bytes of the file body to keep as an excerpt
EXCERPT_BYTES = 500

# Patterns to identify a skill (vs agent) from a path
# We match a *directory component* that contains 'skill' or 'agent'
# as a substring (e.g. 'sample_skills', 'agents', 'my-skills').
SKILL_PATH_PATTERN = re.compile(r"(^|/)([^/]*skill[^/]*)(/|$)", re.IGNORECASE)
AGENT_PATH_PATTERN = re.compile(r"(^|/)([^/]*agent[^/]*)(/|$)", re.IGNORECASE)

# Frontmatter-style key-value patterns to pull declared metadata
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL | re.MULTILINE)
KV_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+?)\s*$", re.MULTILINE)


@dataclass
class DiscoveryConfig:
    """Configuration for discovery."""

    skill_directories: list[Path]
    agent_directories: list[Path]
    # If True, walk the entire tree under each root. If False, only
    # the top-level files and immediate subdirectories named skills/agents.
    recursive: bool = True
    # Skip common noise directories
    skip_dirs: tuple[str, ...] = (
        "node_modules",
        ".git",
        "dist",
        "build",
        "target",
        "__pycache__",
        ".venv",
        "venv",
        ".pytest_cache",
    )


class DiscoveryError(RuntimeError):
    """Raised when discovery cannot proceed."""


def classify_artifact(path: Path, root: Path) -> ArtifactType:
    """Classify a file as skill/agent/unknown from its path.

    Directory hint wins over filename hint: e.g. a file at
    'agents/SKILL.md' is classified as AGENT (the parent directory
    'agents' is the stronger hint than the basename 'SKILL').
    """
    rel = str(path.relative_to(root))
    # Check the directory part (everything except the basename) first.
    # If the directory tree contains 'agent' or 'skill' as a directory
    # component, that hint wins over the filename.
    directory = str(path.parent.relative_to(root))
    if AGENT_PATH_PATTERN.search(directory):
        return ArtifactType.AGENT
    if SKILL_PATH_PATTERN.search(directory):
        return ArtifactType.SKILL
    # Fallback: filename-based
    if path.stem.upper() in {"AGENT", "AGENTS"}:
        return ArtifactType.AGENT
    if path.stem.upper() in {"SKILL"}:
        return ArtifactType.SKILL
    # Last resort: re-check the full path (in case the path component
    # hint is only in the basename, e.g. 'loose/SKILL.md' where 'loose'
    # has no hint)
    if AGENT_PATH_PATTERN.search(rel):
        return ArtifactType.AGENT
    if SKILL_PATH_PATTERN.search(rel):
        return ArtifactType.SKILL
    return ArtifactType.UNKNOWN


def parse_declared_metadata(body: str) -> dict[str, str]:
    """Parse a YAML-style frontmatter block from a Markdown file.

    Returns a dict of `key -> raw string value` for any keys
    found in the leading `---...---` block. This is best-effort;
    the metadata parser handles full validation.
    """
    if not body:
        return {}
    m = FRONTMATTER_PATTERN.search(body)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        km = KV_PATTERN.match(line)
        if km:
            key, val = km.group(1), km.group(2).strip()
            # Strip surrounding quotes
            if (val.startswith('"') and val.endswith('"')) or (
                val.startswith("'") and val.endswith("'")
            ):
                val = val[1:-1]
            out[key] = val
    return out


def artifact_name_from_path(path: Path, root: Path) -> str:
    """Derive a stable artifact name from a path.

    Strategy:
    - If the path contains a directory whose name includes
      'skill' or 'agent', use the *innermost* such directory
      (lowercased and stripped to 'skills' or 'agents') as a
      namespace prefix, then the directory one level above the
      file (or the file stem if at top level). Examples:
        sample_skills/valid/SKILL.md  -> 'skills/valid'
        agents/summarizer/AGENT.md    -> 'agents/summarizer'
    - Otherwise, use the relative path stem.
    """
    rel = path.relative_to(root)
    parts = rel.parts
    # Find the innermost directory whose name contains 'skill' or 'agent'
    namespace: str | None = None
    for part in parts[:-1]:
        low = part.lower()
        if "skill" in low:
            namespace = "skills"
        elif "agent" in low:
            namespace = "agents"
    if namespace is None:
        return rel.stem
    # Use the directory one level above the file as the leaf name.
    # If the file is directly inside the skill/agent dir, use the
    # filename stem.
    if len(parts) >= 3:
        return f"{namespace}/{parts[-2]}"
    # Phase 7 fix: 2-part case (root/<skill-name>/SKILL.md).
    # Previously returned "skills/SKILL" — the file stem, not the
    # skill name. Use the parent directory name as the leaf.
    if len(parts) == 2:
        return f"{namespace}/{parts[0]}"
    return f"{namespace}/{rel.stem}"


def discover_artifact(path: Path, root: Path) -> SkillArtifact:
    """Convert a file path into a SkillArtifact record."""
    size = path.stat().st_size
    body = read_text_safe(path)
    excerpt = body[:EXCERPT_BYTES] if body else ""
    declared = parse_declared_metadata(body)

    return SkillArtifact(
        name=artifact_name_from_path(path, root),
        path=relative_to_root(path, root),
        artifact_type=classify_artifact(path, root),
        size_bytes=size,
        estimated_tokens=estimate_tokens_from_bytes(size),
        content_hash=sha256_file(path),
        modified_timestamp=FileInfo(path, size, sha256_file(path)).modified_timestamp,
        declared_version=declared.get("version"),
        owner=declared.get("owner"),
        category=declared.get("category"),
        body_excerpt=excerpt,
    )


def discover(config: DiscoveryConfig) -> list[SkillArtifact]:
    """Walk the configured directories and return all artifacts.

    Raises:
        DiscoveryError: if no artifacts are found AND any
        configured directory exists (this is a CI-blocking
        condition; the user almost certainly wanted at least
        one artifact).
    """
    artifacts: list[SkillArtifact] = []
    # Use absolute-path-keyed dedup so the same file can appear
    # in two different roots without conflict.
    seen_abs: set[str] = set()
    # Use content-hash dedup so files with identical content
    # (e.g. shared template refs) collapse to one artifact.
    seen_hashes: set[str] = set()

    roots: list[Path] = list(config.skill_directories) + list(config.agent_directories)
    for root in roots:
        if not root.exists():
            continue
        for path in _iter_candidate_files(root, config):
            try:
                _rel = relative_to_root(path, root)
            except ValueError:
                _rel = str(path)
            key = str(path.resolve())
            if key in seen_abs:
                continue
            seen_abs.add(key)
            artifact = discover_artifact(path, root)
            if artifact.content_hash in seen_hashes:
                continue
            seen_hashes.add(artifact.content_hash)
            artifacts.append(artifact)

    if not artifacts and any(r.exists() for r in roots):
        raise DiscoveryError(
            "No skill or agent artifacts were found in any of the "
            f"configured directories: {[str(r) for r in roots]}. "
            "Check that the directories contain Markdown / YAML / JSON "
            "files under a 'skills/' or 'agents/' path."
        )

    return artifacts


def _iter_candidate_files(root: Path, config: DiscoveryConfig) -> Iterable[Path]:
    """Yield candidate artifact files under root, skipping noise."""
    if not config.recursive:
        # Only top-level + one level of skills/ or agents/
        for p in sorted(root.iterdir()):
            if p.is_file():
                yield p
            elif p.is_dir() and p.name.lower() in {"skills", "agents"}:
                for sp in sorted(p.iterdir()):
                    if sp.is_file():
                        yield sp
        return

    for path in walk_files(root):
        # Skip noise
        rel_parts = path.relative_to(root).parts
        if any(part in config.skip_dirs for part in rel_parts):
            continue
        # Only known extensions
        if path.suffix.lower() not in {".md", ".markdown", ".yaml", ".yml", ".json", ".txt", ".prompt"}:
            continue
        yield path
