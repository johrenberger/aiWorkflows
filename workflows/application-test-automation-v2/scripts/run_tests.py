"""Fallback test runner for environments where pytest is not installed.

This script previously lived at ./pytest.py and was a `python -m pytest`
shim. That placement had a critical bug: when invoked from the v2 source
dir, the shim's module name `pytest` shadowed the real pytest package,
so any subprocess call like `python -m pytest --cov ...` (which the v2
adapter's `discover_test_command` and `discover_coverage_command` both
issue via subprocess.run) silently ran the shim instead of the real
pytest. The shim didn't support --cov, so coverage reports were never
written and the test-factory pipeline would report `no_report_written`.

Moved to scripts/run_tests.py (Bug #5, PR #24). Invoke directly:
`python scripts/run_tests.py`. For real test runs use `python -m pytest`.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
import tempfile
import traceback
from pathlib import Path


def _load_module(path: Path):
    module_name = "test_" + "_".join(path.with_suffix("").parts[-3:])
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _run_test(func):
    params = inspect.signature(func).parameters
    kwargs = {}
    temp_dir = None
    if "tmp_path" in params:
        temp_dir = tempfile.TemporaryDirectory()
        kwargs["tmp_path"] = Path(temp_dir.name)
    try:
        func(**kwargs)
        return True, ""
    except Exception:
        return False, traceback.format_exc()
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    test_root = Path.cwd() / "tests"
    if not test_root.exists():
        print("No tests directory found.")
        return 1
    test_files = [path for path in sorted(test_root.rglob("test_*.py")) if "fixtures" not in path.parts]
    total = 0
    failures = 0
    failure_details = []
    for path in test_files:
        module = _load_module(path)
        for name in sorted(dir(module)):
            if not name.startswith("test_"):
                continue
            obj = getattr(module, name)
            if callable(obj):
                total += 1
                ok, detail = _run_test(obj)
                if not ok:
                    failures += 1
                    failure_details.append((f"{path}:{name}", detail))
    for label, detail in failure_details:
        print(f"FAIL {label}")
        print(detail)
    passed = total - failures
    print(f"{passed} passed, {failures} failed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
