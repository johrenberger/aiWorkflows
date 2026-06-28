"""Ensure no dreaming artifact captures hidden chain-of-thought or private reasoning."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DREAMING_DIR = REPO_ROOT / ".openclaw" / "dreaming"

# Section headings that indicate hidden / private reasoning capture.
FORBIDDEN_HEADINGS = (
    "## Reasoning",
    "## Internal Analysis",
    "## Internal Reasoning",
    "## Hidden Thoughts",
    "## Hidden Chain",
    "## Chain of Thought",
    "## Private Reasoning",
    "## CoT",
)

# Substring markers (case-insensitive) that indicate reasoning envelopes.
FORBIDDEN_MARKERS = (
    "<<<REASONING>>>",
    "<<<HIDDEN>>>",
    "<reasoning>",
    "</reasoning>",
    "[[INTERNAL_THINKING]]",
)

# Files whose job is to document the no-hidden-reasoning rule itself.
# They necessarily mention the marker strings; this is not capture.
RULE_DOCUMENTING_FILES = {
    "validation-checklist.md",
    "README.md",
    "workflow-nightly-dreaming.md",
}


def _all_dreaming_files() -> list[Path]:
    return [p for p in DREAMING_DIR.rglob("*") if p.is_file()]


def _all_dreaming_files_excluding_rule_docs() -> list[Path]:
    return [
        p
        for p in _all_dreaming_files()
        if p.name not in RULE_DOCUMENTING_FILES
    ]


def _all_artifact_files() -> list[Path]:
    """Same as `_all_dreaming_files` but exposed for clarity."""
    return _all_dreaming_files()


@pytest.mark.parametrize(
    "path",
    _all_dreaming_files_excluding_rule_docs(),
    ids=lambda p: str(p.relative_to(REPO_ROOT)),
)
def test_no_forbidden_heading(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for heading in FORBIDDEN_HEADINGS:
        assert heading not in text, (
            f"Forbidden heading {heading!r} found in {path.relative_to(REPO_ROOT)}"
        )


@pytest.mark.parametrize(
    "path",
    _all_dreaming_files_excluding_rule_docs(),
    ids=lambda p: str(p.relative_to(REPO_ROOT)),
)
def test_no_forbidden_marker(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    for marker in FORBIDDEN_MARKERS:
        assert marker.lower() not in lowered, (
            f"Forbidden marker {marker!r} found in {path.relative_to(REPO_ROOT)}"
        )


@pytest.mark.parametrize("path", _all_dreaming_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_no_fenced_reasoning_block(path: Path) -> None:
    """A fenced block whose info string is 'reasoning' is forbidden."""
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            # opening fence: e.g. ```reasoning or ~~~reasoning
            after_fence = stripped.lstrip("`~").strip().lower()
            assert after_fence != "reasoning", (
                f"Fenced 'reasoning' block found in {path.relative_to(REPO_ROOT)}: {line!r}"
            )


def test_root_dreaming_md_has_no_hidden_reasoning() -> None:
    text = (REPO_ROOT / "DREAMING.md").read_text(encoding="utf-8")
    for heading in FORBIDDEN_HEADINGS:
        assert heading not in text
    lowered = text.lower()
    for marker in FORBIDDEN_MARKERS:
        assert marker.lower() not in lowered
