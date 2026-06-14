#!/usr/bin/env python3
"""Run mypy in strict mode and report the current error count.

The SGP mypy config is currently `strict = false` (permissive)
because the codebase has 16 untyped-def errors. This script
shows the current error count so we can track progress as
contributors add type annotations.

To tighten mypy strict mode:
1. Run this script: `python3 run_mypy_strict.py`
2. Fix the errors (start with `no-untyped-def`, the most common)
3. Re-run; the error count should decrease
4. When the count is 0, flip `strict = true` in pyproject.toml

Usage: python3 run_mypy_strict.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


REPO = Path(__file__).resolve().parent


def main() -> int:
    """Run mypy --strict, report error count and error types."""
    print("=" * 80)
    print("Running mypy --strict on src/skill_governance/")
    print("=" * 80)
    result = subprocess.run(
        [
            "python3", "-m", "mypy", "--no-incremental", "--strict",
            "src/skill_governance/",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    # mypy writes errors to stdout
    output = result.stdout
    if not output:
        print("No errors found! Strict mode is clean. Flip strict=true in pyproject.toml.")
        return 0
    # Parse errors: each line is "path:line: error: <message> [<code>]"
    error_pattern = re.compile(r"^src/sk.*?:(\d+): error: (.*?)\s+\[([\w-]+)\]")
    errors: list[tuple[int, str, str]] = []
    for line in output.splitlines():
        m = error_pattern.match(line)
        if m:
            errors.append((int(m.group(1)), m.group(2), m.group(3)))
    if not errors:
        print("Could not parse mypy output. Raw output:")
        print(output)
        return 1
    by_code = Counter(code for _, _, code in errors)
    by_file = Counter(line.split(":")[0] for line in output.splitlines() if error_pattern.match(line))
    print(f"\nTotal errors: {len(errors)}")
    print(f"\nBy error code:")
    for code, count in by_code.most_common():
        print(f"  [{code:20s}]  {count:3d} occurrences")
    print(f"\nBy file:")
    for f, count in by_file.most_common():
        print(f"  {f:50s}  {count:3d} errors")
    print(f"\nFirst 5 errors (for the highest-priority code {by_code.most_common(1)[0][0]}):")
    target_code = by_code.most_common(1)[0][0]
    for line, msg, code in errors:
        if code == target_code:
            print(f"  {code}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
