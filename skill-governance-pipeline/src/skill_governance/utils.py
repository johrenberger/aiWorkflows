"""Shared utilities for the skill governance pipeline.

Centralizes hashing, token estimation, and file scanning
helpers so the rest of the pipeline can stay focused on
its own logic.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator


# Average characters per token for OpenAI/MiniMax-style tokenizers.
# 4 chars/token is a common rule of thumb for English prose.
DEFAULT_CHARS_PER_TOKEN = 4


def sha256_text(text: str) -> str:
    """Compute the SHA-256 hex digest of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def estimate_tokens(text: str, chars_per_token: int = DEFAULT_CHARS_PER_TOKEN) -> int:
    """Estimate token count from character count.

    Uses the 4-chars-per-token heuristic. Good enough for
    static analysis; runtime metrics can refine this.
    """
    if not text:
        return 0
    return max(1, len(text) // chars_per_token)


def estimate_tokens_from_bytes(size_bytes: int, chars_per_token: int = DEFAULT_CHARS_PER_TOKEN) -> int:
    """Estimate token count from file size, assuming ASCII."""
    return max(1, size_bytes // chars_per_token)


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string with Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_timestamp(s: str) -> datetime | None:
    """Parse an ISO 8601 timestamp; return None on failure."""
    if not s:
        return None
    try:
        # Accept trailing Z
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass(frozen=True)
class FileInfo:
    """Lightweight wrapper around a file path with size + hash."""

    path: Path
    size_bytes: int
    content_hash: str

    @property
    def modified_timestamp(self) -> str:
        """Return the file's mtime as a UTC ISO 8601 string."""
        mtime = self.path.stat().st_mtime
        return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Artifacts we recognize as skills/agents
SKILL_EXTENSIONS = {".md", ".markdown", ".yaml", ".yml", ".json", ".txt", ".prompt"}
SKILL_BASENAMES = {"SKILL", "AGENT", "AGENTS", "PROMPT", "INSTRUCTIONS"}

# Patterns that suggest a skill/agent file
SKILL_PATH_HINTS = re.compile(
    r"(^|/)(" + "|".join(["skills", "agents", "prompts", "instructions"]) + r")(/|$)",
    re.IGNORECASE,
)


def is_skill_artifact(path: Path, root: Path) -> bool:
    """Return True if a file looks like a skill or agent artifact.

    Heuristic: a file is a candidate if it has a recognized
    extension AND is under a directory whose name suggests a
    skill/agent location, OR has a recognized basename.
    """
    if path.suffix.lower() not in SKILL_EXTENSIONS:
        return False
    rel = str(path.relative_to(root))
    if SKILL_PATH_HINTS.search(rel):
        return True
    if path.stem.upper() in SKILL_BASENAMES:
        return True
    return False


def walk_files(root: Path) -> Iterator[Path]:
    """Yield every regular file under root, deterministically."""
    if not root.exists():
        return
    for p in sorted(root.rglob("*")):
        if p.is_file():
            yield p


def read_text_safe(path: Path) -> str:
    """Read a file as text, returning '' on any decode error."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="replace")


def write_json(path: Path, data: object) -> None:
    """Write data as JSON to path, with deterministic key sorting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    """Write text to path, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def relative_to_root(path: Path, root: Path) -> str:
    """Return a forward-slash relative path."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    return str(rel).replace(os.sep, "/")
