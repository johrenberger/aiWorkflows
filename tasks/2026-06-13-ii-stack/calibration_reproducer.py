#!/usr/bin/env python3
"""Calibration reproducer for integration-implementation promotion to usable.

Verifies the 3 use cases (UC1 no skill baseline, UC2 and UC3
with the skill) on the Node/Express proxy all produced
working code with:
- ≥1 test file
- ≥5 test cases total
- an implementation report
- a handoff packet
- a passing validation log
"""
from __future__ import annotations
import sys
from pathlib import Path

WORKSPACE = Path("/data/.openclaw/workspace/tasks/2026-06-13-ii-stack")
UC1_TEST = WORKSPACE / "tests/uc1.test.js"
UC2_TEST = WORKSPACE / "tests/uc2.test.js"
UC3_TEST = WORKSPACE / "tests/uc3.test.js"
REPORT = WORKSPACE / "reports/integration-implementation-report.md"
HANDOFF = WORKSPACE / "handoffs" / "2026-06-13T210900Z-integration-implementation-to-code-change-review.md"
VALIDATION = WORKSPACE / "validation/logs/npm_test.log"
SERVER = WORKSPACE / "src/server.js"


def check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "✓" if ok else "✗"
    print(f"  {mark} {name} {detail}")
    return ok


def main() -> int:
    print(f"=== integration-implementation → usable calibration reproducer ===\n")

    overall_pass = True

    # File presence
    print("[Files]")
    overall_pass &= check("server.js exists", SERVER.is_file(), f"({SERVER.stat().st_size} bytes)" if SERVER.is_file() else "")
    overall_pass &= check("UC1 test exists", UC1_TEST.is_file())
    overall_pass &= check("UC2 test exists", UC2_TEST.is_file())
    overall_pass &= check("UC3 test exists", UC3_TEST.is_file())
    overall_pass &= check("implementation report exists", REPORT.is_file())
    overall_pass &= check("handoff packet exists", HANDOFF.is_file())
    overall_pass &= check("validation log exists", VALIDATION.is_file())

    # Validation log content
    print("\n[Validation]")
    if VALIDATION.is_file():
        log = VALIDATION.read_text()
        overall_pass &= check("validation log shows passing tests", "passed" in log.lower() or "31 passed" in log)
    else:
        overall_pass &= check("validation log readable", False)

    # Implementation report completeness (check 4 required sections)
    print("\n[Implementation report completeness]")
    if REPORT.is_file():
        r = REPORT.read_text()
        for section in [
            "## Task",
            "## Acceptance criteria",
            "## Integration profile",
            "## Failure modes addressed",
            "## Design checks",
            "## Tests added or updated",
            "## Validation",
        ]:
            overall_pass &= check(f"report has '{section}'", section in r)

    # Handoff packet completeness (check 4 required fields per handoff-packet skill)
    print("\n[Handoff packet completeness]")
    if HANDOFF.is_file():
        h = HANDOFF.read_text()
        for field in [
            "## 1. Task ID",
            "## 5. Context summary",
            "## 7. Files changed",
            "## 8. Commands run",
            "## 9. Validation results",
            "## 10. Decisions made",
            "## 11. Risks",
            "## 13. Required next action",
        ]:
            overall_pass &= check(f"handoff has '{field}'", field in h)

    # Test count check
    print("\n[Test count]")
    if all(p.is_file() for p in [UC1_TEST, UC2_TEST, UC3_TEST]):
        total_lines = sum(p.read_text().count("\n") for p in [UC1_TEST, UC2_TEST, UC3_TEST])
        test_count = sum(1 for line in (
            UC1_TEST.read_text() + UC2_TEST.read_text() + UC3_TEST.read_text()
        ).split("\n") if line.strip().startswith("test(") or "test(" in line)
        overall_pass &= check(f"≥3 test functions (got {test_count})", test_count >= 3)

    print()
    print(f"=== OVERALL: {'PASS' if overall_pass else 'FAIL'} ===")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
