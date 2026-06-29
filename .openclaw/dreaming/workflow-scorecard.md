# Workflow Scorecard

Cycle: 2026-06-29 cycle-3

Same 1–5 dimensions as cycle 1. Cycle-2 deltas marked with **(updated)** or **(NEW)**.

---

## Skill Governance Pipeline (SGP) (carried)

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 5 | EV-001 |
| contribution_quality | 5 | EV-001 |
| overlap_risk | 5 | EV-001 |
| validation_compatibility | 5 | EV-001 |
| handoff_quality | 4 | EV-001 |
| recovery_contribution | 4 | EV-001 |
| deterministic_replacement_opportunity | 1 | EV-001 |
| minimax_usability | 5 | EV-001 |

- **Cycle-2 update:** EV-007's 16-PR trace reframes this from "the SGP ship" to "the SGP quality-tightening arc." The scores stand; the evidence behind them is much stronger now. P-S-003 (permissive-to-strict progression) is now demonstrably canonical, not anomalous. P-S-004 (additive CI gates) is newly surfaced from EV-007.
- **Recommendation:** `keep` (unchanged)

---

## A2 validation exercise (task-state-management) — carried

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 4 | EV-002 |
| contribution_quality | 4 | EV-002 |
| overlap_risk | 4 | EV-002 |
| validation_compatibility | 4 | EV-002 |
| handoff_quality | 4 | EV-002 |
| recovery_contribution | 4 | EV-002 |
| deterministic_replacement_opportunity | 3 | EV-002 |
| minimax_usability | 4 | EV-002 |

- **Recommendation:** `keep`
- **Cycle-2 status:** unchanged.

---

## BDD-driven slice workflow (BusinessOperationsDashboard) — carried

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 5 | EV-003 |
| contribution_quality | 5 | EV-003 |
| overlap_risk | 5 | EV-003 |
| validation_compatibility | 5 | EV-003 |
| handoff_quality | 4 | EV-003 |
| recovery_contribution | 4 | EV-003 |
| deterministic_replacement_opportunity | 2 | EV-003 |
| minimax_usability | 4 | EV-003 |

- **Recommendation:** `add_guardrail` (unchanged from cycle 1)
- **Cycle-2 status:** PI-004 still proposed, not applied.
- **Evidence below 3:** deterministic_replacement_opportunity (2) — the sub-agent review step is currently optional; without it, concurrency bugs slip through.
- **Observed impact:** Without a clear ship gate, slices ship with reviewer-only findings.
- **Proposed remediation:** Add a routing rule: "Slice N is not shippable until sub-agent review returns zero CRITICAL or HIGH findings." See PI-004.
- **Validation needed:** Apply to the next 3 slices and compare findings to historical `slice N.1` commits.

---

## Dreaming workflow (this workflow) (updated)

| Dimension | Cycle 1 | Cycle 2 | Evidence |
| --- | --- | --- | --- |
| activation_precision | 4 | 4 | EV-004, EV-009 |
| contribution_quality | 4 | 5 | EV-006 — 13 artifacts + 105 tests + a defined spec boundary |
| overlap_risk | 5 | 5 | EV-001 |
| validation_compatibility | 4 | 5 | EV-008 — local + CI validation both green in cycle 2 |
| handoff_quality | 4 | 4 | EV-006, EV-009 |
| recovery_contribution | 3 | 4 | EV-009 |
| deterministic_replacement_opportunity | 2 | 2 | EV-004 — PI-006 unfilled |
| minimax_usability | 4 | 4 | EV-006 |

- **Cycle-2 update:** contribution_quality 4 → 5; validation_compatibility 4 → 5; recovery_contribution 3 → 4.
- **Recommendation:** `revise` (unchanged in recommendation; scores improved)
- **Evidence below 3:** deterministic_replacement_opportunity (2) — Stage 1 evidence collection could be partially scripted.
- **Observed impact:** Without a JSONL run log, dreaming depends on human-curated Git+memory; per-tool-call patterns are unavailable.
- **Proposed remediation:** see PI-006.
- **Validation needed:** see `skill-usage-scorecard.md` "dreaming" entry.

---

## Local pre-push validation via Makefile (sibling workflow pattern)

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 5 | EV-008 |
| contribution_quality | 5 | EV-008 |
| overlap_risk | 4 | EV-008 |
| validation_compatibility | 5 | EV-008 |
| handoff_quality | 5 | EV-008 |
| recovery_contribution | 5 | EV-008 |
| deterministic_replacement_opportunity | 5 | EV-008 — this pattern IS the deterministic replacement for "push and wait for CI" |
| minimax_usability | 5 | EV-008 |

- **Recommendation:** `keep`
- **Evidence:** EV-008
- **Cycle-2 action:** PI-008 applied. This pattern is ready to generalize (PI-009, review-required).
