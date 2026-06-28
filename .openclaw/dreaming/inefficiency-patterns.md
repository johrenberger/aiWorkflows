# Inefficiency Patterns

P-IP-001 through P-IP-002 are carried from cycle 1; P-IP-003 is new in cycle 2.

---

## P-IP-001 — Dreaming Stage 1 ran without structured run logs (carried; **unchanged in cycle 2**)

- **Pattern ID:** P-IP-001
- **Evidence reference:** EV-004
- **Cycle-2 status:** unchanged. `find` across the workspace still returns no structured run logs. PI-006 still proposed.
- **Recommended improvement:** Add a JSONL run log (PI-006). Until then, dreaming's per-tool-call retry/timeout/blocked-state findings are unavailable.
- **Deterministic tooling opportunity:** yes — JSONL with fixed schema; parser in deterministic Stage 1.
- **Regression scenario link:** RS-008

---

## P-IP-002 — Slice N ships before sub-agent review, requiring slice N.1 (carried)

- **Pattern ID:** P-IP-002
- **Evidence reference:** EV-003
- **Cycle-2 status:** unchanged. PI-004 still proposed; PI-005 still proposed.
- **Recommended improvement:** Standardize spawn-reviewer step as part of slice workflow (PI-005, review-required).
- **Regression scenario link:** RS-005, RS-007

---

## P-IP-003 — CI-only fix-up loop on workflows that lack local validation (NEW)

- **Pattern ID:** P-IP-003
- **Evidence reference:** EV-006, EV-008
- **Affected workflow / skill:** dreaming workflow (in cycle 1); extensible to any workflow whose CI is the only place its tests run
- **Observed inefficiency:** Cycle 1 generated 5 fix-up commits (out of 9 total) because CI-only validation does not run before push. Each fix-up is a re-push → wait for CI → fix → re-push cycle. Wasted ~30 minutes per fix-up in cycle 1.
- **Was the output still successful:** Yes — cycle 1 landed. But the cost was real.
- **Cause:** No local equivalent of the CI validation. The CI workflow has the tests but the developer has no ergonomic way to run them locally before pushing.
- **Recommended improvement:** Add a Makefile target mirroring the CI workflow's tests (PI-008 applied; PI-009 NEW extends the pattern to other workflows).
- **Deterministic tooling opportunity:** not directly applicable; the improvement is a developer-tool one.
- **Regression scenario link:** RS-010 (Makefile prereq degradation), and indirectly RS-011, RS-012 (the Makefile's first use caught both).
