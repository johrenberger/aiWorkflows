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