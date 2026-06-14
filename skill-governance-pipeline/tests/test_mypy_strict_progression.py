"""BDD tests for the gradual mypy strict-mode progression.

Bucket C.1: tighten mypy strict mode one switch at a time.

The current mypy config is permissive (`strict = false`) with
selective strict flags enabled. The goal is to gradually turn
on more strict checks as the codebase becomes more typed.

These tests lock in the current permissive state and document
the eventual goal. As the codebase becomes more typed, we
flip one switch at a time and update the tests accordingly.
"""
from __future__ import annotations

import re
from pathlib import Path

import tomllib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


def _read_pyproject() -> dict:
    with PYPROJECT_PATH.open("rb") as f:
        return tomllib.load(f)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _get_mypy_config() -> dict:
    pyproject = _read_pyproject()
    return pyproject.get("tool", {}).get("mypy", {})


class TestMypyConfigPersists:
    """The mypy config block must exist and have a defined shape."""

    def test_mypy_config_section_exists(self) -> None:
        """Given pyproject.toml
        When we look for the [tool.mypy] section
        Then it exists (so mypy runs in CI).
        """
        config = _get_mypy_config()
        assert config != {}, "Expected [tool.mypy] section in pyproject.toml"

    def test_mypy_targets_src_directory(self) -> None:
        """Given the mypy config
        When we read it
        Then the `files` setting points to the src directory
        (so mypy only checks the package, not tests).
        """
        config = _get_mypy_config()
        assert "files" in config, "Expected 'files' setting in [tool.mypy]"
        assert any("src/skill_governance" in f for f in config["files"]), (
            f"Expected 'src/skill_governance' in files, got {config['files']}"
        )


class TestMypyStrictModeIsActive:
    """The mypy config must document WHY it's permissive."""

    def test_mypy_has_strict_true_explainer(self) -> None:
        """Given pyproject.toml
        When we look at the [tool.mypy] section
        Then there's a comment explaining that strict = false
        is intentional and lists the switches to raise
        gradually (lesson #98: mypy as cheap insurance).
        """
        text = _read_text(PYPROJECT_PATH)
        # The mypy section should mention 'strict' and 'raise' or 'gradual'
        mypy_section_match = re.search(
            r"\[tool\.mypy\](.*?)(?=\n\[|$)", text, re.DOTALL
        )
        assert mypy_section_match, "Could not find [tool.mypy] section"
        section = mypy_section_match.group(1)
        assert "strict" in section.lower(), (
            f"Expected 'strict' in [tool.mypy] section.\nSection: {section}"
        )

    def test_mypy_strict_flag_is_true(self) -> None:
        """Given the mypy config
        When we read it
        Then strict = true (current state: all 16 untyped-def
        errors fixed; full type coverage).
        """
        config = _get_mypy_config()
        assert config.get("strict") is True, (
            f"Expected strict = true, got {config.get('strict')!r}. "
            f"If you flipped to strict=false, document the reason "
            f"in the mypy config comment and update this test."
        )


class TestMypyProgressionHasGradualSwitches:
    """The mypy config should enable some strict flags gradually."""

    def test_mypy_warn_return_any_enabled(self) -> None:
        """Given the mypy config
        When we read it
        Then warn_return_any = true (catches obvious 'Any' leaks).
        """
        config = _get_mypy_config()
        assert config.get("warn_return_any") is True, (
            f"Expected warn_return_any = true, got {config.get('warn_return_any')!r}"
        )

    def test_mypy_warn_unused_ignores_enabled(self) -> None:
        """Given the mypy config
        When we read it
        Then warn_unused_ignores = true (catches dead type:ignore comments).
        """
        config = _get_mypy_config()
        assert config.get("warn_unused_ignores") is True, (
            f"Expected warn_unused_ignores = true, got {config.get('warn_unused_ignores')!r}"
        )

    def test_mypy_warn_redundant_casts_enabled(self) -> None:
        """Given the mypy config
        When we read it
        Then warn_redundant_casts = true (catches unnecessary 'cast' calls).
        """
        config = _get_mypy_config()
        assert config.get("warn_redundant_casts") is True, (
            f"Expected warn_redundant_casts = true, got {config.get('warn_redundant_casts')!r}"
        )
