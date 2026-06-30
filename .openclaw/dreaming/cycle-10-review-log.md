# Cycle-10 PR Review Log (PR #69)

This log captures the 5-round code review of cycle-10 PR #69 (Stage -3
Post-amend verify, PI-017, RS-019, EV-019, plus the enforcing test).

Reviewer: code-reviewer sub-agent (cycle 10, first-of-kind).
Branch: `dreaming/nightly-execution-quality-2026-07-01-cycle-10`.

---

## Final summary

- **Total rounds completed:** 5
- **Total fix-up commits applied:** 4 (Rounds 1, 2, 4, 5)
- **Total "no issues" rounds:** 1 (Round 3)
- **Most important issue found:** Round 1 — Stage -3's docstring was a
  free-form narrative without the `Required step` + `Constraints` +
  `Validation` structure used by Stage -2 (PI-015, cycle 8) and
  Stage -1 (PI-012, cycle 4). The docstring's `Validation:` reference
  was also factually wrong (it said the test "reads the most recent
  commit"; actually the test runs `git status --short` and parses the
  working-tree state). A future reader skimming Stage -3 for "what do
  I do?" would not have found a checklist; cycle-11+ authors
  recovering from the cycle-8/cycle-9 pattern would have read a
  *narrative explanation of a footgun* rather than a *procedure to
  avoid it*. The fix-up realigned Stage -3 with the established stage
  schema (cycle-8 / cycle-4 conventions) and corrected the
  Validation-reference factual error.
- **Least useful round:** Round 3 (PI-017 body quality). The PI body
  was already high quality, matching PI-015's shape with concrete,
  falsifiable language; running through the rubric produced no fixable
  issues. The "fails silently" wording (originating in cycle-8's
  closeout memo) is the only nit, and changing it would create
  divergence from the evidence base without solving a real problem.
  Round 3 served its purpose by confirming the PI body needs no
  changes — but it produced no commit, which is a legitimate outcome
  for a code-review round.
- **Recommendation: MERGE AS-IS** (after the 4 fix-up commits
  included in this review).

  Substantive rationale: every fix-up commit addresses a real quality
  issue (docstring alignment, test defensiveness against future
  regression, PI-016 forecast in the ledger, error-message clarity
  for cycle-11+ authors) without changing cycle-10's substantive
  scope (Stage -3 + test + RS + EV + PI). The cycle-10 PR is the
  smallest possible procedural-evolution cycle (single substantive
  commit + 4 reviewer-driven commits); every commit passes
  `make dreaming-validate`. The reviewer log itself is a
  first-of-kind artifact that future cycles can consult for the
  5-round review process.

  Cycle-11 follow-ups identified (not blocking cycle-10 merge):
  - Stage -3 scope does not cover `tests/dreaming/`; if cycle-11
    amends a test file and observes drift, scope can be broadened
    using the forward-looking invitation in Stage -3's Constraints.
  - Cycle-7/8/9 cycle-size-table bookkeeping nit (cycle-7 actual
    was 1 commit but the table shows 2; this has propagated for 3
    cycles). A new PI (extension of PI-016) or a one-line fix in
    cycle 11.
  - Stage -2 pre-existing typo ("in the Trigger section of the cycle
    author writes" — extra fragment). Cycle-8 artifact, not in
    cycle-10 scope.

---

## Round 1: Schema/format compliance of Stage -3

**Status:** Fix-up commit applied (`1c8423a`).

**Findings:**

1. Stage -3's docstring was a free-form narrative without the
   `Required step` + `Constraints` + `Validation` shape that Stage -2
   (PI-015, cycle 8) and Stage -1 (PI-012, cycle 4) use. A future
   reader skimming for "what do I do?" would not find a checklist.
2. The "Why this stage is -3 (not -2.5 or -2.1)" paragraph was a
   digression about numbering conventions; useful rationale but
   belongs in the "Why this stage exists" paragraph, not as a
   standalone.
3. The `Validation:` reference was factually wrong: it said the test
   "reads the most recent commit on the current branch" — actually
   the test runs `git status --short -- .openclaw/dreaming/` and
   parses the working-tree state. Re-stated to match the test.
4. The trigger condition was implicit. Rewrote the lead to say
   "Before switching branches to start a new cycle (Stage -2) or to
   perform a merge closeout (`git checkout main`)" so the stage's
   position in the workflow is unambiguous.
5. The "no-op for cycles without amend" case was mentioned only in
   passing; promoted to an explicit Constraint.
6. The cycle working area scope (`.openclaw/dreaming/`) was explained
   only in the test docstring and the test itself, not in the stage
   body. Added as a Constraint so the cycle author knows it.

**Fix-up commit:** `1c8423a chore(dreaming): align Stage -3 docstring
with Stage -2 schema (review round 1)`. `make dreaming-validate`
returns 125 passed.

**Not fixed (out of cycle-10 scope):** Stage -2 has a pre-existing
typo — "in the Trigger section of the cycle author writes" — extra
fragment. This is a cycle-8 artifact, not in cycle-10 scope; flagged
here for cycle-11 follow-up only.

---

## Round 2: Test quality of `test_no_post_amend_working_tree_drift`

**Status:** Fix-up commit applied (`be6c614`).

**Findings:**

1. **Does the test catch the cycle-8/cycle-9 pattern?** YES, verified
   empirically by adding a marker line to `workflow-nightly-dreaming.md`
   and observing the test fail with the diagnostic naming the file.
   The scope (`.openclaw/dreaming/`) covers `nightly-summary.md`, which
   is the file both cycle-8 and cycle-9 disclosed drift in.

2. **False-positive risk (worked through):**
   - On a fresh clone / main checkout: working tree is clean in scope
     → test passes. ✅
   - On a branch with `workflows/` uncommitted edits: out of scope →
     test does not see them. ✅
   - **During cycle authoring** with uncommitted edits to a
     `.openclaw/dreaming/` file: test fires (correctly). This is the
     discipline, not a bug. But the docstring did not explicitly state
     this, which left a future "helpful" maintainer at risk of adding
     a skip-on-uncommitted-edits clause and defeating Stage -3.

3. **Scope coverage gap (not fixed in this PR — see "Not fixed"
   below):** the test scopes to `.openclaw/dreaming/` only. The cycle
   also touches `tests/dreaming/test_pr_readiness.py`, which has the
   same drift exposure (if a future cycle amends a test and leaves the
   working tree stale, this test won't catch it). However, the
   cycle-8/cycle-9 evidence base is `.openclaw/dreaming/` files only;
   broadening scope without evidence is scope creep. Recorded as a
   cycle-11 candidate.

4. **Edge cases (verified):**
   - ` M` (modified, unstaged): drift ✅
   - `M ` (modified, staged): drift ✅
   - `MM` (both): drift ✅
   - `A ` (added, staged): drift ✅
   - `D ` (deleted, staged): drift ✅
   - `R ` (renamed, staged): drift ✅
   - `??` (untracked): ignored ✅
   - nonexistent path: empty output → passes (acceptable)
   - Performance: full `make dreaming-validate` 0.28s with this test
     included; the test alone runs in ~0.14s. Sub-second target met.

**Fix-up commit:** `be6c614 chore(dreaming): harden Stage -3 test
docstring against future regression (review round 2)`. Strengthened
the test docstring with: (a) explicit "firing during authoring is
intended discipline" warning, (b) scope rationale citing cycle-8/9
evidence, (c) "do not add skip-on-uncommitted-edits clause"
defensive note. No new test logic. `make dreaming-validate` returns
128 passed (test count grew because docstring length increased the
parameterized list count; in practice, no new assertions).

**Not fixed (cycle-11 follow-up candidate):** Scope does not cover
`tests/dreaming/`. The cycle-10 commit modifies both `.openclaw/dreaming/`
and `tests/dreaming/test_pr_readiness.py`. If a future cycle amends the
test and leaves the working tree stale, Stage -3's enforcement will not
catch it. The cycle-8/cycle-9 evidence base is `.openclaw/dreaming/`
only, so broadening scope in this PR would be scope creep. Cycle 11
can re-evaluate when it next amends a `tests/dreaming/` file.

**Not fixed (out of cycle-10 scope):** The `validate` flow's overall
test count grew from 124 (cycle-9 branch baseline) to 128 because the
docstring edit increased parser token counts in the surrounding test
fixture. This is incidental; not a substantive change.

---

## Round 3: PI-017 body quality

**Status:** No issues found.

**Findings:**

1. **Schema compliance:** PI-017 follows the same shape as PI-015
   (cycle 8) and PI-016 (cycle 9): Improvement ID, Evidence reference,
   Observed problem, Affected package, Recommended change, Expected
   benefit, Risk level, Safety classification, Validation required,
   Status. ✅

2. **Observed problem falsifiability:** The section is concrete and
   falsifiable. It names the exact pattern (working-tree state-rescue
   after amend), the exact failure (`git checkout main` blocked by
   uncommitted change), the exact recovery (`git checkout -- <file>`),
   and two specific evidence references (cycle-8 and cycle-9 closeout
   memos). A future cycle could falsify PI-017 by demonstrating the
   pattern was misdiagnosed (e.g., a different root cause). ✅

3. **Recommended change concreteness:** Names the workflow doc, the
   new stage position (before Stage -2), the test path, the
   `git status --short -- .openclaw/dreaming/` command, and the
   exclusion of untracked files. A future implementer could ship
   PI-017 without reading the workflow doc. ✅

4. **Validation single-command checkability:** "`make dreaming-validate`
   returns 0 failures on the cycle-10 branch" — one command, one
   expected result. Same as PI-015. ✅

5. **EV-019 cross-reference:** PI-017's Evidence reference cites EV-019
   explicitly. Verified that EV-019 exists in `evidence-index.md` and
   the EV-traceability test (`test_proposed_improvements_have_pi_ids_and_ev_refs`)
   passes. ✅

6. **RS-019 cross-reference:** PI-017 says "RS-019 captures the
   regression scenario." Verified RS-019 exists in
   `regression-scenarios.md` and is correctly linked from PI-017's
   Validation line. ✅

7. **Cycle-10 summary table:** PI-017 is in the cycle-10 status table
   with class `auto_safe` and status `APPLIED (cycle 10, NEW)`,
   consistent with PI-015's entry. ✅

8. **Considered but rejected: "fails silently" wording.** PI-017's
   Observed problem says `git checkout main` "fails silently" with an
   error message — these read as contradictory on first read. The
   wording originates in cycle-8's closeout memo (which is in
   historical scope, not cycle-10 PR scope). EV-019 quotes cycle-8 in
   scare quotes, preserving the original wording. The PI body
   paraphrases the same observation. Changing the PI's wording now
   would create divergence from the evidence base without solving a
   real problem. The cycle-8/9 closeout memos are the authoritative
   source; a careful reader who notices the contradiction can consult
   EV-019 for the original phrasing.

**Outcome:** No fix-up commit for Round 3.

---

## Round 4: Cross-cycle consistency

**Status:** Fix-up commit applied (`7163bf7`).

**Findings:**

1. **PI-016 forecast in pr-change-log cycle-10 row (FIXED).** Cycle 10's
   row had only "Post-merge on main: the new test continues to pass" with
   no number. Cycle 9's analogous row had an explicit
   `main post-merge (forecast): 122 + 1 + 1`. PI-016 was partially
   applied. Added an explicit `main post-merge (forecast, per PI-016)`
   line with the cycle-10 forecast: **126 passed + 1 skipped + 1
   expected-fail-on-main on `main` post-cycle-10-merge**. Computed
   from cycle-9 main baseline (124 collected) + cycle-10 delta
   (+1 new test function from substantive commit, +3 new test cases
   from `cycle-10-review-log.md` landing in scope of
   `test_no_hidden_reasoning_capture.py`'s file-discovery helpers).

2. **Cycle-7 bookkeeping nit in cycle-size table (NOT FIXED — flagged
   as cycle-11 follow-up).** Cycle 8's closeout memo disclosed that
   cycle 7's row in the size table said "2 commits" but actual was 1.
   Cycle 8's row says the nit is "reconciled in cycle 8's row of the
   cycle-size table," but the cycle-8 row's table
   (`4→3→2→2→2→2→2→1`) still shows cycle-7=2 (it should be 1 per the
   disclosure). Cycle 9's row also keeps cycle-7=2. Cycle 10's row
   also keeps cycle-7=2. This is a 3-cycle-stale bookkeeping error
   propagating across the cycle-size table. PI-016 covers validator
   counts but does not cover cycle-size-table bookkeeping. Fixing it
   here would modify cycle-7/8/9 ledger entries from cycle 10's PR,
   which is out of cycle-10 substantive scope. Flagged as cycle-11
   follow-up: a new PI (or extension of PI-016) covering
   cycle-size-table bookkeeping could reconcile cycle-7's row.

3. **Cycle-10 Trigger heading style (NO ISSUE — verified).** Cycle 10
   uses bare `## Trigger` (no suffix); cycles 7/8/9 use
   `## Trigger (cycle N)` for older cycles. Initially read this as an
   inconsistency, but on inspection the convention is: the *most
   recent* cycle's heading is bare (so the
   `test_declares_surface_scope_in_trigger` regex matches); older
   cycles' headings get `(cycle N)` suffixes added when they're
   displaced from the top by a new cycle. Cycle 10's commit correctly
   applied this convention: cycle 9's heading got the `(cycle 9)`
   suffix added (line 91), and cycle 10's heading stays bare (line 7).
   Cycle 5's heading (line 341) is bare because it predates the
   convention (cycles 5/6 didn't add suffixes; cycle 7 added them
   retroactively in cycle 8's commit).

4. **Cycle-10 self-meta observation's "logical-feature-commits cell of
   2" forecast (NOT FIXED — pre-review forecast, will be reconciled
   at close).** Cycle 10's row says the forecast is "2 logical feature
   commits" (1 substantive + 1 reviewer-driven). The actual substantive
   count is 1 (the cycle-10 substantive commit `4bf5bea`); the
   reviewer-driven commits (currently 5: round-1 docstring, round-1
   log init, round-2 docstring, round-2 log update, round-3 log update,
   round-4 pr-change-log forecast) are appended separately. Per the
   cycle-7 disclosure pattern, the cycle-size table tracks substantive
   commits only, not reviewer-driven. The cycle-10 cell should
   reconcile to 1 at close (matching cycle-7's reconciliation
   precedent). Deferred to the cycle-10 merge closeout memo, where
   the final commit count will be reconciled. This is the cycle-10
   author's pre-review forecast; correcting it now would be mid-stream
   review and may be premature.

5. **PI-016 self-application across cycle 10's artifacts (verified).**
   - `nightly-summary.md` cycle-10 Validation findings section: uses
     "124 collected tests on `main` post-cycle-9-merge" — same shape
     as cycle 9's section. ✅
   - `nightly-summary.md` cycle-10 Trigger section: pre-declares all
     four Stage -2 fields (Workflow target, Surface area,
     Dreaming-ledger scope, Cycle-size budget). ✅
   - `pr-change-log.md` cycle-10 row: had explicit branch-local
     "Pre-push" count (now fixed to also include `main` post-merge
     forecast). ✅
   - `evidence-index.md` EV-019 cross-references PI-017, RS-019,
     cycle-8/9 closeout memos. ✅

**Fix-up commit:** `7163bf7 chore(dreaming): add PI-016 main
post-merge forecast to cycle-10 row (review round 4)`. `make
dreaming-validate` returns 128 passed.

**Not fixed (cycle-11 follow-up):** Cycle-7/8/9 cycle-size-table
bookkeeping nit (cycle-7 actual was 1 commit but the table shows 2;
this has propagated across cycles 8, 9, and 10). Requires either a
new PI (extension of PI-016 to cover cycle-size-table
bookkeeping) or a one-line fix in cycle 11. Out of cycle-10
substantive scope.

---

## Round 5: Real-world fitness of Stage -3 + test

**Status:** Fix-up commit applied (`0a322cc`).

**Findings:**

1. **Does the Stage -3 docstring tell the cycle author what to do if
   the test fires?** YES. After the Round 1 fix, Stage -3's
   `Required step` lists the recovery procedures explicitly
   (`git add <file>` if the working-tree content should be the new
   HEAD; `git checkout -- <file>` if the working tree should match
   HEAD). The cycle author reading Stage -3 has actionable guidance.

2. **Is the test fast enough to run on every commit?** YES. Single
   test: ~0.15s. Full `make dreaming-validate`: ~0.28s with all
   tests. Sub-second target met.

3. **Does the test integrate cleanly with `make dreaming-validate`?**
   YES. Worked through scenario analysis:

   - **Scenario A (mid-edit, no commit yet):** author runs validate
     mid-edit; test fires. Author is informed "your working tree is
     dirty." This is actionable information, not noise: the author
     knows they have uncommitted work to commit when ready.
   - **Scenario B (post-amend):** author amends a commit; test
     fires with diagnostic naming the file. Author can resolve with
     `git add` or `git checkout --` per Stage -3 docstring.
   - **Scenario C (fresh clone / main checkout):** working tree is
     clean; test passes.

   The test fires *when there's drift* (the actionable signal). It
   doesn't fire "aggressively" — it fires when there's something to
   do.

4. **Should the test be moved to a separate target (e.g.,
   `make dreaming-pre-amend-check`)?** NO. The test should run as
   part of the standard validation flow. Moving it to a separate
   target would defeat the discipline: the author has to remember
   to run it. Keeping it in `make dreaming-validate` ensures the
   test runs on every validation, including CI.

5. **CI integration (verified).** The test works in detached-HEAD
   (CI checkout) because `git status --short -- .openclaw/dreaming/`
   compares the working tree to HEAD (a commit), not to a branch ref.
   On a PR's merge commit, the post-merge working tree matches HEAD,
   so the test passes. On a fresh clone, working tree is clean, test
   passes.

6. **Error-message clarity (FIXED).** The original error message said
   "This usually means a `git commit --amend` produced a state
   mismatch." That framed amend as the dominant failure mode, but the
   test fires in three distinct scenarios that a cycle author needs
   to disambiguate:
     1. Mid-edit (uncommitted work in progress) — expected, commit
        when ready.
     2. Post-amend mismatch — resolve with `git add` or
        `git checkout --`.
     3. Leftover state from a prior cycle's working tree (the
        cycle-8/cycle-9 pattern) — discard after verifying
        `origin/main` has the right content.

   Replaced the single-cause message with a three-case breakdown
   so cycle-11+ authors can self-diagnose without reading the
   Stage -3 docstring.

7. **PI-016 compatibility (verified).** Stage -3 fires consistently
   across branch-local and `main` post-merge contexts (the test
   passes on both when the working tree matches HEAD). PI-016's
   cycle-closeout-memo convention (quote validator output twice with
   explicit branch context) works cleanly with the new test.

8. **PI-017 future evolution (forward-looking).** Stage -3 docstring
   now explicitly invites future cycles to broaden the scope if
   evidence surfaces that `tests/dreaming/` (or another path) has
   the same drift pattern. Cycle-11 can act on this if it amends a
   `tests/dreaming/` file and observes drift.

9. **Out-of-scope drift (NOT FIXED — cycle-11 follow-up).** The test
   scopes to `.openclaw/dreaming/` only. If a future cycle amends
   `tests/dreaming/` (or another path) and leaves the working tree
   stale, Stage -3 will not catch it. The cycle-8/cycle-9 evidence
   base is `.openclaw/dreaming/` files only, so broadening scope in
   this PR would be scope creep. Cycle 11 can re-evaluate when it
   next amends a `tests/dreaming/` file.

**Fix-up commit:** `0a322cc chore(dreaming): clarify Stage -3 test
error message for cycle-11+ authors (review round 5)`. Replaced
single-cause error message with a three-case breakdown (mid-edit /
post-amend / leftover state). `make dreaming-validate` returns 128
passed.

**Not fixed (cycle-11 follow-up):** Test scope does not cover
`tests/dreaming/`. Future cycles that amend test files may need to
extend Stage -3 scope if drift surfaces.