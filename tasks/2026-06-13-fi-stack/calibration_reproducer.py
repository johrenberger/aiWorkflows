#!/usr/bin/env python3
"""Calibration reproducer for frontend-implementation promotion to usable."""
import sys
from pathlib import Path

WORKSPACE = Path("/data/.openclaw/workspace/tasks/2026-06-13-fi-stack")
UC1_TEST = WORKSPACE / "tests/uc1.test.jsx"
UC2_TEST = WORKSPACE / "tests/uc2.test.jsx"
UC3_TEST = WORKSPACE / "tests/uc3.test.jsx"
REPORT = WORKSPACE / "reports/frontend-implementation-report.md"
HANDOFF = WORKSPACE / "handoffs" / "2026-06-13T233900Z-frontend-implementation-to-code-change-review.md"
VALIDATION = WORKSPACE / "validation/logs/npm_test.log"
PET_VISIT_LIST = WORKSPACE / "src/components/PetVisitList.jsx"
NEW_VISIT_FORM = WORKSPACE / "src/components/NewVisitForm.jsx"
PET_TYPE_FILTER = WORKSPACE / "src/components/PetTypeFilter.jsx"


def check(name, ok, detail=""):
    mark = "✓" if ok else "✗"
    print(f"  {mark} {name} {detail}")
    return ok


def main():
    print(f"=== frontend-implementation → usable calibration reproducer ===\n")
    overall = True

    print("[Source files]")
    for p in [PET_VISIT_LIST, NEW_VISIT_FORM, PET_TYPE_FILTER]:
        overall &= check(f"{p.name} exists", p.is_file(),
                         f"({p.stat().st_size} bytes)" if p.is_file() else "")
    overall &= check("UC1 test exists", UC1_TEST.is_file())
    overall &= check("UC2 test exists", UC2_TEST.is_file())
    overall &= check("UC3 test exists", UC3_TEST.is_file())

    print("\n[Artifacts]")
    overall &= check("implementation report exists", REPORT.is_file())
    overall &= check("handoff packet exists", HANDOFF.is_file())
    overall &= check("validation log exists", VALIDATION.is_file())

    print("\n[Validation]")
    if VALIDATION.is_file():
        log = VALIDATION.read_text()
        overall &= check("validation log shows 24 passing tests", "24 passed" in log)
        overall &= check("validation log shows 3 test files", "3" in log and "Test Files" in log)
    else:
        overall &= check("validation log readable", False)

    print("\n[Implementation report completeness]")
    if REPORT.is_file():
        r = REPORT.read_text()
        for section in [
            "## Task",
            "## Acceptance criteria",
            "## Framework profile used",
            "## Component / route changes",
            "## Out of scope",
            "## Design checks",
            "## Accessibility",
            "## Tests added or updated",
            "## Validation",
        ]:
            overall &= check(f"report has '{section}'", section in r)
        # React profile detection cues
        for cue in [
            "react",
            "@testing-library/react",
            "vitest",
            "Vite",
            "JSX",
        ]:
            overall &= check(f"report references '{cue}'", cue in r)

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
            overall &= check(f"handoff has '{field}'", field in h)

    print("\n[A11y checks (per skill requirements)]")
    if NEW_VISIT_FORM.is_file():
        f = NEW_VISIT_FORM.read_text()
        overall &= check("UC2 uses <label htmlFor>", "htmlFor=" in f)
        overall &= check("UC2 uses aria-invalid", "aria-invalid" in f)
        overall &= check("UC2 uses aria-describedby", "aria-describedby" in f)
        overall &= check("UC2 uses role=alert", 'role="alert"' in f)
        overall &= check("UC2 uses aria-live", "aria-live" in f)
    if PET_TYPE_FILTER.is_file():
        f = PET_TYPE_FILTER.read_text()
        overall &= check("UC3 uses role=combobox", 'role="combobox"' in f)
        overall &= check("UC3 uses aria-expanded", "aria-expanded" in f)
        overall &= check("UC3 uses aria-activedescendant", "aria-activedescendant" in f)
        overall &= check("UC3 uses role=listbox", 'role="listbox"' in f)

    print()
    print(f"=== OVERALL: {'PASS' if overall else 'FAIL'} ===")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
