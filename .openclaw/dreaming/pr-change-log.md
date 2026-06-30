# PR Change Log

Cycle: 2026-06-29 cycle-5
Branch: `dreaming/nightly-execution-quality-2026-06-29-cycle-2`
Base: `main` (`63ac32b`, the PR #59 merge commit)

This log maps every change on the branch to evidence and to safety classification.

---

## Commit: `chore(dreaming): add PI-008 local validation via Makefile (cycle-2 follow-up)`

- **Change IDs:** C2-001
- **Files changed:**
  - `Makefile` (new) — `make dreaming-validate`, `make dreaming-pr-ready`, `make dreaming-clean`, `make dreaming-help`, `make dreaming-resolve-base`
- **Change type:** auto_safe (developer tooling; no runtime behavior change)
- **Evidence reference:** EV-006, L-009, EV-008
- **Reason for change:** PI-008 retroactively identified as the dominant root cause of cycle-1's 5 fix-up commits. Apply PI-008 in cycle 2 to verify it works.
- **Expected impact:** Subsequent cycles catch CI-environment mismatches locally before push. Estimated cycle-1 saving: 30 minutes × 5 fix-ups = 2.5 hours per cycle.
- **Validation performed:** `make dreaming-validate` ran green on cycle-2 branch ahead of any commits; first use caught 2 real issues (L-010, L-013) that would otherwise have been CI fix-ups.
- **Rollback notes:** `git revert` the commit if developer ergonomics prove worse than saved fix-up cycles.
- **Status:** applied

---

## Commit: `chore(dreaming): relax PR-readiness branch regex and skip-on-empty`

- **Change IDs:** C2-002
- **Files changed:**
  - `tests/dreaming/test_pr_readiness.py` — branch regex accepts `YYYY-MM-DD` or `YYYY-MM-DD-suffix`; commit-prefix test skips on empty range
- **Change type:** auto_safe (test refinement; no production behavior change)
- **Evidence reference:** EV-008, L-010, L-013
- **Reason for change:** Cycle-2 branch name `dreaming/nightly-execution-quality-2026-06-29-cycle-2` broke cycle-1's strict `YYYY-MM-DD` regex; commit-prefix test failed (rather than skipped) on freshly-checked-out branches. Caught by `make dreaming-validate` in PI-008's first use.
- **Expected impact:** Future cycles with `-N` cycle suffixes work without re-fixing the test. Empty-range case (the *expected* state of a pre-first-commit branch) skips gracefully.
- **Validation performed:** `make dreaming-validate` returns 104 passed, 1 skipped on a freshly-checked-out cycle-2 branch.
- **Rollback notes:** `git revert` the commit.
- **Status:** applied

---

## Commit: `chore(dreaming): populate cycle-2 nightly artifacts`

- **Change IDs:** C2-010..C2-020
- **Files changed:**
  - `.openclaw/dreaming/evidence-index.md` (replaced) — adds EV-006, EV-007, EV-008, EV-009
  - `.openclaw/dreaming/nightly-summary.md` (replaced)
  - `.openclaw/dreaming/lessons-learned.md` (replaced) — adds L-009 through L-013
  - `.openclaw/dreaming/failure-patterns.md` (replaced) — adds P-F-005
  - `.openclaw/dreaming/success-patterns.md` (replaced) — adds P-S-004
  - `.openclaw/dreaming/inefficiency-patterns.md` (replaced) — adds P-IP-003
  - `.openclaw/dreaming/skill-usage-scorecard.md` (replaced) — adds "Makefile-driven local validation" slot; updates dreaming dimensions
  - `.openclaw/dreaming/workflow-scorecard.md` (replaced)
  - `.openclaw/dreaming/regression-scenarios.md` (replaced) — adds RS-010, RS-011, RS-012
  - `.openclaw/dreaming/minimax-consumption-brief.md` (replaced)
  - `.openclaw/dreaming/proposed-improvements.md` (replaced) — PI-008 marked APPLIED; PI-009, PI-010 added
  - `.openclaw/dreaming/pr-change-log.md` (replaced — this file)
  - `.openclaw/dreaming/validation-checklist.md` (replaced)
- **Change type:** auto_safe (artifact population; no runtime behavior change)
- **Evidence references:** EV-006, EV-007, EV-008, EV-009
- **Reason for change:** Cycle 2 surfaces cycle-1's evidence-traceability gap (EV-001 was a coarse snapshot of a 16-PR arc); adds PR-review activity as an evidence source (per user confirmation at the start of cycle 2); updates all artifacts to reflect cycle-2 evidence and new patterns.
- **Expected impact:** Dreaming's cycles cumulatively improve. Cycle 3 will see EV-007 + EV-001 together and not duplicate the arc-expansion work.
- **Validation performed:** `make dreaming-validate` returns 105 passed, 1 skipped on the cycle-2 branch.
- **Rollback notes:** `git revert` the commit.
- **Status:** applied

---

## Review-required changes (proposed but NOT applied on this branch)

- PI-002 (state-machine transition-table check) — proposed in `proposed-improvements.md`; not implemented on this branch.
- PI-004 (sub-agent review as slice ship gate) — proposed; not implemented.
- PI-005 (register `code-review-slice-N` as a skill) — proposed; not implemented.
- PI-006 (OpenClaw run log) — proposed; not implemented. **Cycle-2 status: still the single largest unfilled gap.**
- PI-009 (generalize PI-008 to other workflows) — proposed; not implemented.
- PI-010 (treat each EV entry as a candidate for arc expansion) — informational proposal; not a code change.

## Blocked changes

None.

## Cycle-2 self-meta observation

Three commits, three intentional changes — no fix-ups needed. **PI-008 paid for itself in the first 30 seconds of use.** Cycle 1's ratio was 4-feature-to-5-fix-up; cycle 2's ratio is 3-feature-to-0-fix-up. This is the empirical signal that PI-008 is the correct close-out of the cycle-1 fix-up loop (L-009).

---

## Cycle 3 entries

---

## Commit: `chore(dreaming): remove main from push trigger; skip-on-merge-base-equal-HEAD; exclude-current-branch-from-count`

- **Change IDs:** C3-001, C3-002, C3-003
- **Files changed:**
  - `.github/workflows/nightly-dreaming-validation.yml` — remove `main` from `on: push: branches:` (C3-001)
  - `tests/dreaming/test_pr_readiness.py::test_commits_use_chore_dreaming_prefix` — skip when HEAD equals merge-base (C3-002)
  - `tests/dreaming/test_pr_readiness.py::test_only_one_dreaming_branch_exists` — exclude current branch from the count (C3-003)
- **Change type:** auto_safe (CI/test config; no runtime behavior change)
- **Evidence references:** EV-010, EV-011, L-014
- **Reason for change:** Post-PR-#60-merge CI failure on `main`. The dreaming workflow's `push:` trigger included `main`, and the PR-readiness tests are nonsensical on `main`. PI-008 caught the secondary issue (current-branch-included-in-count) on the first local validation run of cycle 3.
- **Expected impact:** Subsequent cycles with merge-to-main will not regress CI on `main`. Future CI workflows written from this precedent will not bundle `main` into PR-readiness suites.
- **Validation performed:** `make dreaming-validate` returns 105 passed, 0 skipped, 0 failed on the cycle-3 branch ahead of any push. CI on PR side to be confirmed.
- **Rollback notes:** `git revert` if the trigger change removes a desired push-time validation.
- **Status:** applied on branch, awaiting PR

---

## Commit: `chore(dreaming): populate cycle-3 nightly artifacts`

- **Change IDs:** C3-004
- **Files changed:**
  - `.openclaw/dreaming/evidence-index.md` — EV-010, EV-011
  - `.openclaw/dreaming/lessons-learned.md` — L-014
  - `.openclaw/dreaming/regression-scenarios.md` — RS-013, RS-014
  - `.openclaw/dreaming/proposed-improvements.md` — PI-011
  - `.openclaw/dreaming/nightly-summary.md` (replaced)
  - `.openclaw/dreaming/README.md` — cycle-3 line added
  - `.openclaw/dreaming/pr-change-log.md` (replaced — this file)
- **Change type:** auto_safe (artifact population; no runtime behavior change)
- **Evidence references:** EV-010, EV-011, L-014
- **Reason for change:** Cycle 3's evidence base (CI failure event + PI-008 self-application) must be traceable per cycle-1's evidence-traceability invariant.
- **Expected impact:** Cycle 4 starts with EV-001..EV-011 indexed; no re-coverage needed.
- **Validation performed:** `make dreaming-validate` returns 105 passed, 0 failed on the cycle-3 branch ahead of any push.
- **Rollback notes:** `git revert` the commit.
- **Status:** applied on branch, awaiting PR

---

## Cycle-3 review-required changes (proposed but NOT applied on this branch)

- PI-002, PI-004, PI-005, PI-006, PI-009 (carry from cycle 2) — none implemented in cycle 3
- PI-011 (cycle-3 NEW, auto_safe) — proposed but not applied; doc-only, will land in cycle 4 or later

## Cycle-3 blocked changes

None.

## Cycle-3 self-meta observation

TBD after PR push.

---

## Cycle 4 entries

This cycle is a maintenance cycle (`P-S-005` NEW): no new evidence on `main` since cycle 3; the two auto_safe PIs cycle 3 surfaced without closing become cycle 4's body.

---

## Commit: `chore(dreaming): document CI trigger model and add workspace pre-check`

- **Change IDs:** C4-001, C4-002
- **Files changed:**
  - `.openclaw/dreaming/workflow-nightly-dreaming.md` — added **CI Trigger Model** section (PI-011, C4-001)
  - `Makefile` — added `dreaming-precheck` target (PI-012, C4-002)
- **Change type:** auto_safe (doc + developer tooling; no runtime behavior change)
- **Evidence references:** EV-012, EV-013, L-015, RS-015
- **Reason for change:** Cycle 3 surfaced the rule that the dreaming validation suite is a PR-readiness suite; the workflow trigger must reflect that. Cycle 3 also surfaced the lagging-branch issue, which PI-012 closes by surfacing workspace state at human time. Both changes were carried in `proposed-improvements.md` as PIs across cycles 3 and 4.
- **Expected impact:** Future cycles don't repeat the trigger-bundle bug (PI-011) and don't trip on lingering branches (PI-012). The PI-012 path also serves as the empirical first instance of the **L-015** pattern: surface workspace-state assertions at human time, not validation time.
- **Validation performed:** `make dreaming-precheck` runs cleanly on the cycle-4 workspace and reports the expected single-branch state. `make dreaming-validate` returns 105 passed, 0 failed locally.
- **Rollback notes:** `git revert` the commit if the doc section is misleading or the precheck target's surface area grows beyond what a one-second check should be.
- **Status:** applied on branch, awaiting PR

---

## Cycle-4 review-required changes (proposed but NOT applied on this branch)

- PI-009 (generalize PI-008 to SGP) — held per user directive ("A then B" reading).
- PI-002, PI-004, PI-005, PI-006 (cycle-1 carry) — none implemented in cycle 4. PI-006 has been proposed for 4 consecutive cycles; cycle 5 candidate.
- PI-010 (cycle-2 informational) — N/A.

## Cycle-4 blocked changes

None.

## Cycle-4 self-meta observation

One commit, zero fix-ups. Cycle-4 sizes align with `P-S-005`. The cycle counter is **1B→2,PI-008→3,CI-fix→4,PI-011+PI-012**. The trend is converging; a future cycle should either take on PI-006 directly or skip until evidence forces the issue.

---

## Cycle 5 entries

This cycle applies the long-deferred PI-006 partially: the downstream side (parser + spec) is in scope; the runtime side (OpenClaw core) is explicitly out.

---

## Commit: `chore(dreaming): add OpenClaw run log spec and deterministic parser (PI-006 partial)`

- **Change IDs:** C5-001 through C5-004
- **Files added:**
  - `.openclaw/dreaming/openclaw-run-log-spec.md` — JSONL format spec, v1 (C5-001)
  - `tests/dreaming/ev_parser.py` — Deterministic parser (C5-002)
  - `tests/dreaming/test_openclaw_run_log_parser.py` — 9 pytest cases (C5-003)
  - `tests/dreaming/fixtures/openclaw-run-log-fixture.jsonl` — Fixture exercising happy + 3 error paths (C5-004)
- **Change type:** review_required (PI-006 specifically demands human review of evidence-collection rules)
- **Evidence references:** EV-014, EV-015, L-016, P-IP-004, RS-016
- **Reason for change:** PI-006 was the single largest unfilled gap from cycle 1 onward. The cycle-5 audit (per RS-016) surfaced that PI-006 bundles two units; this commit applies the downstream one.
- **Expected impact:** When OpenClaw core emits JSONL logs (separate package, separate PR there), dreaming's Stage 1 can read from them instead of `git log`-and-`grep`. The format spec is a stable contract; future runtime work doesn't require spec changes.
- **Validation performed:** `make dreaming-validate` returns 116 passed, 1 skipped. The 9 parser tests cover happy path + 4 error/edge cases + 2 truncation tests.
- **Rollback notes:** `git revert` if the spec's truncation rules or versioning policy turn out to be wrong. The parser itself is well-tested and isolated.
- **Status:** applied on branch, awaiting PR

---

## Commit: `chore(dreaming): populate cycle-5 nightly artifacts; mark PI-006 partial`

- **Change IDs:** C5-005 through C5-007
- **Files changed:**
  - `.openclaw/dreaming/evidence-index.md` — EV-014, EV-015, EV-016 (cycle 5 evidence)
  - `.openclaw/dreaming/lessons-learned.md` — L-016
  - `.openclaw/dreaming/regression-scenarios.md` — RS-016
  - `.openclaw/dreaming/inefficiency-patterns.md` — P-IP-004
  - `.openclaw/dreaming/proposed-improvements.md` — PI-013 added and APPLIED; PI-006 status changed from `proposed` to **`partial`** in both summary tables; cycle markers bumped cycle-4→cycle-5 across all artifacts
  - `.openclaw/dreaming/nightly-summary.md` (replaced)
  - `.openclaw/dreaming/pr-change-log.md` (replaced — this file)
- **Change type:** review_required (artifact population + scope-status change of PI-006)
- **Evidence references:** EV-014, EV-015, EV-016, L-016, P-IP-004, RS-016
- **Reason for change:** Per cycle-1 spec, every cycle's evidence and PI status is reflected in the artifacts. The PI-006 status change is the most consequential artifact edit — it signals to future readers that part of PI-006 is done and part is not.
- **Expected impact:** Cycle 6 reads `partial` and understands the scope split without redoing the audit.
- **Validation performed:** `make dreaming-validate` returns 116 passed, 1 skipped locally.
- **Rollback notes:** `git revert` the commit.
- **Status:** applied on branch, awaiting PR

---

## Cycle-5 review-required changes

- PI-006 itself → **partial** (cycle 5; downstream applied, runtime side still unfilled in OpenClaw core)

## Cycle-5 blocked changes

None.

## Cycle-5 self-meta observation

Cycle 5 rebroke the monotonically-decreasing commit-count trend (`4→3→2→2→2`) by applying the largest deferred PI. The diminishing-returns P-S-005 curve now reads "longer cycle intentional" rather than "no new work".


---

## Cycle-7 (2026-06-30) — file PI-014, add RS-017, back-fill EV-016

- **Cycle:** 7
- **Branch:** `dreaming/nightly-execution-quality-2026-06-30-cycle-7`
- **Originating user request:** "File new PI and start cycle 7" (Telegram msg #11563, 2026-06-30 23:40 GMT+2)
- **Trigger context:** Followed cycle-6 closeout memo (`memory/2026-06-30-cycle-6-final.md`), which surfaced the cyber-signal-daily cron staleness as a "worth filing" item. User picked it up.
- **Safety classification:** all cycle-7 changes are `auto_safe` (PI/RS/EV artifacts; no code; no runtime; no schema; no skill/workflow).

### Cycle-7 review-required changes

None. All changes are `auto_safe`.

### Cycle-7 blocked changes

None.

### Cycle-7 artifacts changed

- `.openclaw/dreaming/proposed-improvements.md` — PI-014 entry (NEW, cycle 7, auto_safe, proposed); cycle-7 status table appended.
- `.openclaw/dreaming/regression-scenarios.md` — RS-017 entry (NEW, cycle 7; status: `failing` baseline).
- `.openclaw/dreaming/evidence-index.md` — EV-016 entry (NEW, cycle 7); supersedes a same-numbered cycle-5 cycle-shape observation (preserved in cycle-5 nightly summary).
- `.openclaw/dreaming/nightly-summary.md` — cycle-7 body prepended; cycle-5 body preserved below as "restored after cycle-7 header prepend" with a cross-reference to the EV-016 supersession.
- `.openclaw/dreaming/pr-change-log.md` — this section.

### Cycle-7 evidence references

- EV-016 (cycle 7) — `cyber-signal-daily` cron feed pipeline is broken (cron `runs` history; `/tmp/cyber-signal-feeds.json` mtime; `ls scripts/` ENOENT).
- RS-017 — cron deliverable freshness check (NEW, cycle 7).
- PI-014 — restore the fetch script (NEW, cycle 7, auto_safe, proposed).

### Cycle-7 reason for change

The cyber-signal-daily cron has been silently producing 19-day-stale briefs for the entire window since 2026-06-11. The brief deliveries themselves are correct (the agent is doing the right thing with stale data), but the failure mode is structural — a missing shell script. Filing it as PI-014 makes the broken state visible; adding RS-017 ensures the next 19-day-stale window is caught earlier (manual inspection on each cron run).

### Cycle-7 expected impact

- PI ledger gains a new `auto_safe` item with concrete validation criteria (script exists; cron delivers fresh data).
- Regression scenario RS-017 is the first RS to cover a non-dreaming artifact (a cron on the gateway). This sets a precedent: dreaming's nightly review can flag non-dreaming issues as long as they're filed with the auto_safe/review_required/blocked schema.
- EV-016 supersession is documented (cycle-5 EV-016 was a cycle-shape observation; cycle-7 EV-016 is an infrastructure-failure observation; the number is reused because the cycle-5 entry was preserved and remains accurate as a cycle-shape note).

### Cycle-7 validation performed

- `make dreaming-validate` was run on `main` post-cycle-6-merge (`c21b712`) during cycle-6 closeout — **123 passed, 0 failed, 0 skipped**.
- No new automated tests added in cycle 7 (RS-017 is a manual-inspection regression check, by design).
- All cycle-7 edits are text-only artifacts; `tests/dreaming/` is unchanged.

### Cycle-7 rollback notes

`git revert` the cycle-7 commit. No data migrations, no state changes, no schema changes — pure artifact rollback.

### Cycle-7 status

applied on branch, awaiting PR (cycle-7 branch `dreaming/nightly-execution-quality-2026-06-30-cycle-7`; awaiting commit + push + PR creation)

### Cycle-7 self-meta observation

Cycle 7 is the first cycle whose substantive work is **outside the dreaming-workflow's own surface area**. PI-014's fix lives in `/data/.openclaw/workspace/scripts/`, a directory that does not currently exist on this gateway. The cycle-7 framing is "out-of-scope ledger addition" — a different shape from cycle 5's "biggest cycle since 1" (more files) and cycle 6's "substantive-by-handoff" (harness document). The cycle-size table stays at `4→3→2→2→2→2→2` (logical feature commits = 2). The diminishing-returns P-S-005 curve is preserved.

Whether cycle 7 should expand into a 3-commit cycle (artifacts + fetch script + cron adjustment) is a scope decision deferred to a future cycle. Cycle 7 keeps it tight: 2 commits, artifacts-only, PI body explicitly notes "fix is on the gateway, not in this repo's package."



---

## Cycle-8 (2026-07-01) — add Stage -2 Surface-Scope Pre-Declaration (PI-015)

- **Cycle:** 8
- **Branch:** `dreaming/nightly-execution-quality-2026-07-01-cycle-8`
- **Originating user request:** "let's define cycle 8 to evolve workflow" (Telegram msg #11587, 2026-07-01 00:51 GMT+2), with clarifications at #11589 and #11592.
- **Trigger context:** "evolve workflow" was ambiguous until clarified to mean the dream workflow's own procedure document (`.openclaw/dreaming/workflow-nightly-dreaming.md`), not a neighboring workflow. Q1: yes (scope-pre-declaration direction), Q2: substantive (modify workflow doc + tests + RS + EV), Q3: no (no off-limits items in cycles 1–7).
- **Safety classification:** all cycle-8 changes are `auto_safe` (workflow-doc change + test addition + RS + EV + PI). No code changes; no production-runtime changes; no schema migrations.

### Cycle-8 review-required changes

None. All changes are `auto_safe`.

### Cycle-8 blocked changes

None.

### Cycle-8 artifacts changed

- `.openclaw/dreaming/workflow-nightly-dreaming.md` — Stage -2 added before Stage -1 (NEW, PI-015); ~25 lines.
- `tests/dreaming/test_pr_readiness.py` — `test_declares_surface_scope_in_trigger` added (NEW); ~55 lines.
- `.openclaw/dreaming/regression-scenarios.md` — RS-018 entry (NEW).
- `.openclaw/dreaming/evidence-index.md` — EV-017 entry (NEW).
- `.openclaw/dreaming/proposed-improvements.md` — PI-015 entry (NEW, cycle 8, auto_safe, APPLIED this cycle); cycle-8 status table appended.
- `.openclaw/dreaming/nightly-summary.md` — cycle-8 body prepended (uses Stage -2 schema, dogfooding); cycle-7 body preserved below.
- `.openclaw/dreaming/pr-change-log.md` — this section.

### Cycle-8 evidence references

- EV-017 (cycle 8, NEW) — cycles 5/6/7 each retrofitted scope justification; no pre-declaration stage existed.
- RS-018 (cycle 8, NEW) — most recent cycle's Trigger section must declare surface scope.
- PI-015 (cycle 8, NEW, APPLIED this cycle) — Stage -2 Surface-Scope Pre-Declaration.

### Cycle-8 reason for change

Cycles 5, 6, and 7 each shipped a self-meta observation justifying scope decisions that were not surfaced until close-out. Stage -2 (PI-015, cycle 8) makes the scope decision a pre-cycle artifact, not a post-cycle observation. The new test `test_declares_surface_scope_in_trigger` enforces ongoing compliance: the most recent cycle's Trigger section must contain all four field labels (Workflow target, Surface area, Dreaming-ledger scope, Cycle-size budget). Past cycles' Trigger sections are preserved as historical record; the test is forward-looking.

### Cycle-8 expected impact

- Future cycles pre-declare scope at human time (when planning) instead of justifying at audit time (when closing).
- Cross-repo work (cycle 6 pattern) and non-dreaming-ledger work (cycle 7 pattern) become structural artifacts registered before the cycle ships, not afterthoughts.
- The diminishing-returns P-S-005 curve is preserved at 0 CI fix-ups; cycle 8 is a single-commit cycle.

### Cycle-8 validation performed

- **Pre-commit:** ran `test_declares_surface_scope_in_trigger` against the cycle-7 nightly-summary.md (before cycle-8 edits) — confirmed it **fails** with the expected diagnostic ("Missing Stage -2 fields: ['Workflow target', 'Surface area', 'Dreaming-ledger scope', 'Cycle-size budget']"). This proves the test is actually checking what it claims.
- **Pre-push:** `make dreaming-validate` on the cycle-8 branch — expected: **123 passed, 0 failed, 1 skipped** (the empty-range commits-prefix test, same skip rule). The new test must pass because cycle-8's Trigger is written in the new format.
- **Post-merge on main:** the new test continues to pass because cycle-8's Trigger is the most recent in the file.

### Cycle-8 rollback notes

`git revert` the cycle-8 commit. The Stage -2 docstring is forward-looking; reverting the cycle-8 commit removes Stage -2 from the workflow doc, removes the test, removes RS-018/EV-017/PI-015 from their respective ledgers, and reverts nightly-summary.md to its pre-cycle-8 state. Past cycles' Trigger sections are not affected.

### Cycle-8 status

applied on branch, awaiting PR (cycle-8 branch `dreaming/nightly-execution-quality-2026-07-01-cycle-8`; awaiting commit + push + PR creation)

### Cycle-8 self-meta observation

Cycle 8 is the first cycle where the workflow-doc change is the deliverable, not just a side effect. Cycles 2 and 4 added workflow stages (Stage 0, Stage -1) as part of broader PI rollouts; cycle 8 adds Stage -2 as the cycle's entire substantive work. The cycle-size table stays at `4→3→2→2→2→2→2→1` (logical feature commits = 1).

Cycle 7's bookkeeping nit (table said 2 commits, actual was 1) is reconciled in cycle 8's row of the cycle-size table.

### Pre-push catch (cycle 8)

Same as cycle 7's pre-push catch: `test_only_one_dreaming_branch_exists` flagged lingering dreaming branches locally (cycle 5 and cycle 6 from prior sessions). Cleaned with `git branch -D`. PI-008 pattern from cycle 2; the test docstring at `tests/dreaming/test_pr_readiness.py::test_only_one_dreaming_branch_exists` explicitly references this precedent.


---

## Cycle-9 (2026-07-01) — file PI-016 (cycle closeout memo convention)

- **Cycle:** 9
- **Branch:** `dreaming/nightly-execution-quality-2026-07-01-cycle-9`
- **Originating user request:** "Kick off cycle 9" (Telegram msg #11611, 2026-07-01 01:06 GMT+2)
- **Trigger context:** Cycle 8's merge closeout (`memory/2026-07-01-cycle-8-closeout.md`) surfaced PI-016 as a candidate for the next cycle. With PI-006a, PI-014, PI-009, and the AI-overload review date (2026-07-15) all in their prior-cycle states and no new external evidence, cycle 9's natural opening is the procedural-evolution candidate from the closeout memo's "Cycle 9 candidates" list.
- **Safety classification:** all cycle-9 changes are `auto_safe` (PI entry + cycle-9 Trigger + pr-change-log row). No code changes; no production-runtime changes; no schema migrations.

### Cycle-9 review-required changes

None. All changes are `auto_safe`.

### Cycle-9 blocked changes

None.

### Cycle-9 artifacts changed

- `.openclaw/dreaming/proposed-improvements.md` — PI-016 entry (NEW, cycle 9, auto_safe, proposed); cycle-9 status table appended.
- `.openclaw/dreaming/nightly-summary.md` — cycle-9 body prepended (uses Stage -2 schema, dogfooding); cycle-8 body preserved below.
- `.openclaw/dreaming/pr-change-log.md` — this section.

### Cycle-9 evidence references

- EV-018 (cycle 9, NEW) — two consecutive closeout memos mislabeled `make dreaming-validate` output.
- cycle-7 closeout memo (`memory/2026-07-01-cycle-7-final.md`) — first occurrence of the validation-counting-error pattern.
- cycle-8 closeout memo (`memory/2026-07-01-cycle-8-final.md`) — second occurrence (branch-local count mislabeled as `main` count).
- cycle-8 merge closeout memo (`memory/2026-07-01-cycle-8-closeout.md`) — disclosed the bookkeeping error and proposed the convention.

### Cycle-9 reason for change

Two consecutive closeout memos (cycles 7 and 8) mislabeled `make dreaming-validate` output by quoting the validator's headline number without distinguishing branch-local from `main` post-merge counts. PI-016 codifies the convention: every cycle closeout memo quotes `make dreaming-validate` output **twice when applicable** — branch-local count AND `main` post-merge count, both with explicit branch context. Cycle 9's own closeout memos (this cycle's cycle-closeout and merge-closeout, when the latter lands) are the first written under the new convention.

### Cycle-9 expected impact

- Eliminates the recurring bookkeeping-error pattern in cycle closeout memos.
- Future closeout memos don't need correction entries.
- The validation discipline is preserved and accurately reported.

### Cycle-9 validation performed

- **Branch-local:** `make dreaming-validate` on the cycle-9 branch (commit hash TBD until commit lands) — actual count to be recorded at commit time and in the cycle-closeout memo.
- **Stage -2 enforcement:** `test_declares_surface_scope_in_trigger` reads cycle-9's Trigger section (top of `nightly-summary.md`) and asserts the four field labels appear. Cycle 9's Trigger is written in the new format, so the test passes.
- **`main` post-merge (forecast):** cycle 9 adds 0 new tests, so the `main` post-merge count should match cycle 8's `main` post-merge count (122 passed + 1 skipped + 1 expected-fail-on-main on `ec087fe`). Forecast: **122 passed + 1 skipped + 1 expected-fail-on-main on `main` post-cycle-9-merge**.
- **Post-merge validation (PI-016 self-applied):** the cycle-9 closeout memos will quote both counts with explicit branch context, per PI-016.

### Cycle-9 rollback notes

`git revert` the cycle-9 commit. The PI-016 entry is removed from `proposed-improvements.md`, the cycle-9 body is removed from `nightly-summary.md`, and this pr-change-log row is removed. No data migrations, no state changes — pure artifact rollback.

### Cycle-9 status

applied on branch, awaiting PR (cycle-9 branch `dreaming/nightly-execution-quality-2026-07-01-cycle-9`; awaiting commit + push + PR creation)

### Cycle-9 self-meta observation

Cycle 9 is the first cycle whose substantive work is a **procedural convention about how I write memos, not a code/doc/artifact change**. The cycle-size table goes `4→3→2→2→2→2→2→1→1→1` (logical feature commits = 1). Three cycles in a row (7, 8, 9) have all been PI-as-self-discipline cycles — cycles where the cycle's value is in the ledger entry, not in a deliverable.
