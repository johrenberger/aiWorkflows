# Success Patterns

P-S-001 through P-S-003 are carried from cycle 1; P-S-004 is new in cycle 2.

---

## P-S-001 — Sub-agent code-review loop (carried)

- **Pattern ID:** P-S-001
- **Evidence reference:** EV-002, EV-003
- **Standardization path:** routing rule + validation rule + documentation update. See PI-005.

## P-S-002 — BDD-first development with per-scenario fresh SQLite (carried)

- **Pattern ID:** P-S-002
- **Evidence reference:** EV-003
- **Standardization path:** documentation update + optional reusable script (`bdd-bootstrap/`).

## P-S-003 — Permissive-to-strict progression with locked-in permissive tests (carried + reinforced)

- **Pattern ID:** P-S-003
- **Evidence reference:** EV-001, EV-007 (cycle 2)
- **Cycle-2 update:** The cycle-1 single-event evidence for this pattern (the mypy strict flip in PR #58) was correct but underspecified. EV-007 traces the 16-PR SGP quality-tightening arc and shows the pattern applied **across multiple gates**: mypy, ruff, branch coverage, hypothesis testing. The pattern is canonical; a candidate promotion to a generic validation-discipline skill is now well-evidenced.
- **Standardization path:** documentation update + validation rule. Cycle-1's PI-001 is now better-scoped; renamed intent: "tie L-001's pattern to a reusable CI check that asserts the ordering invariant (permissive test → progression script → strict flip)."

---

## P-S-004 — Additive CI gates without regression (NEW)

- **Pattern ID:** P-S-004
- **Evidence reference:** EV-007 (PRs #47, #50)
- **Affected workflow / skill:** SGP CI; extensible to any project
- **Observed success behavior:** PR #47 (2026-06-14T15:03) adds a branch coverage gate + GitHub Actions workflow. PR #50 (2026-06-14T15:58) adds mypy + ruff type-check and lint. Each addition is **independent of the others** — the existing test suite keeps passing, the new gate passes on its own merit, and no existing CI step is rewritten. By the time of the v1.0.0 release (PR #55, 2026-06-14T19:40), the CI workflow has 3 distinct gates each guarding a different dimension.
- **Why it worked:** Each gate was added as a **separate commit on a separate PR**, so bisecting a CI failure points at the gate that introduced it. The gates are also ordered: low-cost first (branch coverage) → moderate-cost (mypy+ruff) → expensive (Hypothesis property tests in PR #49). The ordering matters — fast feedback gates come first.
- **How to preserve:** When adding a CI gate to an existing project, ship it as a *new commit on a new PR* (not a rewrite of an existing step). Order new gates by feedback cost (cheap first). Document each gate's purpose in `docs/ci-gates.md`.
- **Standardization path:** documentation update + reusable `.github/workflows/ci-gates.yml` template that other projects can copy.
