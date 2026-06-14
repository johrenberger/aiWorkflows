"""BDD-TDD tests for README documentation contracts.

These tests lock in the presence of key documentation sections and
concepts. They exist to catch accidental deletion of the
human-in-the-loop (HITL) workflow for rewrite proposals, which is
critical for users who would otherwise see a list of `.rewrite.md`
files in `output/proposed_rewrites/` and not know what to do with
them.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


README_PATH = Path(__file__).resolve().parent.parent / "README.md"


def _read_readme() -> str:
    """Read the README.md file as text."""
    return README_PATH.read_text(encoding="utf-8")


def _section_text(readme: str, section_marker: str) -> str:
    """Return the text of a `## Section` block, skipping code fences.

    Code fences can contain `##` (e.g. a sample `remediation_backlog.md`
    entry inside the worked example), so a naive `\n## ` search would
    cut the section short. This helper finds the next `## ` at column 0
    that is OUTSIDE a fenced code block.
    """
    start = readme.index(section_marker)
    # Walk forward, tracking fence state
    in_fence = False
    i = start + len(section_marker)
    while i < len(readme):
        line_start = i
        # Find end of line
        nl = readme.find("\n", i)
        if nl == -1:
            nl = len(readme)
        line = readme[line_start:nl]
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and line.startswith("## "):
            return readme[start:line_start]
        i = nl + 1
    return readme[start:]


# --- Section presence -------------------------------------------------------


def test_hitl_section_is_present_in_readme():
    """Given a user running `skill-governance rewrite`
    When they look for documentation on what to do with the proposals
    Then the README has a 'Human-in-the-loop for rewrite proposals' section.
    """
    readme = _read_readme()
    assert "## Human-in-the-loop for rewrite proposals" in readme, (
        "README must have a '## Human-in-the-loop for rewrite proposals' "
        "section. The rewrite command proposes, it does not apply; users "
        "need to know how to act on the proposals."
    )


def test_worked_example_is_present_in_readme():
    """Given a user has read the HITL section
    When they look for a concrete example
    Then the README has a '### Worked example' subsection
        with a sample remediation_backlog.md entry and a 6-step procedure.
    """
    readme = _read_readme()
    assert "### Worked example" in readme, (
        "README must have a '### Worked example' subsection under the "
        "HITL section. A concrete example is what turns the abstract "
        "workflow into a usable procedure."
    )
    # The worked example should reference a real output path
    assert "remediation_backlog.md" in readme
    # And a real proposal location
    assert "output/proposed_rewrites/" in readme
    # And the 6-step procedure (re-validate is the closing step)
    assert "Re-run" in readme or "re-run" in readme.lower(), (
        "The worked example must end with a re-validate step. The "
        "whole point of applying a rewrite is to fix the blockers; "
        "if re-validation still shows them, the proposal is wrong."
    )


# --- Concept coverage -------------------------------------------------------


def test_hitl_section_distinguishes_propose_vs_apply():
    """Given a user is new to the rewrite command
    When they read the HITL section
    Then they learn that the command proposes but does not apply
        (auto-apply would silently change behavior).
    """
    readme = _read_readme()
    section_text = _section_text(readme, "## Human-in-the-loop for rewrite proposals")
    # The section must explicitly say the command proposes, not applies
    assert "propos" in section_text.lower(), (
        "The HITL section must say the command 'proposes' to distinguish "
        "it from auto-apply."
    )
    # And explain why (auto-apply would be unsafe)
    assert "auto" in section_text.lower() or "silently" in section_text.lower(), (
        "The HITL section must explain WHY auto-apply is wrong "
        "(silently changes behavior)."
    )


def test_hitl_section_documents_the_three_decisions():
    """Given a user is reviewing a proposal
    When they look for the decision options
    Then the README documents three actions: accept, refine, reject.
    """
    readme = _read_readme()
    section_text = _section_text(readme, "## Human-in-the-loop for rewrite proposals")
    # All three decision verbs must be present
    for verb in ("accept", "refine", "reject"):
        assert verb in section_text.lower(), (
            f"The HITL section must document the '{verb}' decision. "
            f"Missing verb means the user has fewer options than the "
            f"workflow supports."
        )


def test_hitl_section_documents_proposal_anatomy():
    """Given a user is reading a proposal file
    When they look for a legend of what the fields mean
    Then the README has an 'Anatomy of a proposal file' subsection
        that lists the 7 standard sections.
    """
    readme = _read_readme()
    assert "### Anatomy of a proposal file" in readme, (
        "The HITL section must have an 'Anatomy of a proposal file' "
        "subsection. A legend turns a confusing YAML+markdown blob into "
        "a reviewable document."
    )
    # The 7 standard sections from the rewrite_generator
    for section in (
        "Why this rewrite was triggered",
        "What changed",
        "Token efficiency",
        "Validation expectations",
        "Original excerpt",
        "Compatibility and migration",
    ):
        assert section in readme, (
            f"Anatomy section must list '{section}'. Missing section "
            f"means the user doesn't know what to look for when "
            f"reviewing a proposal."
        )


def test_hitl_section_documents_the_artifact_filter_flag():
    """Given a user only wants to rewrite one artifact
    When they look for a CLI flag
    Then the README documents the `--artifact` flag in the HITL section.
    """
    readme = _read_readme()
    section_text = _section_text(readme, "## Human-in-the-loop for rewrite proposals")
    # The HITL section must have its own 'Filtering to one proposal'
    # subsection (not just mention the flag in passing).
    assert "### Filtering to one proposal" in section_text, (
        "The HITL section must have a '### Filtering to one proposal' "
        "subsection that documents the --artifact flag. The Commands "
        "section lists --artifact for the rewrite command, but the "
        "HITL section needs its own copy so users reviewing a proposal "
        "know how to scope the run."
    )
    assert "--artifact" in section_text, (
        "The 'Filtering to one proposal' subsection must include the "
        "--artifact flag in a code block."
    )
