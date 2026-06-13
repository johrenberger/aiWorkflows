# Story 020: V2 Always-Generate Coverage

## Goal

As the v2 (test-factory) workflow, I should run coverage generation by
default during `test-factory run`, so that the emitted `risk_scores.json`
has real `line_coverage` values for every file — not a uniform
`line_coverage=0.0` fallback that hides the difference between a file
with 5% coverage and one with 95%.

## Background

Story 019 wired v2's `risk_scores.json` into mutation as a first-class
coverage source. In every mutation run since then, v2 has been invoked
**without** `--generate-coverage`, so `line_coverage` was 0.0 across the
board. This made v2's `coverage_gap` signal degenerate (always "100%
gap") and forced mutation's selector to fall back to its readiness-40
heuristic uniformly.

The cost: ~5-30 min per `test-factory run` for a typical repo, and
v2 mutates the target repo (writes `coverage.json` / `coverage.xml`).
Both are real, and both are why `--generate-coverage` is currently
opt-in (PR #23, 2026-06-10). The fix is to flip the default and give
the user a way to opt out — so that the choice to skip coverage
generation is a deliberate one, not a forgotten flag.

`test-factory coverage` (the standalone subcommand) keeps its current
read-only behavior; coverage generation only happens inside `run`.

## Acceptance Scenarios

1. **Default `test-factory run` generates coverage.**
   Given a target repo with a working primary-adapter coverage command
   When the user runs `test-factory run --repo PATH` (no flag)
   Then `coverage_generate()` is invoked and its result is attached to
   the run record as `coverage_generation` (status="ok" or
   status="no_report_written" — both indicate generation was attempted).

2. **`--no-generate-coverage` skips the generation step.**
   Given the same repo
   When the user runs `test-factory run --repo PATH --no-generate-coverage`
   Then `coverage_generation` is `None` and the run record does NOT
   contain a `coverage_generation` key with a real value.

3. **`--generate-coverage` still works (backward compatibility).**
   Given the same repo
   When the user runs `test-factory run --repo PATH --generate-coverage`
   Then the behavior is identical to the current `generate_coverage=True`
   path (PR #23 contract preserved).

4. **`--generate-coverage` and `--no-generate-coverage` are mutually exclusive.**
   Given any invocation
   When both flags are present
   Then the CLI exits non-zero with a clear argparse error
   ("argument --no-generate-coverage: not allowed with --generate-coverage").

5. **`test-factory coverage` is unchanged.**
   Given the same repo
   When the user runs `test-factory coverage --repo PATH` (no flag)
   Then it does NOT invoke `coverage_generate()`. It only reads existing
   reports (current read-only behavior preserved).

6. **Generation result is reported even when it fails.**
   Given a repo whose primary adapter cannot produce coverage (e.g.
   missing pytest-cov plugin, JaCoCo preflight-blocked, etc.)
   When `test-factory run` completes
   Then `coverage_generation["generation"]["status"]` is one of
   `{"ok", "no_report_written", "error", "failed", "skipped"}` and
   the user can tell whether generation ran but produced no usable
   report vs. never ran. (`failed` = command exited non-zero;
   `error` = unexpected exception; `no_report_written` = exit 0
   but no coverage file appeared; `skipped` = no primary adapter
   for the repo's language.)

7. **CLI help mentions the new default.**
   Given any user running `test-factory run --help`
   When the help text is displayed
   Then it states that coverage generation is on by default, and that
   `--no-generate-coverage` opts out.

## Executable Test Mapping

`tests/test_020_v2_default_generate_coverage.py` — 7 tests covering
scenarios 1-7.

## Done Criteria

- `test-factory run` invokes `coverage_generate()` by default.
- `--no-generate-coverage` is a recognized opt-out flag.
- `--generate-coverage` and `--no-generate-coverage` are mutually exclusive.
- `test-factory coverage` is unchanged (read-only).
- CLI help text reflects the new default.
- End-to-end Broadleaf run proves the new default fires the
  `coverage_generate` step AND surfaces the JaCoCo preflight findings
  (the two `static_surefire_argline_blocks_jacoco` findings) without
  the user having to opt in.
- Existing tests in `tests/test_coverage_generation.py` still pass
  (PR #23 contract preserved).

## End-to-End Evidence (Broadleaf, 2026-06-13)

Run: `test-factory run --repo /tmp/BroadleafCommerce --out
/tmp/v2-broadleaf-story020 --limit 1 --module admin`

Result:
- `coverage_generation.generation.status = "failed"` (Maven build
  hit a flaky MVEL test in `broadleaf-common`; unrelated to story 020)
- `coverage_generation.generation.preflight_findings` contained the
  two `static_surefire_argline_blocks_jacoco` findings (one in
  `pom.xml`, one in `admin/broadleaf-admin-functional-tests/pom.xml`).
  These would only have been surfaced before via the opt-in
  `--generate-coverage` flag.
- `risk_scores.json` was produced (765 records) but `line_coverage=0.0`
  across the board — expected, because the Maven build failed before
  JaCoCo could emit a report. Fixing `line_coverage` for real requires
  the JaCoCo pom patch (a separate story, not story 020's scope).

## Out of Scope (Future Stories)

- JaCoCo static-argLine pom fix (so the Maven build actually produces
  `.exec` files in the first place).
- Routing the generated coverage to an external `--out` dir so the
  target repo is not mutated (e.g. for repos where
  `coverage.json` / `coverage.xml` writes would conflict with a
  checked-in fixture).
- Caching the generated coverage across runs (5-30 min is currently
  paid every time).
