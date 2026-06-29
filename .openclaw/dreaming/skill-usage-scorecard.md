# Skill Usage Scorecard

Cycle: 2026-06-29 cycle-4

Same dimension set and recommendation values as cycle 1. Cycle-2 deltas marked with **(NEW)** or **(updated)**.

---

## task-state-management (carried)

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 4 | EV-002 |
| contribution_quality | 4 | EV-002 |
| overlap_risk | 2 | EV-002 |
| validation_compatibility | 4 | EV-002 |
| handoff_quality | 3 | EV-002 |
| recovery_contribution | 3 | EV-002 |
| deterministic_replacement_opportunity | 3 | EV-002 |
| minimax_usability | 4 | EV-002 |

- **Recommendation:** `revise` (unchanged from cycle 1)
- **Cycle-2 status:** unchanged. PI-002 still proposed, not applied.

---

## handoff-packet (carried)

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 4 | EV-002 |
| contribution_quality | 4 | EV-002 |
| overlap_risk | 2 | EV-002 |
| validation_compatibility | 4 | EV-002 |
| handoff_quality | 5 | EV-002 |
| recovery_contribution | 3 | EV-002 |
| deterministic_replacement_opportunity | 2 | EV-002 |
| minimax_usability | 5 | EV-002 |

- **Recommendation:** `revise` (unchanged)
- **Cycle-2 status:** unchanged.
- **Evidence below 3:** overlap_risk (2), deterministic_replacement_opportunity (2)
- **Observed impact:** see `task-state-management`. Also: handoff-packet template generation could be partially scriptable.
- **Proposed remediation:** see `task-state-management`. Also: consider a deterministic validator for handoff-packet structure.
- **Validation needed:** A test that asserts the boundary.

---

## code-review-slice-N (emergent; not yet registered — carried)

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 4 | EV-003 |
| contribution_quality | 5 | EV-003 |
| overlap_risk | 4 | EV-003 |
| validation_compatibility | 5 | EV-003 |
| handoff_quality | 4 | EV-003 |
| recovery_contribution | 5 | EV-003 |
| deterministic_replacement_opportunity | 5 | EV-003 — score 5 means "low opportunity" per workflow-nightly-dreaming.md §Stage 5 |
| minimax_usability | 4 | EV-003 |

- **Recommendation:** `revise` (register as skill)
- **Cycle-2 status:** unchanged. PI-005 still proposed, not applied.

---

## dreaming (the workflow itself — **updated**)

| Dimension | Cycle 1 | Cycle 2 | Evidence |
| --- | --- | --- | --- |
| activation_precision | 4 | 4 | EV-004, EV-009 |
| contribution_quality | 4 | 5 | EV-006 — cycle 1's 9-commit arc produced 13 artifacts and 105 tests |
| overlap_risk | 5 | 5 | EV-001 — boundary with SGP documented in `DREAMING.md` |
| validation_compatibility | 4 | 5 | EV-008 — PI-008 (Makefile target) extends validation locally; CI validation enforced |
| handoff_quality | 4 | 4 | EV-006 |
| recovery_contribution | 3 | 4 | EV-009 — cycle-2 caught its own draft mistake via local validation |
| deterministic_replacement_opportunity | 2 | 2 | EV-004 — Stage 1 still human-curated; PI-006 unfilled |
| minimax_usability | 4 | 4 | EV-006 — brief referenced by name |

- **Cycle-2 update:** contribution_quality 4 → 5; validation_compatibility 4 → 5; recovery_contribution 3 → 4.
- **Score evidence rule applied:** score 5 on `deterministic_replacement_opportunity` means "low opportunity" per `workflow-nightly-dreaming.md` §Stage 5. The 2 means "high opportunity" — and PI-008 is the first cycle's response to that opportunity, but the *full* opportunity (PI-006, run-log parser) remains open.
- **Recommendation:** `revise` after cycle 2 (still — PI-006 and PI-008's general extension PI-009 are open)
- **Evidence below 3:** deterministic_replacement_opportunity (2) — Stage 1 still human-curated; PI-006 unfilled
- **Observed impact:** Without a JSONL run log, dreaming depends on human-curated Git+memory; per-tool-call patterns are unavailable.
- **Proposed remediation:** Add a JSONL run log and a deterministic parser (PI-006). PI-008 partially closes the gap by catching CI-environment mismatches locally.
- **Validation needed:** A test that asserts Stage 1 parses a fixture log without grep / read calls.

---

## NEW Makefile-driven local validation (sibling workflow pattern)

- This is not a skill, but it deserves a scorecard slot per `workflow-nightly-dreaming.md` §Stage 5 — it is a **system-level pattern** that contributes to the workflow the same way a skill does.

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 5 | EV-008 — exactly-once-per-pre-push; no false activations |
| contribution_quality | 5 | EV-008 — caught 2 real issues on first use |
| overlap_risk | 4 | EV-008 — overlaps with dream-workflow CI; documented in Makefile |
| validation_compatibility | 5 | EV-008 — runs the same pytest suite as CI |
| handoff_quality | 5 | EV-008 — output is pass/fail with skip-vs-fail distinction |
| recovery_contribution | 5 | EV-008 — by design; the recovery is "fix locally, don't push" |
| deterministic_replacement_opportunity | 5 | EV-008 — this pattern IS the deterministic replacement for "push and wait for CI" |
| minimax_usability | 5 | EV-008 — MiniMax can run `make dreaming-validate` directly |

- **Recommendation:** `keep`
- **Affected workflow / skill:** dreaming workflow; extensible (PI-009)
- **PI-008 status:** **APPLIED in cycle 2**
