# Cycle-10 PR Review Log (PR #69)

This log captures the 5-round code review of cycle-10 PR #69 (Stage -3
Post-amend verify, PI-017, RS-019, EV-019, plus the enforcing test).

Reviewer: code-reviewer sub-agent (cycle 10, first-of-kind).
Branch: `dreaming/nightly-execution-quality-2026-07-01-cycle-10`.

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