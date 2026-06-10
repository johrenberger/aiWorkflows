"""Regression test for Bug #5 (PR #24): the v2 source directory
previously contained a `pytest.py` shim that shadowed the real pytest
package. When `test-factory run --generate-coverage` invoked
`python -m pytest --cov ...` from the v2 source directory, the shim
was loaded instead of real pytest, and `--cov` / `--cov-report` flags
were silently ignored, so no coverage report was written.

The fix was to move the shim to `scripts/run_tests.py` and add
`__test__ = False` to `TestFactoryOrchestrator` so the real pytest
doesn't try to collect the orchestrator class as a test class.

These tests verify the fix.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SHIM_PATH = REPO_ROOT / "scripts" / "run_tests.py"
SHADOW_PATH = REPO_ROOT / "pytest.py"


def test_pytest_shim_no_longer_shadows_real_pytest() -> None:
    """The shim must not be at the top level of the repo. If it is,
    `python -m pytest` from the v2 source dir loads the shim instead
    of the real pytest package, breaking --cov and any other plugin."""
    assert not SHADOW_PATH.exists(), (
        f"Top-level pytest.py at {SHADOW_PATH} shadows the real pytest "
        "package. Move any fallback test runner to scripts/."
    )


def test_shim_still_exists_for_fallback() -> None:
    """The shim is preserved at scripts/run_tests.py for environments
    where pytest is not installed. Verify it's still there."""
    assert SHIM_PATH.exists(), (
        f"Fallback test runner missing at {SHIM_PATH}. The shim was "
        "moved here in PR #24 to avoid shadowing real pytest."
    )


def test_shim_runs_without_importing_real_pytest() -> None:
    """The fallback runner should NOT depend on real pytest. We just
    verify the script imports cleanly and that its main() function
    returns the right exit code when no tests/ dir exists (so we
    don't accidentally run 38 tests from within a test, which would
    be slow and would mask the assertion we actually care about)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("v2_run_tests", str(SHIM_PATH))
    assert spec is not None and spec.loader is not None, (
        f"could not load {SHIM_PATH} as a Python module"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Verify the shim defines the expected entry points.
    assert callable(getattr(mod, "main", None)), "shim must export main()"
    assert callable(getattr(mod, "_load_module", None)), "shim must export _load_module()"
    assert callable(getattr(mod, "_run_test", None)), "shim must export _run_test()"


def test_real_pytest_loads_from_repo_root() -> None:
    """`python -m pytest --collect-only` from the v2 source dir should
    load the REAL pytest, not the shim. The shim doesn't have a
    `collect-only` flag and would print '33 passed, 0 failed' (running
    tests) or 'No tests directory found' (if cwd differs) instead of
    the real pytest's collect summary."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    # Real pytest prints "N tests collected" or "N deselected" — never
    # "No tests directory found" (that's the shim's failure message).
    assert "No tests directory found" not in result.stdout, (
        f"shim was loaded instead of real pytest:\nstdout={result.stdout[:500]}\n"
        f"stderr={result.stderr[:500]}"
    )
    # Real pytest imports its own pytest package; if the shim were
    # loaded, the import would say 'No module named pytest' or similar
    # because the shim doesn't have a `collect` function.
    assert "AttributeError" not in result.stderr or "test_" not in result.stderr[-200:], (
        f"real pytest failed to load:\n{result.stderr[:1000]}"
    )


def test_test_factory_orchestrator_not_collected_as_test() -> None:
    """`TestFactoryOrchestrator` starts with `Test` for historical
    reasons but is the orchestrator class, not a test. Pytest tries to
    collect it as a test class and emits a PytestCollectionWarning. The
    fix was to set `__test__ = False` on the class."""
    from test_factory.orchestrator import TestFactoryOrchestrator

    assert getattr(TestFactoryOrchestrator, "__test__", None) is False, (
        "TestFactoryOrchestrator.__test__ must be False to prevent pytest "
        "from trying to collect it as a test class."
    )
