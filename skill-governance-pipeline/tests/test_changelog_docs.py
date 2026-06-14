"""BDD tests for the CHANGELOG.md file.

Locks in the contract that:
- CHANGELOG.md exists at the SGP project root
- It has a [1.0.0] section with the key release metadata
- The version in pyproject.toml matches the latest version
  in the changelog

These tests are the durable form of "the release is real,
not just a tag."
"""
from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG_PATH = PROJECT_ROOT / "CHANGELOG.md"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_version(pyproject_text: str) -> str | None:
    """Find the `version = "X.Y.Z"` line in pyproject.toml."""
    m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
    return m.group(1) if m else None


def _extract_changelog_versions(changelog_text: str) -> list[str]:
    """Find all version headers in the changelog (`## [X.Y.Z] - ...`)."""
    return re.findall(r"^##\s+\[([^\]]+)\]", changelog_text, re.MULTILINE)


class TestChangelogExists:
    """The CHANGELOG.md must exist and be non-empty."""

    def test_changelog_file_exists(self) -> None:
        """Given the SGP project root
        When we look for the changelog
        Then CHANGELOG.md exists.
        """
        assert CHANGELOG_PATH.exists(), (
            f"Expected CHANGELOG.md at {CHANGELOG_PATH}, but it doesn't exist."
        )

    def test_changelog_is_non_empty(self) -> None:
        """Given the changelog
        When we read it
        Then it has at least one version section.
        """
        text = _read_text(CHANGELOG_PATH)
        versions = _extract_changelog_versions(text)
        assert len(versions) >= 1, (
            f"Expected at least 1 version in CHANGELOG.md, got {versions}"
        )


class TestChangelogV100Section:
    """The 1.0.0 release section must have key metadata."""

    def test_changelog_has_1_0_0_section(self) -> None:
        """Given the changelog
        When we look for the 1.0.0 release
        Then the [1.0.0] section exists.
        """
        text = _read_text(CHANGELOG_PATH)
        versions = _extract_changelog_versions(text)
        assert "1.0.0" in versions, (
            f"Expected [1.0.0] in CHANGELOG.md, got versions: {versions}"
        )

    def test_changelog_1_0_0_has_quality_metrics(self) -> None:
        """Given the [1.0.0] section
        When we read it
        Then it mentions test count, coverage, and lint status
        (so the release isn't a tag without substance).
        """
        text = _read_text(CHANGELOG_PATH)
        # Extract the 1.0.0 section
        m = re.search(
            r"^##\s+\[1\.0\.0\].*?(?=^##\s+\[|^---|\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        assert m, "Could not find [1.0.0] section"
        section = m.group(0)
        for kw in ["Tests", "coverage", "mypy", "ruff"]:
            assert kw.lower() in section.lower(), (
                f"Expected quality metric {kw!r} in 1.0.0 section.\n"
                f"Section: {section[:500]}"
            )

    def test_changelog_1_0_0_has_added_section(self) -> None:
        """Given the [1.0.0] section
        When we read it
        Then it has an 'Added' subsection listing the modules
        (so users can see what shipped).
        """
        text = _read_text(CHANGELOG_PATH)
        m = re.search(
            r"^##\s+\[1\.0\.0\].*?(?=^##\s+\[|^---|\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        assert m, "Could not find [1.0.0] section"
        section = m.group(0)
        assert "### Added" in section, (
            f"Expected '### Added' subsection in 1.0.0.\n"
            f"Section: {section[:500]}"
        )

    def test_changelog_1_0_0_lists_core_modules(self) -> None:
        """Given the [1.0.0] section
        When we read it
        Then it mentions at least 5 core modules by name
        (so the release is substantive, not a stub).
        """
        text = _read_text(CHANGELOG_PATH)
        m = re.search(
            r"^##\s+\[1\.0\.0\].*?(?=^##\s+\[|^---|\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        section = m.group(0) if m else ""
        core_modules = [
            "discovery.py",
            "metadata_parser.py",
            "contract_validator.py",
            "dependency_analyzer.py",
            "overlap_analyzer.py",
            "roi_scorer.py",
            "recommendation_engine.py",
            "ci_gate.py",
        ]
        mentioned = [m for m in core_modules if m in section]
        assert len(mentioned) >= 5, (
            f"Expected at least 5 core modules in 1.0.0 section, "
            f"found {len(mentioned)}: {mentioned}"
        )


class TestChangelogVersionMatchesPyproject:
    """The CHANGELOG version must match the pyproject.toml version."""

    def test_pyproject_version_appears_in_changelog(self) -> None:
        """Given the project version in pyproject.toml
        When we look for it in the changelog
        Then it appears as a release section.
        """
        pyproject = _read_text(PYPROJECT_PATH)
        changelog = _read_text(CHANGELOG_PATH)
        version = _extract_version(pyproject)
        assert version is not None, "Could not parse version from pyproject.toml"
        assert f"[{version}]" in changelog, (
            f"Version [{version}] from pyproject.toml not found in CHANGELOG.md"
        )
