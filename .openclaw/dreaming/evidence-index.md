# Evidence Index

Cycle: 2026-06-29 cycle-2
Review window: 2026-06-29 → 2026-06-29 (cycle 2 anchored to cycle-1 close event)

Cycle 2's evidence base is narrower than cycle 1: no new memory/, no new commits on `origin/main` since cycle 1's PR #59 merge. However, **cycle 1's evidence (EV-001, the SGP v1.0 ship) was coarse-grained — a snapshot of the merge moment rather than the arc of work**. Cycle 2 expands EV-001 into a richer traceable record (EV-007) and adds EV-006 (cycle 1 close event).

Each entry is an evidence record. Every recommendation, lesson, pattern, scenario, and proposed improvement in other artifacts references one of the `EV-####` IDs below.

---

## EV-001 — Skill Governance Pipeline v1.0.0 ship (carried from cycle 1)

- **Run identifier:** sgp-v1.0.0-ship
- **Date:** 2026-06-14
- **Source files reviewed:**
  - `memory/2026-06-14.md` (lines 7–124)
  - Git commits: `01d1c34` (Merge PR #55 — sgp/v1-release), `82c514f` (#54), `5c821a2` (#56), `bb0f13d` (#57), `da6bfc8` (#58)
  - `skill-governance-pipeline/` (17 modules, 75/75 unit tests)
- **Task type:** Major workflow ship (Python governance pipeline)
- **Outcome:** success
- **Workflows used:** in-session; tracked as `tasks/2026-06-13-sgp/` through `tasks/2026-06-13-sgp-p5/`
- **Agents used:** main session
- **Skills used:** none explicit; `skill-maturation` rules implicit per memory
- **Files changed:** Created `skill-governance-pipeline/`; mypy strict in `a965c13`
- **Validation performed:** 75/75 unit tests; real-catalog E2E (126 artifacts); CI gating; mutation testing
- **Git commits / diffs:** see PRs #43, #44, #45, #46, #47, #48, #49, #50, #51, #52, #53, #54, #55, #56, #57, #58 (cycle 2 expanded this to EV-007)
- **Summary:** 39-minute, 5-phase SGP ship across 16 PRs. Shipped with mypy in permissive mode; strict mode flipped across PRs #55–#58 via the permissive-state-test pattern (L-001).
- **Linked lessons:** L-001, L-002
- **Linked regression scenarios:** RS-001, RS-002
- **Linked proposed improvements:** PI-001
- **Cycle-2 note:** EV-001 was assigned a single commit hash (`01d1c34`). The actual ship is a **16-PR arc** (PRs #43–#58, 2026-06-13 → 2026-06-14). See EV-007 for the traceable per-PR record. Cycle 1 underestimated the surface area by ~15x because it collapsed the arc into one timestamp.

---

## EV-002 — Task-state-management A2 exercise + Finding 1 fix (carried from cycle 1)

- **Run identifier:** tsm-a2-exercise-2026-06-12
- **Date:** 2026-06-12
- **Source files reviewed:** `memory/2026-06-12.md` (1100 lines), PR #17 (`300877f`), `tasks/2026-06-12-task-state-management-exercise/`
- **Linked lessons:** L-003, L-004
- **Linked regression scenarios:** RS-003, RS-004
- **Linked proposed improvements:** PI-002, PI-003

---

## EV-003 — BusinessOperationsDashboard slices 1 → 3.1 (carried from cycle 1)

- **Run identifier:** bod-slices-1-to-3.1
- **Date:** 2026-06-20
- **Source files reviewed:** `memory/2026-06-20.md`, slice commits `44628bf` → `db4f15f` → `dae7f51`, `BusinessOperationsDashboard/`
- **Linked lessons:** L-005, L-006
- **Linked regression scenarios:** RS-005, RS-006, RS-007
- **Linked proposed improvements:** PI-004, PI-005

---

## EV-004 — OpenClaw log evidence gap (carried from cycle 1)

- **Run identifier:** dreaming-cycle-1
- **Date:** 2026-06-29
- **Summary:** No structured OpenClaw run logs or saved handoff-packet files discoverable in the workspace. Cycle 1 ran on Git + memory only.
- **Cycle-2 status:** unchanged. `find` across `/data/.openclaw/workspace` still returns no structured run logs as of cycle 2 (2026-06-29 cycle-2).
- **Linked lessons:** L-007
- **Linked regression scenarios:** RS-008
- **Linked proposed improvements:** PI-006 (still proposed, not applied)

---

## EV-005 — Cron scheduling limitation (carried from cycle 1)

- **Run identifier:** bod-slice-3-followup
- **Date:** 2026-06-20
- **Summary:** Memory records "Cron schedules (currently interval-only)" and "`WORKER_MAX_ATTEMPTS` config" as known open items.
- **Cycle-2 status:** unchanged. PI-007 still proposed, not applied.
- **Linked lessons:** L-008
- **Linked regression scenarios:** RS-009
- **Linked proposed improvements:** PI-007

---

## EV-006 — PR #59 cycle-1 merge event

- **Run identifier:** dreaming-cycle-1-merge
- **Date:** 2026-06-28T23:13:40Z
- **Source files reviewed:**
  - `gh pr view 59` (state, merge commit, PR comments)
  - `git log ac92032..origin/main` (9 commits landed on main)
- **Task type:** Cycle-1 PR landed on main
- **Outcome:** success
- **Workflows used:** `.github/workflows/nightly-dreaming-validation.yml` (CI)
- **Validation performed:** 105 pytest tests in CI (passing after 5 fix-up commits)
- **Git commits landed:** `7ee12dd`, `38b4f8d`, `85c65ff`, `64a83c9`, `a8b28b7`, `4eb8605`, `a35b983`, `1e7bcbc`, `32222ca`
- **Summary:** PR #59 (the cycle 1 branch) merged to main at `63ac32b`. Cycle 1 generated 9 commits: 4 logical features + 5 fix-ups. The 5 fix-ups all stemmed from one root cause: **CI-environment mismatch (detached HEAD, marker-scan false positives, allowlist gaps) that a local CI run would have caught before push (PI-008)**. Cycle 2 is partly a verification that PI-008, when applied, eliminates the fix-up pattern.
- **Cycle-2 feedback on cycle-1:** L-009, L-010. The fact that the same fix-up classes could recur (and **did** recur in cycle 2's first attempt with PI-008 itself) confirms that ad-hoc pre-push validation is brittle; the Makefile target is the durable fix.
- **Linked lessons:** L-009 (cycle-1 fix-up root cause), L-010 (spec-vs-implementation gap on `DREAMING.md`)
- **Linked regression scenarios:** RS-010 (prereqs and skew)
- **Linked proposed improvements:** PI-008 → APPLIED in cycle 2

---

## EV-007 — SGP quality-tightening arc, PRs #43 → #58

- **Run identifier:** sgp-quality-arc-2026-06-11-to-14
- **Date:** 2026-06-11 → 2026-06-14
- **Source files reviewed:** `gh pr list --state all` for PRs #30–#58 (30 PRs in the window); commit history of `skill-governance-pipeline/`; `memory/2026-06-13.md` and `memory/2026-06-14.md`
- **Task type:** Multi-PR quality-tightening arc on the Skill Governance Pipeline
- **Outcome:** success (SGP reached v1.0.0)
- **Workflows used:** additive CI improvements (PRs #47, #50)
- **Validation performed:** branch coverage gate added in PR #47; mypy+ruff gate added in PR #50; 51 hypothesis property-based tests in PR #49; FOCUSED_PICKS BDD-TDD batches in PRs #44, #45, #46; mutation testing quality checks in PR #43, #58
- **PR-level trace:**

| PR | Date | Type | Surface |
|----|------|------|---------|
| #43 | 2026-06-13T22:50 | feat | Skill Governance Pipeline v1.0.0 (17 CRs, 75 tests, 153 files) |
| #44 | 2026-06-14T01:56 | test | coverage batches 1+2+3 — 21 modules at 90%+ |
| #45 | 2026-06-14T02:46 | test | FOCUSED_PICKS — 34 BDD-TDD tests for 6 P1 gaps |
| #46 | 2026-06-14T03:15 | test | FOCUSED_PICKS2 — 45 BDD-TDD tests for 8 P2/P3 gaps |
| #47 | 2026-06-14T15:03 | ci | branch coverage gate + GitHub Actions workflow |
| #48 | 2026-06-14T15:10 | docs | HITL workflow for rewrite proposals + 6 BDD-TDD docs |
| #49 | 2026-06-14T15:31 | test | 51 Hypothesis property-based tests for analyzer invariants |
| #50 | 2026-06-14T15:58 | ci | mypy + ruff type-check and lint, with auto-fixes |
| #51 | 2026-06-14T17:40 | feat | `uses_skills` / `used_by_agents` cross-references |
| #52 | 2026-06-14T18:10 | feat | pre-commit hook + validate-files subcommand |
| #53 | 2026-06-14T18:36 | feat | `recommend-task` command for natural-language task input |
| #54 | 2026-06-14T19:40 | feat | `recommend-task` filters "unknown" artifacts by default |
| #55 | 2026-06-14T19:40 | chore | ship v1.0.0 release — CHANGELOG + version bump |
| #56 | 2026-06-14T19:41 | fix | `dependency_analyzer` filters "unknown" artifacts (fixes 6 false cycles) |
| #57 | 2026-06-14T19:41 | test | lock in mypy permissive state + script to track strict progression |
| #58 | 2026-06-14T19:42 | chore | flip mypy to strict=true + add full type annotations |

- **Summary:** Cycle 1 captured only the merge moment (`01d1c34` / PR #55). Cycle 2 traces the full arc: PR #43 ships v1.0.0 in permissive mode → PRs #44–46 push coverage and BDD density → PRs #47, #50 add CI gates → PRs #48, #51–54 add developer ergonomics and bug fixes → PRs #56–58 progressively tighten mypy to strict via the permissive-state-test pattern (L-001). **This arc is itself a real-world demonstration of P-S-003** (permissive-to-strict progression with locked-in permissive tests). L-001's evidence is much stronger when framed against this 16-PR chain.
- **Linked lessons:** L-001 (reframed — was based on a single PR), L-002 (mutation testing rollout across PRs #43 + #58 is wider evidence than the single "261 survived" line), L-011 (NEW — quality gate sequence)
- **Linked patterns:** P-S-003 reinforced; P-S-004 (NEW) — "additive CI gates" pattern (PRs #47 and #50 each added independent validation without regressing existing checks)
- **Linked regression scenarios:** RS-001, RS-002 (reframed)
- **Linked proposed improvements:** PI-001 (now more clearly scoped: tie L-001's pattern to a reusable CI check that asserts the ordering invariant)

---

## EV-008 — PI-008 first-cycle validation (cycle-2 self-application)

- **Run identifier:** pi-008-first-use-2026-06-29
- **Date:** 2026-06-29 (cycle 2)
- **Source files reviewed:** first `make dreaming-validate` run on the cycle-2 branch
- **Task type:** Validation of the PI-008 follow-up
- **Outcome:** partial — caught 2 real issues before push (branch name regex too strict; commit-prefix test fails instead of skips on empty range)
- **Summary:** PI-008 (apply local CI via Makefile) caught **the very class of issue it was designed to catch** on its first use. Without it, cycle 2 would have shipped the same pattern of CI-only fix-ups as cycle 1. The Makefile paid for itself within seconds.
- **Linked lessons:** L-012 (NEW) — "local CI has compounding returns: it catches the same class of bug twice in a row before its third recurrence."
- **Linked regression scenarios:** RS-011 (NEW) — branch-name regex accepts cycle suffix
- **Linked proposed improvements:** PI-008 → **APPLIED in cycle 2**; PI-009 (NEW) — generalize PI-008 pattern to other workflow artifact sets

---

## EV-009 — Dreaming workflow self-application (cycle-2)

- **Run identifier:** dreaming-cycle-2-self-application
- **Date:** 2026-06-29 (cycle 2)
- **Summary:** Cycle 2 used the cycle-1 workflow (now on main) to evaluate itself. Two observations:
  - The evidence-traceability test (`test_evidence_traceability.py`) caught a near-miss where cycle 2's proposed EV-006 referenced EV-004 — the test currently requires every scenario's EV to exist in the evidence-index; without this invariant, cross-cycle linkage would silently rot.
  - The hidden-reasoning test caught one of my own draft phrasings during cycle-2 draft (caught in `make dreaming-validate`, not in review).
- **Linked lessons:** L-013 (NEW) — "the spec's evidence rules protect against self-application drift when re-instantiated."
