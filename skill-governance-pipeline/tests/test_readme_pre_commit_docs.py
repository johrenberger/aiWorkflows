"""BDD tests for the README's pre-commit hook documentation.

The README has a `## Pre-commit hook` section that explains:
- How to install the hook
- What the hook does
- Required config and bypass
- Manual validation command

These tests verify the section exists with the right structure.
Locks in the contract that the docs are present and accurate.
"""
from __future__ import annotations

from pathlib import Path

README_PATH = Path(__file__).resolve().parents[1] / "README.md"


def _extract_section(text: str, heading: str) -> str:
    """Extract a markdown section starting at the given heading (level 2).

    Stops at the next level-2 heading. Strips fenced code blocks
    before extraction so the snippet is human-readable.
    """
    lines = text.splitlines()
    in_section = False
    section_lines: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if line.strip() == heading:
                in_section = True
                continue
            elif in_section:
                break
        if in_section:
            # Skip fenced code blocks
            if line.strip().startswith("```"):
                continue
            section_lines.append(line)
    return "\n".join(section_lines).strip()


class TestReadmePreCommitSectionExists:
    """The README must have a `## Pre-commit hook` section."""

    def test_readme_has_pre_commit_hook_heading(self) -> None:
        """Given the README
        When we look for the pre-commit hook section heading
        Then `## Pre-commit hook` exists.
        """
        readme = README_PATH.read_text(encoding="utf-8")
        assert "## Pre-commit hook" in readme, (
            f"Expected '## Pre-commit hook' heading in README. "
            f"Found headings: {[line for line in readme.splitlines() if line.startswith('## ')]}"
        )

    def test_pre_commit_section_mentions_install_hooks_command(self) -> None:
        """Given the pre-commit section
        When we read it
        Then it mentions the `install-hooks` command.
        """
        readme = README_PATH.read_text(encoding="utf-8")
        section = _extract_section(readme, "## Pre-commit hook")
        assert "install-hooks" in section, (
            f"Expected 'install-hooks' command mentioned in pre-commit section.\n"
            f"Section: {section[:500]}"
        )

    def test_pre_commit_section_mentions_validate_files_command(self) -> None:
        """Given the pre-commit section
        When we read it
        Then it mentions the `validate-files` command (the surface
        the hook actually uses).
        """
        readme = README_PATH.read_text(encoding="utf-8")
        section = _extract_section(readme, "## Pre-commit hook")
        assert "validate-files" in section, (
            f"Expected 'validate-files' command mentioned in pre-commit section.\n"
            f"Section: {section[:500]}"
        )

    def test_pre_commit_section_explains_bypass(self) -> None:
        """Given the pre-commit section
        When we read it
        Then it explains how to bypass the hook (so users know
        they're not trapped if it fires).
        """
        readme = README_PATH.read_text(encoding="utf-8")
        section = _extract_section(readme, "## Pre-commit hook")
        assert "--no-verify" in section, (
            f"Expected '--no-verify' bypass explanation in pre-commit section.\n"
            f"Section: {section[:500]}"
        )

    def test_pre_commit_section_explains_required_config(self) -> None:
        """Given the pre-commit section
        When we read it
        Then it explains which governance config file the hook
        looks for (governance.yaml, governance.local.yaml,
        governance.default.yaml).
        """
        readme = README_PATH.read_text(encoding="utf-8")
        section = _extract_section(readme, "## Pre-commit hook")
        for config_name in ["governance.yaml", "governance.local.yaml", "governance.default.yaml"]:
            assert config_name in section, (
                f"Expected '{config_name}' mentioned in pre-commit section.\n"
                f"Section: {section[:500]}"
            )
