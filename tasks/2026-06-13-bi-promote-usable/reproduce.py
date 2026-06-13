#!/usr/bin/env python3
"""Calibration reproducer for backend-implementation promotion to usable.

Verifies the 3 with-skill use cases (UC2, UC3, UC4) on the
re-baselined johrenberger/spring-petclinic-rest fork produced
the artifacts the backend-implementation skill prescribes:
- 1 implementation report
- 1 handoff packet
- 1 validation-runner log

If all 3 use cases have all 3 artifacts, the skill is
demonstrably "usable" (artifacts are produced; the workflow
runs end-to-end).

The 4th use case (UC1) was the no-skill baseline; it has no
artifacts by design.
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path("/data/.openclaw/workspace")
TASKS = [
    ("UC2", "soft-delete on Visit",     "2026-06-13-bi-skill-test"),
    ("UC3", "caching on PetService",    "2026-06-13-bi-uc3"),
    ("UC4", "POST /api/pets-with-owner", "2026-06-13-bi-uc4"),
]

REQUIRED_ARTIFACTS = [
    ("implementation report", "reports/backend-implementation-report.md"),
    ("handoff packet",        "handoffs/"),
    ("validation-runner log", "validation/logs/mvnw_test.log"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    print(f"=== backend-implementation → usable calibration reproducer ===")
    print(f"Run at: {now_iso()}\n")
    print(f"Verifying that 3 with-skill use cases produced the required artifacts.\n")

    overall_pass = True
    per_use_case = []

    for label, desc, task_id in TASKS:
        task_dir = WORKSPACE / "tasks" / task_id
        if not task_dir.is_dir():
            print(f"  [{label}] FAIL — task dir missing: {task_dir}")
            overall_pass = False
            per_use_case.append((label, desc, False, "task dir missing"))
            continue

        results = []
        case_pass = True
        for artifact_name, rel_path in REQUIRED_ARTIFACTS:
            full_path = task_dir / rel_path
            # Use exists() for files, is_dir() for the handoffs/ directory
            if rel_path.endswith("/"):
                ok = full_path.is_dir() and any(full_path.iterdir())
            else:
                ok = full_path.is_file() and full_path.stat().st_size > 0
            results.append((artifact_name, ok))
            if not ok:
                case_pass = False

        status = "PASS" if case_pass else "FAIL"
        per_use_case.append((label, desc, case_pass, results))
        if not case_pass:
            overall_pass = False
        print(f"  [{label}] {status} — {desc}")
        for name, ok in results:
            mark = "✓" if ok else "✗"
            print(f"      {mark} {name}")

    print()
    print(f"=== OVERALL: {'PASS' if overall_pass else 'FAIL'} ===")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
