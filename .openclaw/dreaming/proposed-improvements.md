# Proposed Improvements

Cycle: 2026-06-29 cycle-4

PI-001 through PI-007 are carried from cycle 1 (some with updates); PI-008 is now **APPLIED**; PI-009 and PI-010 are NEW.

Safety classifications: `auto_safe | review_required | blocked`

Status values: `proposed | applied | deferred | rejected`

---

## PI-001 — Add "permissive-state" pre-check to SGP CI (carried, scope reframed)

- **Improvement ID:** PI-001
- **Evidence reference:** EV-001, EV-007, L-001 (reframed)
- **Cycle-2 update:** EV-007 shows L-001's pattern applied **multiple times** across the SGP arc. The PI's scope is now "assert that any permissive-state-test is preceded by, or co-committed with, a strict-flip commit" — a sharper invariant.
- **Safety classification:** auto_safe
- **Status:** proposed (unchanged)

---

## PI-002 — Add state-machine transition-table requirement to validator (carried)

- **Evidence reference:** EV-002, L-003
- **Status:** proposed (unchanged)
- **Safety classification:** review_required (unchanged)

---

## PI-003 — Add `re.DOTALL` denylist to skill validator CI (carried)

- **Evidence reference:** EV-002, L-004
- **Status:** proposed (unchanged)
- **Safety classification:** auto_safe (unchanged)

---

## PI-004 — Require sub-agent code review before slice ship (carried)

- **Evidence reference:** EV-003, L-005
- **Status:** proposed (unchanged)
- **Safety classification:** review_required (unchanged)

---

## PI-005 — Promote `code-review-slice-N` sub-agent pattern to a registered skill (carried)

- **Evidence reference:** EV-003, P-S-001
- **Status:** proposed (unchanged)
- **Safety classification:** review_required (unchanged)

---

## PI-006 — Add structured OpenClaw run log (carried; **still unfilled in cycle 2**)

- **Improvement ID:** PI-006
- **Evidence reference:** EV-004, L-007, P-IP-001
- **Cycle-2 status:** unchanged. No JSONL run log was added between cycles. `find` still returns nothing. This remains the single largest unfilled deterministic opportunity.
- **Status:** proposed (carried; explicitly not applied)
- **Safety classification:** review_required (unchanged)
- **Validation required:** feed fixture log to parser; assert parsed evidence matches expectations.

---

## PI-007 — Add regression test for cron tick path (carried)

- **Evidence reference:** EV-005, L-008, RS-009
- **Status:** proposed (unchanged)
- **Safety classification:** auto_safe (unchanged)

---

## PI-008 — Run local validation via Makefile target before push (APPLIED in cycle 2)

- **Improvement ID:** PI-008
- **Evidence reference:** EV-006 (cycle-1 fix-up root cause), EV-008 (first-use validation)
- **Applied in cycle 2:** Yes — `Makefile` added at repo root with `dreaming-validate`, `dreaming-pr-ready`, `dreaming-clean`, `dreaming-help`, and `dreaming-resolve-base` targets. First use caught 2 real issues (L-010, L-013) before push.
- **Status:** **APPLIED** (was proposed in cycle 1)
- **Safety classification:** auto_safe (applied; classification was correct)
- **Validation performed:** `make dreaming-validate` returns 104 passed, 1 skipped on the cycle-2 branch ahead of any commits.
- **Rollback notes:** `git revert` the Makefile commit if developer ergonomics prove worse than the saved fix-up cycles.

---

## PI-009 — Generalize PI-008 to other workflow artifact sets (NEW)

- **Improvement ID:** PI-009
- **Evidence reference:** EV-008, L-009
- **Observed problem:** PI-008 solved dreaming's local-validation gap. SGP, BusinessOperationsDashboard, and any other workflow with a CI workflow file are likely to have the same gap, but no equivalent local target exists for them.
- **Affected workflow / skill / artifact:** all workflows with `.github/workflows/*.yml` files
- **Recommended change:** For each existing CI workflow, create a sibling `make <name>-validate` target. Existing precedent: `make dreaming-validate` (PI-008).
- **Expected benefit:** Prevent the cycle-1 fix-up pattern (5 fix-up commits after push) from recurring in other workflows.
- **Risk level:** low
- **Safety classification:** review_required (touches developer workflow conventions)
- **Validation required:** Apply to SGP first; verify `make sgp-validate` catches a known CI-only failure locally before promoting the convention.
- **Status:** proposed

---

## PI-010 — Treat each EV entry as a candidate for arc expansion (NEW, informational)

- **Improvement ID:** PI-010
- **Evidence reference:** EV-007 (the SGP arc-expansion), nightly-summary.md's "Cycle-2 self-meta observation"
- **Observed problem:** Cycle 1's EV-001 was a single timestamp that understated the SGP work by ~15x (16 PRs collapsed into one moment). This is a class of error: **single-event evidence naturally hides arc-scale patterns**.
- **Recommended change:** When writing a new EV-### entry, ask: "Is this a single event or the visible tip of an arc?" If the latter, expand to the arc before publishing.
- **Safety classification:** informational (process guidance, not code)
- **Validation required:** Spot-audit existing EV entries; expand those that prove to be arc-tips on first review.
- **Status:** proposed (informational)

---

## Summary of cycle-2 PI status

| PI | Class | Status |
| --- | --- | --- |
| PI-001 | auto_safe | proposed (reframed) |
| PI-002 | review_required | proposed |
| PI-003 | auto_safe | proposed |
| PI-004 | review_required | proposed |
| PI-005 | review_required | proposed |
| PI-006 | review_required | proposed (carried; still the largest unfilled gap) |
| PI-007 | auto_safe | proposed |
| **PI-008** | **auto_safe** | **APPLIED** ✅ |
| PI-009 | review_required | proposed (NEW) |
| PI-010 | informational | proposed (NEW) |

No blocked-class changes proposed in cycle 2.

---

## PI-011 — Add `on: pull_request:` filter to surface PR-only failures cleanly (NEW, cycle 3)

- **Improvement ID:** PI-011
- **Evidence reference:** EV-010, L-014
- **Observed problem:** Even after removing `main` from the `push:` trigger, a developer can `git push origin main` directly. The dreaming test suite would still fail. The current `tests/` skip-when-precondition-not-held logic is necessary but not sufficient — the workflow trigger itself must reflect the test's domain.
- **Recommended change:** Document (in `workflow-nightly-dreaming.md`) the CI trigger model: "this suite is a PR-readiness suite; PR events are the primary trigger; `push:` is allowed only for early-warning on the feature branch before the PR opens."
- **Expected benefit:** Future cycle maintainers don't repeat the cycle-3 trigger-bundling bug.
- **Safety classification:** auto_safe (documentation-only)
- **Validation required:** N/A (doc-only); apply in cycle 4 or later.
- **Status:** proposed

---

## Summary of cycle-3 PI status

| PI | Class | Status |
| --- | --- | --- |
| PI-001 | auto_safe | proposed (reframed) |
| PI-002 | review_required | proposed |
| PI-003 | auto_safe | proposed |
| PI-004 | review_required | proposed |
| PI-005 | review_required | proposed |
| PI-006 | review_required | proposed (carried; still the largest unfilled gap) |
| PI-007 | auto_safe | proposed |
| PI-008 | auto_safe | APPLIED (cycle 2) |
| PI-009 | review_required | proposed (cycle 2) |
| PI-010 | informational | proposed (cycle 2) |
| PI-011 | auto_safe | APPLIED (cycle 4) |
| PI-012 | auto_safe | APPLIED (cycle 4, NEW) |

No blocked-class changes proposed in cycle 3 or cycle 4.
