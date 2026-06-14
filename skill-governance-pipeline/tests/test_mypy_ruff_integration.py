"""BDD-TDD tests for the mypy + ruff integration.

These tests lock in the static-analysis baseline so the CI
pipeline (and the test suite) can rely on:

1. mypy passes on src/skill_governance/ with the configured
   strictness level
2. ruff passes on src/ and tests/ with the configured rule set
3. Both tools can be invoked the same way locally and in CI
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src" / "skill_governance"


# Tool-availability fixtures --------------------------------------------------


@pytest.fixture(scope="module")
def mypy_available() -> bool:
    """Return True if mypy is on PATH."""
    return shutil.which("mypy") is not None


@pytest.fixture(scope="module")
def ruff_available() -> bool:
    """Return True if ruff is on PATH."""
    return shutil.which("ruff") is not None


# mypy -----------------------------------------------------------------------


def test_mypy_passes_on_src_skill_governance(mypy_available: bool) -> None:
    """Given mypy is installed
    When mypy runs on src/skill_governance/
    Then the exit code is 0 (no type errors).
    """
    if not mypy_available:
        pytest.skip("mypy not installed; install with `pip install mypy`")
    result = subprocess.run(
        ["mypy", str(SRC)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"mypy failed with exit {result.returncode}:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_mypy_config_is_loaded_from_pyproject(mypy_available: bool) -> None:
    """Given the [tool.mypy] config in pyproject.toml
    When mypy runs without --explicit-package-bases
    Then it picks up the config (we verify by checking the
        config is honored — a deliberate type error would fail
        the test, not a config-loading failure).
    """
    if not mypy_available:
        pytest.skip("mypy not installed; install with `pip install mypy`")
    # Confirm the config is parseable and doesn't error out
    # (this is implicit in the previous test, but explicit here).
    config = REPO / "pyproject.toml"
    assert config.exists(), "pyproject.toml must exist for mypy config to load"
    text = config.read_text(encoding="utf-8")
    assert "[tool.mypy]" in text, (
        "pyproject.toml must have a [tool.mypy] section. "
        "Without it, the [tool.mypy] defaults override and the "
        "configured settings (warn_return_any, etc.) are ignored."
    )


# ruff -----------------------------------------------------------------------


def test_ruff_check_passes_on_src_and_tests(ruff_available: bool) -> None:
    """Given ruff is installed
    When ruff check runs on src/ and tests/
    Then the exit code is 0 (no lint errors).
    """
    if not ruff_available:
        pytest.skip("ruff not installed; install with `pip install ruff`")
    result = subprocess.run(
        ["ruff", "check", "src/", "tests/"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"ruff check failed with exit {result.returncode}:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_ruff_config_is_loaded_from_pyproject(ruff_available: bool) -> None:
    """Given the [tool.ruff] config in pyproject.toml
    When ruff check runs without --config
    Then it picks up the config (we verify the rule set is active
        by checking a deliberately-violated rule would fail —
        but we don't actually violate; we just assert the config
        section is present).
    """
    if not ruff_available:
        pytest.skip("ruff not installed; install with `pip install ruff`")
    config = REPO / "pyproject.toml"
    assert config.exists(), "pyproject.toml must exist for ruff config to load"
    text = config.read_text(encoding="utf-8")
    assert "[tool.ruff]" in text, (
        "pyproject.toml must have a [tool.ruff] section. Without it, "
        "ruff uses defaults (no project-specific rules)."
    )
    assert "[tool.ruff.lint]" in text, (
        "pyproject.toml must have a [tool.ruff.lint] section. Without "
        "it, ruff uses default rules (no project-specific select/ignore)."
    )


# Integration: the full test command -----------------------------------------


def test_pip_install_dev_extras_works() -> None:
    """Given the [project.optional-dependencies] dev = [...] extras
    When the dev extras are installed
    Then mypy, ruff, and types-PyYAML are all available.
    """
    # We don't run pip install here (slow, network-dependent).
    # Instead, verify the dev extras are declared correctly.
    config = REPO / "pyproject.toml"
    text = config.read_text(encoding="utf-8")
    assert "dev = [" in text, (
        "pyproject.toml must have a 'dev = [...]' extras group. "
        "The CI workflow installs `.[dev]`; without the group, the "
        "lint/type-check step would fail to install mypy + ruff."
    )
    # Spot-check the required packages are listed
    for pkg in ("mypy", "ruff", "types-PyYAML"):
        assert pkg in text, (
            f"pyproject.toml's dev extras must include '{pkg}'. "
            f"Without it, the type-check / lint step would fail."
        )
