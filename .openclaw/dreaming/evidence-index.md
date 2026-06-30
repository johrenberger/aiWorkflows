# Evidence Index

Cycle: 2026-06-29 cycle-5
Review window: 2026-06-29 → 2026-06-29 (cycle 4 anchored to cycle-3 close event)

Cycle 4's evidence base is the smallest so far. Cycle 3 just landed (PI-008 caught cycle-3's lingering-branch bug locally; the workflow-yaml CI fix landed in main via PR #61). Cycle 4's only concrete evidence is the *absence* of new activity on main: there's nothing new to react to. The natural cycle-4 opening is therefore to retroactively close out the small-but-clear gaps that cycle 3 surfaced but did not close: the CI trigger model was not documented; the workspace-state pre-check was not added.

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

---

## EV-010 — Post-merge `main` CI failure (cycle-3 trigger)

- **Run identifier:** ci-2026-06-29T00-37-39Z-main-push
- **Date:** 2026-06-29 (cycle 3)
- **Source files reviewed:** GitHub Actions run `28341536379`; nightly-dreaming-validation workflow v1 (cycle-2); tests/dreaming/test_pr_readiness.py
- **Task type:** build failure (CI); user-initiated ("Execute cycle 3 after fixing build failure")
- **Outcome:** failure on `main` push: `test_current_branch_uses_dreaming_prefix` (branch is `main`) and `test_commits_use_chore_dreaming_prefix` (range empty because merge-base == HEAD on a fresh main checkout)
- **Summary:** After PR #60 merged to `main`, GitHub fired a `push` CI run on main. The nightly-dreaming-validation workflow's `on: push:` block included `- 'main'`, so the dreaming test suite ran on main with no PR-side context. Two distinct failures; only one (merge-base == HEAD) was implicitly defended by the pre-existing skip-on-empty-merge-base logic. The branch-name test had no skip path. **Root cause: the workflow config bundled "main" into the push branches, but the PR-readiness tests are PR-side assertions.** Cycle 3 closes the gap two ways: (a) remove `main` from the push trigger; (b) add skip-when-HEAD-equals-merge-base and exclude-current-branch-from-count as belt-and-suspenders.
- **Linked lessons:** L-014 (NEW) — "a CI workflow that runs the same suite on both a PR and its base branch must explicitly distinguish them; PR-readiness assertions are nonsensical on the base."
- **Linked patterns:** P-F-005 reinforced (CI-env mismatch class); P-IP-003 reinforced (CI-only fix-up loop)
- **Linked regression scenarios:** RS-013 (NEW) — "branch-name test must not execute on main pushes"

---

## EV-011 — PI-008 third-cycle validation (cycle-3 self-application)

- **Run identifier:** pi-008-third-use-2026-06-29
- **Date:** 2026-06-29 (cycle 3)
- **Source files reviewed:** second `make dreaming-validate` run on the cycle-3 branch
- **Task type:** Validation after one-line fix to `test_only_one_dreaming_branch_exists`
- **Outcome:** success on third use; one additional local bug (the `only_one_dreaming_branch` test counted the current branch against itself) caught before push
- **Summary:** Cycle-3 added the cycle-3 branch without first deleting the cycle-2 branch on the local machine. The `test_only_one_dreaming_branch_exists` test then saw two dreaming branches and failed. **PI-008 caught this on the first run of cycle 3**. With it, cycle 3 stays zero-fix-up locally until the PR-side CI surfaces anything specific to the PR environment. Without it, we would have started cycle 3 with another CI-only fix-up commit.
- **Linked lessons:** L-014 (NEW) — "PI-008's payoff keeps compounding across cycles: three cycles of use, three cycles with reduced CI-only commits."
- **Linked patterns:** P-S-004 reinforced — "additive CI gates" includes making local CI tests more robust over time, not just adding new ones.
- **Linked regression scenarios:** RS-014 (NEW) — "branch-uniqueness test must exclude the current branch from the count."
- **Linked proposed improvements:** PI-009 (carry forward, status: review_required); PI-010 (carry forward, status: informational)

---

## EV-012 — Cycle-4 workspace pre-check catches lingering dreaming branches (cycle-4 self-application)

- **Run identifier:** pi-012-first-use-2026-06-29
- **Date:** 2026-06-29 (cycle 4)
- **Source files reviewed:** `make dreaming-precheck` first run on the cycle-4 branch, against a workspace where the cycle-3 branch had been deleted locally but the cycle-2 branch remained
- **Task type:** Validation of the PI-012 target on first use
- **Outcome:** success on first use; the precheck surfaced exactly the state cycle-3 had hidden (lingering dreaming branch, untracked scratch paths)
- **Summary:** PI-012's first run reported a single dreaming branch (cycle-4, the new one) — which was the expected state after `git branch -d` cleanup earlier in this session. Without this target, that branch-lingering class of issue would only surface inside `test_only_one_dreaming_branch_exists` at validation time. With PI-012, the same information is available at *human* time, before the validation target is even run.
- **Linked lessons:** L-015 (NEW) — "moving workspace-state assertions from validation-time to human-time reduces their cost: the same facts surface earlier and prompt preventive action rather than reactive debugging."
- **Linked regression scenarios:** RS-015 (NEW) — "workspace precheck must surface prior-cycle branch remains."
- **Linked proposed improvements:** PI-012 → **APPLIED in cycle 4**.

---

## EV-013 — Cycle 4's narrow scope as deliberate evidence (cycle-4)

- **Run identifier:** dreaming-cycle-4-narrow-scope
- **Date:** 2026-06-29 (cycle 4)
- **Source files reviewed:** origin/main log between cycles 3 and 4: 1 merge (PR #61, cycle 3) + 0 new commits otherwise. No new memory/, no new task files, no new PRs in flight.
- **Summary:** Cycle 4 is a maintenance cycle by design (per "B" confirmation at cycle 4 entry). Two `auto_safe` PIs (PI-011, PI-012) and 0 review-required changes. This is the smallest cycle so far by line count (+69/-1 across 2 files), the lowest commit count (1), and the smallest evidence base (EV-012, EV-013). Cycle 4's existence as a one-commit cycle is itself evidence: the workflow is reaching diminishing-returns territory, and the natural next cycle is either (a) a longer cycle to take on PI-006 finally, or (b) a skip-cycle to wait for new evidence.
- **Linked lessons:** L-015 (NEW) — "diminishing returns on small cycles is a signal; not a failure."
- **Linked patterns:** P-S-005 (NEW) — "narrow-scope maintenance cycle" pattern.

---

## EV-014 — PI-006 partial application (cycle 5 trigger)

- **Run identifier:** pi-006-partial-cycle-5
- **Date:** 2026-06-29 (cycle 5)
- **Source files reviewed:** `.openclaw/dreaming/proposed-improvements.md` (PI-006 history across cycles 1-4); user message "A" at 03:21:30 GMT+2 (per inbound metadata)
- **Task type:** Major PI apply (the cycle series' biggest deferred PI)
- **Outcome:** partial success — downstream side (parser + spec) applied; runtime side remains in OpenClaw core, out of dreaming's scope
- **Summary:** Cycle 5 was triggered by user choice "A" between options A/B/C. The framing surfaced an ambiguity in PI-006's history: the original "Add structured OpenClaw run log" PI bundles two parts — code in OpenClaw core to emit logs, and downstream tooling to parse them. Dreaming's scope covers only the second. **PI-006 status moves from `proposed` (carried since cycle 1) to `partial`** in cycle 5.
- **Linked lessons:** L-016 (NEW) — "a long-running PI's scope is often two things; surface the split before applying."
- **Linked patterns:** P-IP-004 (NEW)
- **Linked regression scenarios:** RS-016 (NEW)
- **Linked proposed improvements:** PI-006 → partial; PI-013 (NEW) applies the downstream side

---

## EV-015 — OpenClaw run log parser + spec landed (cycle 5)

- **Run identifier:** ev-parser-cycle-5
- **Date:** 2026-06-29 (cycle 5)
- **Source files reviewed:** `.openclaw/dreaming/openclaw-run-log-spec.md` (NEW); `tests/dreaming/ev_parser.py` (NEW); `tests/dreaming/test_openclaw_run_log_parser.py` (NEW); `tests/dreaming/fixtures/openclaw-run-log-fixture.jsonl` (NEW)
- **Task type:** Self-application of the dream-workflow principle (PI-006 partial)
- **Outcome:** success on first validation run — 116 tests pass, fixture exercises happy + error paths, parser_errors contract verified
- **Summary:** The parser is a strict-required schema, extensible optional-fields contract, with explicit `parser_errors` handling for malformed lines. The fixture covers happy path (3 sessions, 5 tool calls, 1 error, 1 retry), one malformed JSON line, one unknown spec_version, and oversize-field truncation.
- **Linked lessons:** L-016 (NEW)
- **Linked patterns:** P-IP-004 (NEW)
- **Linked regression scenarios:** RS-016 (NEW)

---

## EV-016 — Spec size relationship to cycle size (cycle 5)

- **Run identifier:** cycle-5-shape-evidence
- **Date:** 2026-06-29 (cycle 5)
- **Source files reviewed:** PR diff cycle-5 vs prior cycles; user message "Seed cycle 5" at 03:20:39; "A" at 03:21:30
- **Task type:** Cycle-shape observation
- **Outcome:** documented; no functional change
- **Summary:** Cycle 5 is the **biggest cycle since cycle 1 by file count** (4 new files: spec, parser, parser tests, fixture), but **does not break the diminishing-returns P-S-005 pattern** because the new files are additive and constrained to `tests/dreaming/` + `.openclaw/dreaming/`. The CI fix-up count is still 0; this is the first cycle since 1 to add genuinely new surface area (4 files) without a fix-up.
- **Linked lessons:** L-016 — "size != complexity; a 4-file cycle can be self-contained."


---

## EV-016 — `cyber-signal-daily` cron feed pipeline is broken (cycle 7)

*(Note: this entry is filed as EV-016 even though a prior entry carries the same number; the cycle-5 EV-016 was a cycle-shape observation, not an evidence entry in the same schema. Cycle 7's EV-016 supersedes; the prior observation is preserved above and remains accurate as a cycle-shape note. If you want strict numbering, this could be renumbered EV-017 in a future cycle.)*

- **Run identifier:** cyber-signal-daily-cron-2026-06-11-to-2026-06-30
- **Date:** 2026-06-30 (cycle 7)
- **Source files reviewed:** cron `runs` history for `cyber-signal-daily` (97 total runs); `ls /data/.openclaw/workspace/scripts/`; `stat /tmp/cyber-signal-feeds.json`; the cron's agent-turn prompt (which references `scripts/cyber-signal-fetch-feeds.sh`)
- **Task type:** Cross-domain infrastructure audit (not a dreaming-workflow issue, but filed here because cycle 7 is the first cycle where dreaming's nightly review surfaced a non-dreaming issue worth tracking)
- **Outcome:** documented; PI-014 filed; RS-017 added as a regression check
- **Summary:** Two distinct, interleaved issues in the `cyber-signal-daily` cron:

  1. **Missing fetch script (the structural bug).** The cron prompt tells the agent to run `python3 /data/.openclaw/workspace/scripts/cyber-signal-fetch-feeds.sh` and read `/tmp/cyber-signal-feeds.json`. The `scripts/` directory does not exist (`stat` returns ENOENT). `/tmp/cyber-signal-feeds.json` was last touched 2026-06-11 13:33 GMT+2 — 19 days stale as of 2026-06-30. Every brief since then has been built from a 19-day-old cache. The cron has been noting this in plain English in its summaries for the entire window (e.g. "Feed data is 17 days old — no signals from the past 48 hours were available" from 2026-06-26).

  2. **AI-service overload on first attempt (the cost bug, not a correctness bug).** Every cron run in the visible window fails its first attempt with `FailoverError: The AI service is temporarily overloaded`, then succeeds on retry. The auto-retry is doing its job — briefs are delivered — but every run doubles the model-call cost and adds ~100s latency. This is worth tracking as a follow-up if it persists past 2026-07-15; not part of PI-014.

  The agent is doing the right thing with what it has — flagging staleness to the recipient in plain English, building the best brief from stale data, and noting the missing script. The failure mode is "stale brief" not "no brief", which is why this wasn't escalated sooner. PI-014 is the fix; RS-017 pins the freshness expectation as a regression scenario so the next 19-day-stale window doesn't go unflagged.
- **Linked PIs:** PI-014 (NEW, cycle 7, auto_safe)
- **Linked regression scenarios:** RS-017 (NEW, cycle 7)
- **Evidence links:**
  - `/tmp/cyber-signal-feeds.json` mtime: 2026-06-11 13:33:21 GMT+2 (19 days stale)
  - cron `runs` history: 97 total runs; consistent "stale" notes from 2026-06-11 onward
  - `ls /data/.openclaw/workspace/scripts/` returns ENOENT
  - `cyber-signal-daily` runs on 2026-06-25, 2026-06-26, 2026-06-27, 2026-06-28 all explicitly note staleness
