# Failure Patterns

Each pattern has a single evidence reference. Severity comes from observed impact in the review window; recurrence classification follows `workflow-nightly-dreaming.md` §Stage 4.

P-F-001 through P-F-004 are carried from cycle 1; P-F-005 is new in cycle 2.

---

## P-F-001 — Concurrency race conditions not caught by BDD (carried)

- **Pattern ID:** P-F-001
- **Evidence reference:** EV-003
- **Recurrence:** one_off (this cycle), but matches a known class; candidate_regression
- **Impact:** CRITICAL — silent data integrity corruption
- **Prevention strategy:** Sub-agent code review on finalize/finalizeFailure paths before declaring a slice done; at least one concurrency BDD scenario per finalize path.
- **Regression scenario link:** RS-005

---

## P-F-002 — Undocumented state-machine transitions in skill specs (carried)

- **Pattern ID:** P-F-002
- **Evidence reference:** EV-002
- **Recurrence:** one_off; generic; candidate_regression
- **Impact:** warning — feature works after fix
- **Prevention strategy:** SKILL.md must include a complete transition table.
- **Regression scenario link:** RS-003

---

## P-F-003 — DOTALL regex matching across section boundaries (carried)

- **Pattern ID:** P-F-003
- **Evidence reference:** EV-002
- **Recurrence:** one_off; candidate_regression
- **Impact:** warning
- **Prevention strategy:** Prefer line-by-line scanners over `re.DOTALL`.
- **Regression scenario link:** RS-004

---

## P-F-004 — Multi-tenant info leak in `/health` endpoint (carried)

- **Pattern ID:** P-F-004
- **Evidence reference:** EV-003
- **Recurrence:** one_off; systemic pattern; candidate_regression
- **Impact:** HIGH — info disclosure
- **Prevention strategy:** Strict `/health` and `/ready` contracts.
- **Regression scenario link:** RS-006

---

## P-F-005 — CI-environment mismatch causing false-positive test failures (NEW)

- **Pattern ID:** P-F-005
- **Evidence reference:** EV-006, EV-008
- **Affected workflow / skill:** dreaming workflow (cycle 1, cycle 2); extensible to any workflow with CI validation
- **Observed failure:** Three classes of false-positive that ship locally but fail in CI:
  1. Tests that hardcode `main` in `git merge-base` calls fail when CI checkout is detached HEAD with no local `main` ref
  2. Marker-scan greps (e.g., for hidden-reasoning) match docs that legitimately describe the rule they enforce
  3. "Ensure X is not configured" greps match docs that legitimately say "do not configure X"
- **Recurrence:** repeated (cycle 1: 5 fix-up commits; cycle 2 before PI-008: 2 fix-up commits caught locally)
- **Impact:** medium — wastes CI cycles; pollutes PR history with fix-ups; reviews look messier
- **Prevention strategy:** Mirror CI validation as a local Makefile target (PI-008). Run that target before push. Tests and greps designed to anticipate environment variants: detached HEAD, allowlist of rule-documenting files, tighter regexes for forbidden-config verbs (vs. forbidding any mention).
- **Regression scenario link:** RS-010, RS-011, RS-012
