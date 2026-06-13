# Story 023: v2 `--module auto` — cross-module coverage ingest

## Goal

As a test-factory v2 user running against a multi-module Maven repo
(e.g. BroadleafCommerce), I want `test-factory run --module auto` to
ingest coverage reports from **all** Maven modules in the repo, not
just the `--module`-scoped slice, so that `risk_scores.json` reflects
the **whole repo's** coverage gap.

## Background

Story 022 (PR #36) discovered that the "5/765 non-zero line_coverage"
measurement was a scoping bug: the previous `test-factory run
--module admin` had filtered v2's inventory to `admin/` files only,
so the `common/` coverage report could not match. Re-running with
`--module common` produced 294/947 non-zero records.

But the **real** fix is to not scope at all. A user running v2
against a multi-module repo should get cross-module coverage by
default. Today:

```
test-factory run --repo /tmp/BroadleafCommerce --module common
# → 947 risk_scores records, 294 with non-zero line_coverage
# → only common/ source files; admin/ files are excluded
```

What we want:

```
test-factory run --repo /tmp/BroadleafCommerce --module auto
# → 1700+ risk_scores records (whole repo)
# → line_coverage populated for any module that has a report on disk
# → modules without reports: 0.0 (correctly treated as a gap)
```

## Why Now

The cross-module coverage problem was the actual root cause of the
5/765 measurement that motivated story 022. Story 022 added a
regression test for the path-matching algorithm (which works), but
it didn't fix the scoping. The scoping is a CLI-level concern, not
a parser-level one.

## Approach

The orchestrator already supports `module=None` (no filter) — see
`orchestrator._file_rows` and the
`if not module_scope: return True` short-circuit in
`_module_matches_scope`. The CLI is the only place that needs
to change.

Concretely:

1. Add a new sentinel value `"auto"` for `--module` (and
   `--scope`, which is an alias).
2. In the CLI dispatch, treat `args.module == "auto"` as
   `module=None` for the subcommands that filter
   (scan, coverage, score, queue, workitems, report, run,
   pr-summary).
3. The subcommands that take `module` as a *target* (branch,
   commit) keep their current behavior — passing `"auto"` is a
   user error there (these commands require a specific module
   name).
4. Add a `MODULE_AUTO` constant in `cli.py` and unit tests
   pinning the dispatch.

This is intentionally minimal: no orchestrator changes, no new
file formats, no new artifacts. Just a CLI alias for
"`module=None`".

## Acceptance Scenarios

1. **`--module auto` is equivalent to no module filter for
   filter-style subcommands.**
   Given a multi-module repo (e.g. Broadleaf, with `common/`,
   `admin/...`)
   When the user runs `test-factory scan --module auto`
   Then the resulting `repo_inventory.json` contains files from
   every module (not just one).

2. **`--scope auto` is an alias for `--module auto`.**
   Given the same repo
   When the user runs `test-factory scan --scope auto`
   Then the result is identical to `--module auto` (both pass
   `module=None` to the orchestrator).

3. **Coverage ingest from all modules works with
   `--module auto`.**
   Given a repo with JaCoCo reports under
   `common/target/site/jacoco/jacoco.xml` and
   `admin/.../target/site/jacoco/jacoco.xml` (multiple reports)
   When the user runs `test-factory coverage --module auto`
   Then the resulting `coverage_baseline.json` contains records
   from **all** reports (the existing `_discover_reports`
   glob already finds them; `--module auto` simply avoids
   filtering the inventory to one module so the join in
   `_normalize_coverage_path` works across modules).

4. **`--module auto` is rejected for subcommands that take
   `module` as a target.**
   Given the user runs `test-factory branch --module auto` or
   `test-factory commit --module auto`
   Then the CLI errors with a clear message
   ("--module auto is not valid for branch/commit; specify a
   concrete module name").
   (Without this guard, "auto" would be passed to the orchestrator
   and likely produce a confusing error downstream.)

5. **Existing `--module <name>` and `--scope <name>` behavior
   is unchanged.**
   Given a single-module repo
   When the user runs `test-factory scan --module common`
   Then the inventory contains only files under `common/`
   (regression test — the sentinel must not break the
   string-value path).

## Executable Test Mapping

`tests/test_023_v2_module_auto.py` — 4-5 unit tests covering
scenarios 1, 2, 3, 4, 5. The first three are CLI-level
integration tests (build the parser, dispatch through `main()`,
inspect the artifacts). Scenario 4 is a CLI-level error test.
Scenario 5 is a regression test using the existing single-module
fixture.

## Done Criteria

- New sentinel `MODULE_AUTO = "auto"` in `test_factory/cli.py`.
- CLI dispatch treats `args.module == MODULE_AUTO` as `module=None`
  for filter-style subcommands
  (scan, coverage, score, queue, workitems, report, run,
  pr-summary).
- CLI errors with a clear message when `args.module == MODULE_AUTO`
  is passed to `branch` or `commit`.
- New BDD test file `test_023_v2_module_auto.py` with 4-5 unit
  tests, all passing.
- Existing v2 tests pass (the change is additive).
- On a real Broadleaf run with `mvn -pl common,admin test
  jacoco:report` (or a more comprehensive command) followed by
  `test-factory run --module auto`, the `risk_scores.json` has
  records from both modules with non-zero `line_coverage`
  wherever the report had data.

## Out of Scope (Future Stories)

- Automatic per-module coverage generation (running
  `mvn test jacoco:report` per module inside the orchestrator).
  The user is expected to pre-generate the reports. A future
  story could add this as a `--generate-coverage --module auto`
  combo.
- A `--module auto` mode that **also** aggregates reports across
  the inventory (deduplicating by FQCN when a class appears in
  multiple modules' reports). Out of scope — current behavior
  (first-match-wins in `_merge_coverage_records`) is correct for
  the common case where each class lives in exactly one module.
- Module-list introspection (printing the available modules
  before running v2). A future story could add
  `test-factory modules --repo <path>`.

## End-to-End Evidence (Broadleaf, 2026-06-13, post-fix)

Pre-generate coverage for both modules:
```
mvn -pl common test jacoco:report
mvn -pl admin/broadleaf-open-admin-platform test jacoco:report
```

Run v2 with the new flag:
```
test-factory run --repo /tmp/BroadleafCommerce --out /tmp/v2-broadleaf-auto --module auto
```

Expected `risk_scores.json` (post-fix):
- total records: ~1700+ (whole repo's Java files, not just one module)
- records with non-zero line_coverage: sum of per-module results
  (e.g. 294 from common + ~500 from admin/open-admin-platform, if
  the admin module's tests ran successfully)

Pre-fix baseline (from story 022's note):
- total: 947
- non-zero: 294 (only common; admin excluded by `--module common`)
