# Success Patterns

Each pattern has a single evidence reference.

---

## P-S-001 — Sub-agent code-review loop

- **Pattern ID:** P-S-001
- **Evidence reference:** EV-002 (PR #17 review cycle), EV-003 (slice 1+2, slice 3.1, slice 4.1 review cycles)
- **Affected workflow / skill:** `code-review-slice-N` sub-agent (emergent; not yet registered as a skill)
- **Observed success behavior:** Main session spawns a sub-agent with `mode=run`, `timeout=900s`. Sub-agent reviews the slice and produces a categorized finding list. Main session applies CRITICAL > HIGH > MEDIUM > LOW, re-verifies BDD/stage green, commits as `slice N.1`. Loop terminates when slice + slice.N.1 are both green.
- **Why it worked:** Different validator (sub-agent) catches a different class of bugs than BDD/unit tests. The `slice N.1` commit makes the fixes auditable.
- **How to preserve:** Document as a registered skill with explicit frontmatter, triggers ("after a feature slice ships BDD-green"), outputs (categorized finding list), and stop conditions ("BDD still green after fixes"). Standardize the spawn payload.
- **Standardization path:** routing rule + validation rule + documentation update. See PI-005.

---

## P-S-002 — BDD-first development with per-scenario fresh SQLite

- **Pattern ID:** P-S-002
- **Evidence reference:** EV-003 (slice 1 → slice 4.1)
- **Affected workflow / skill:** `BusinessOperationsDashboard` (and presumably generic)
- **Observed success behavior:** cucumber.cjs picks up `tests/support/**/*.ts` and `tests/steps/**/*.ts`; per-scenario fresh SQLite + Fastify on port 0; `tests/support/migrate.ts` runs `prisma db push --skip-generate --accept-data-loss`. Total runtime ~4:35 for 74/74 scenarios.
- **Why it worked:** Fresh DB per scenario eliminates cross-test pollution; port 0 eliminates port conflicts; Prisma `db push` is fast for SQLite. BDD scenarios double as documentation.
- **How to preserve:** Document the stack (`tsx/esm` loader, `cucumber.cjs`, fresh DB per scenario, port 0) as a reusable BDD bootstrap for any Node + Prisma project.
- **Standardization path:** documentation update + optional reusable script (`bdd-bootstrap/`).

---

## P-S-003 — Permissive-to-strict progression with locked-in permissive tests

- **Pattern ID:** P-S-003
- **Evidence reference:** EV-001 (commits `efd083d` then `a965c13`)
- **Affected workflow / skill:** SGP, generic validation discipline
- **Observed success behavior:** Before flipping mypy to strict, the permissive state was captured as a test (`test(sgp): lock in mypy permissive state`), then a progression script tracked the elimination of permissive allowances, then strict mode was flipped.
- **Why it worked:** The permissive-state test makes the change observable; the progression script makes the goal concrete; the strict flip is the smallest possible step.
- **How to preserve:** When tightening any validation gate (mypy strict, mutation budget, lint budget, coverage threshold), use this three-step pattern.
- **Standardization path:** documentation update + validation rule (require permissive-state test before strict flip).
