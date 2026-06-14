"""Metadata parser: extract and validate metadata blocks.

Implements Core Requirement 2.

Each skill/agent should include a metadata block with these
required fields:
- name, artifact_type, purpose, category, owner, version, inputs,
  outputs, dependencies, intended_consumers, quality_level,
  last_reviewed

Validation behavior:
- Missing required metadata is a CI blocker.
- Vague purpose is a warning unless severe.
- Missing input/output contracts is a CI blocker.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from .models import Metadata
from .utils import read_text_safe

# Recognized metadata block formats
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL | re.MULTILINE)
JSON_METADATA_PATTERN = re.compile(r"^\s*\{.*?\}\s*$", re.DOTALL | re.MULTILINE)


def _parse_frontmatter(body: str) -> dict[str, Any] | None:
    """Parse a YAML frontmatter block from a Markdown file."""
    m = FRONTMATTER_PATTERN.search(body)
    if not m:
        return None
    try:
        data = yaml.safe_load(m.group(1))
        if not isinstance(data, dict):
            return None
        return data
    except yaml.YAMLError:
        return None


def _parse_json_block(body: str) -> dict[str, Any] | None:
    """Parse a leading JSON metadata block (for .json files)."""
    # If the file is pure JSON, parse the whole thing
    try:
        data = json.loads(body)
        if isinstance(data, dict) and "metadata" in data and isinstance(data["metadata"], dict):
            return data["metadata"]
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return None


def parse_metadata(path: Path) -> Metadata:
    """Parse the metadata block from a skill/agent file.

    Strategy:
    1. If the file has YAML frontmatter, parse that.
    2. Otherwise, if the file is JSON, parse the whole thing
       (or the `metadata` key if present).
    3. Otherwise, return an empty Metadata with everything None.
    """
    body = read_text_safe(path)
    raw: dict[str, Any] = {}
    fm = _parse_frontmatter(body)
    if fm is not None:
        raw = fm
    else:
        jb = _parse_json_block(body)
        if jb is not None:
            raw = jb

    deps = raw.get("dependencies", [])
    if isinstance(deps, str):
        deps = [d.strip() for d in deps.split(",") if d.strip()]
    elif not isinstance(deps, list):
        deps = []

    consumers = raw.get("intended_consumers", [])
    if isinstance(consumers, str):
        consumers = [c.strip() for c in consumers.split(",") if c.strip()]
    elif not isinstance(consumers, list):
        consumers = []

    # Cross-reference fields: uses_skills (on agents) and
    # used_by_agents (on skills). These are lists of artifact
    # names. Accept string or list for flexibility.
    uses_skills = raw.get("uses_skills", [])
    if isinstance(uses_skills, str):
        uses_skills = [s.strip() for s in uses_skills.split(",") if s.strip()]
    elif not isinstance(uses_skills, list):
        uses_skills = []

    used_by_agents = raw.get("used_by_agents", [])
    if isinstance(used_by_agents, str):
        used_by_agents = [a.strip() for a in used_by_agents.split(",") if a.strip()]
    elif not isinstance(used_by_agents, list):
        used_by_agents = []

    # `last_reviewed` should be a string (ISO date) regardless
    # of YAML auto-parsing into a date/datetime object.
    last_reviewed = raw.get("last_reviewed")
    if last_reviewed is not None and not isinstance(last_reviewed, str):
        last_reviewed = str(last_reviewed)

    return Metadata(
        raw=raw,
        name=raw.get("name"),
        artifact_type=raw.get("artifact_type"),
        purpose=raw.get("purpose"),
        category=raw.get("category"),
        owner=raw.get("owner"),
        version=raw.get("version"),
        inputs=raw.get("inputs"),
        outputs=raw.get("outputs"),
        dependencies=deps,
        intended_consumers=consumers,
        quality_level=raw.get("quality_level"),
        last_reviewed=last_reviewed,
        uses_skills=uses_skills,
        used_by_agents=used_by_agents,
    )
