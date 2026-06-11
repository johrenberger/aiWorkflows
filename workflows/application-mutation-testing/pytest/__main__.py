from __future__ import annotations

import importlib.util
import inspect
import sys
import traceback
from pathlib import Path

from pytest import SkipTest, resolve_arguments


def load_module(module_path: Path, synthetic_name: str):
    spec = importlib.util.spec_from_file_location(synthetic_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_test_files(paths: list[str]) -> list[Path]:
    if not paths:
        paths = ["tests"]

    discovered: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file():
            discovered.append(path)
            continue
        discovered.extend(
            sorted(
                test_path
                for test_path in path.rglob("test_*.py")
                if "fixtures" not in test_path.parts
            )
        )
    return sorted(dict.fromkeys(discovered))


def load_fixture_functions(project_root: Path):
    conftest_path = project_root / "tests" / "conftest.py"
    fixture_functions = {}
    if conftest_path.exists():
        conftest = load_module(conftest_path, "_local_conftest")
        for name, value in vars(conftest).items():
            if callable(value) and getattr(value, "__pytest_fixture__", False):
                fixture_functions[name] = value
    return fixture_functions


def run_test_function(test_function, fixture_functions):
    markers = getattr(test_function, "__pytest_markers__", [])
    for marker in markers:
        if getattr(marker, "condition", False):
            raise SkipTest(marker.reason)

    cache = {}
    finalizers = []
    try:
        kwargs = resolve_arguments(test_function, fixture_functions, cache, finalizers)
        test_function(**kwargs)
    finally:
        for finalizer in reversed(finalizers):
            if finalizer is not None:
                finalizer.cleanup()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    filtered_args = [arg for arg in args if not arg.startswith("-")]
    project_root = Path.cwd()
    fixture_functions = load_fixture_functions(project_root)
    test_files = discover_test_files(filtered_args)

    total = 0
    failures = 0
    skipped = 0

    for index, test_file in enumerate(test_files):
        module = load_module(test_file, f"_test_module_{index}")
        for name, value in vars(module).items():
            if inspect.isfunction(value) and name.startswith("test_"):
                total += 1
                try:
                    run_test_function(value, fixture_functions)
                    sys.stdout.write(".")
                except SkipTest:
                    skipped += 1
                    sys.stdout.write("s")
                except Exception:
                    failures += 1
                    sys.stdout.write("F")
                    sys.stdout.write(f"\n\nFAILED {test_file}::{name}\n")
                    traceback.print_exc()

    sys.stdout.write("\n")
    sys.stdout.write(f"{total} tests collected\n")
    sys.stdout.write(f"{total - failures - skipped} passed, {failures} failed, {skipped} skipped\n")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
