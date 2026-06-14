"""BDD tests for the README's recommend-task documentation.

The README has a `## recommend-task` section that explains:
- The command's purpose and example usage
- How the matching algorithm works (tokenize, index, score, sort)
- Limitations and pairings with the catalog guide

These tests verify the section exists with the right structure.
Locks in the contract that the docs are present.
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
            if line.strip().startswith("```"):
                continue
            section_lines.append(line)
    return "\n".join(section_lines).strip()


class TestReadmeRecommendTaskSection:
    """The README must have a `## recommend-task` section."""

    def test_readme_has_recommend_task_heading(self) -> None:
        """Given the README
        When we look for the recommend-task section heading
        Then `## recommend-task` exists.
        """
        readme = README_PATH.read_text(encoding="utf-8")
        assert "## recommend-task" in readme, (
            f"Expected '## recommend-task' heading in README. "
            f"Found headings: {[line for line in readme.splitlines() if line.startswith('## ')]}"
        )

    def test_recommend_task_section_has_example_command(self) -> None:
        """Given the recommend-task section
        When we read it
        Then it shows an example command (so users can see the usage).
        """
        readme = README_PATH.read_text(encoding="utf-8")
        section = _extract_section(readme, "## recommend-task")
        assert "recommend-task" in section, (
            f"Expected 'recommend-task' command in section.\n"
            f"Section: {section[:500]}"
        )
        assert "python" in section.lower() or "skill_governance" in section, (
            f"Expected python invocation in section.\n"
            f"Section: {section[:500]}"
        )

    def test_recommend_task_section_explains_algorithm(self) -> None:
        """Given the recommend-task section
        When we read it
        Then it explains the matching algorithm (so users
        understand the determinism and limitations).
        """
        readme = README_PATH.read_text(encoding="utf-8")
        section = _extract_section(readme, "## recommend-task")
        # Algorithm keywords: tokenize, score, overlap
        for kw in ["tokenize", "score", "match"]:
            assert kw in section.lower(), (
                f"Expected algorithm keyword {kw!r} in section.\n"
                f"Section: {section[:500]}"
            )

    def test_recommend_task_section_mentions_catalog_guide_pairing(self) -> None:
        """Given the recommend-task section
        When we read it
        Then it points to the CATALOG.md decision guide as a
        complementary tool (so users have the full navigation story).
        """
        readme = README_PATH.read_text(encoding="utf-8")
        section = _extract_section(readme, "## recommend-task")
        assert "CATALOG" in section or "catalog" in section, (
            f"Expected CATALOG.md mention in section.\n"
            f"Section: {section[:500]}"
        )

    def test_recommend_task_section_explains_limitations(self) -> None:
        """Given the recommend-task section
        When we read it
        Then it lists limitations (so users don't expect LLM-quality matches).
        """
        readme = README_PATH.read_text(encoding="utf-8")
        section = _extract_section(readme, "## recommend-task")
        assert "Limitation" in section or "limitation" in section.lower(), (
            f"Expected limitations section in recommend-task docs.\n"
            f"Section: {section[:500]}"
        )
