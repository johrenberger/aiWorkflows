# Story 031 — Split "unmeasurable" from "measurable-zero" in zero-coverage queue

## Why

Code-review H3 from `tasks/2026-06-13-skill-progress-review/reports/code-review-report.md`:

> The `is_zero_coverage` definition treats `branch_coverage=None`
> (not analyzed) the same as `branch_coverage=0.0` (analyzed, no
> branches hit). A file with `branch_coverage=None` may have been
> skipped because no tests could be instrumented for it (e.g.
> aspect-oriented Java, generated code, code with custom JaCoCo
> filters). Surface those as "zero-coverage" lumps them in with
> files that have 0 line coverage — the prioritization is then
> wrong.

This is a real problem in practice. The story 024 end-to-end run
on Broadleaf produced 653 zero-coverage files. Of those, some
are "really untested" (the user's priority) and some are
"couldn't be analyzed by JaCoCo" (a different priority — the
user needs to fix the analysis, not the tests).

## What's in this PR

1. **Add a `coverage_status` annotation to every queue item** with
   one of three values:
   - `"measured_zero"` — line_coverage=0 AND branch_coverage=0
   - `"unmeasurable"` — branch_coverage is None (analysis didn't
     run, or coverage record is missing entirely)
   - `"measured_nonzero"` — line_coverage > 0 (not zero-coverage
     at all, just for completeness)

2. **Split `zero_coverage_queue.json` into two artifacts**:
   - `zero_coverage_queue.json` (unchanged name, narrower scope) —
     only `"measured_zero"` items. These are the user's real
     priority.
   - `unmeasurable_queue.json` (new) — `"unmeasurable"` items. The
     user can act on these separately (e.g. exclude aspect-oriented
     files, add custom JaCoCo filters).

3. **`--zero-coverage-only` flag's semantics**: the flag is now
   even more useful — it filters to `"measured_zero"` (the real
   "no tests" set). `--unmeasurable-only` flag (new) filters to
   `"unmeasurable"`. The original flag's name is preserved to keep
   story 024's contract intact.

4. **`is_zero_coverage()` helper deprecation**: kept for backward
   compat (returns True for both measured_zero and unmeasurable),
   but new code should use `coverage_status()` which returns the
   three-state string.

5. **Update `final_report.md` rendering**: the "Zero-Coverage
   Files" section now has a sub-header for the unmeasurable
   bucket, and the count line says "Measured-zero: N, Unmeasurable:
   M".

## Why this matters

In the story 024 E2E on Broadleaf, of the 653 zero-coverage files,
a real percentage are unmeasurable (JaCoCo couldn't analyze
generated code, aspect-oriented wrappers, etc.). Splitting them
out means the user can:

- Focus the test-writing effort on the measured_zero bucket
  (the real gap).
- Identify the unmeasurable bucket as a separate workstream
  (fix the build / filters).

## Tests

- Existing 12 tests in `test_024_v2_zero_coverage_priority.py`:
  `is_zero_coverage` semantics preserved (backward compat), and
  add a new test that the artifact split happens.
- New 8 tests in a new `test_031_v2_zero_coverage_split.py`:
  - `coverage_status()` returns the right value for each case
  - `queue()` writes both `zero_coverage_queue.json` and
    `unmeasurable_queue.json`
  - `--zero-coverage-only` only returns measured_zero
  - `--unmeasurable-only` only returns unmeasurable
  - The `final_report.md` rendering shows both buckets
  - Old `is_zero_coverage()` still returns True for both cases
    (backward compat)
  - Items with `line_coverage > 0` are in neither bucket
  - Sort order is preserved within each bucket (by risk_score)

## Out of scope

- The `score_file` function's default-to-zero behavior (when
  coverage is None) — that's a separate issue (items that
  haven't been analyzed at all get 0 risk_score because
  everything is 0). Fixing that would change priority
  calculations, which is out of scope.
- A `--zero-coverage-include-unmeasurable` flag (no need; the
  default behavior of including both is what `is_zero_coverage`
  already does).
- Changing the `RiskScoreRecord` model (this is annotation-only).
