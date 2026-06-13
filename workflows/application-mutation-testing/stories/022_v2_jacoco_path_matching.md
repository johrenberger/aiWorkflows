# Story 022: v2 JaCoCo path-matching — regression net for the existing join

## Goal

As a test-factory v2 maintainer, I want a regression test suite
that pins the path-matching contract between
`CoverageRecord.path` (JaCoCo's dot-package-slash form, e.g.
`org/example/Foo.java`) and v2's `repo_inventory.json` paths
(Maven module-relative form, e.g.
`common/src/main/java/org/example/Foo.java`).

## Background

When v2 ingests a JaCoCo `jacoco.xml`, it produces
`CoverageRecord` entries keyed on JaCoCo's
`org/example/Foo.java`-style paths (the parser joins
`<package>` and `<sourcefile>` from the XML). v2's
`risk_scores.json` is keyed on v2's own inventory file paths
(e.g. `common/src/main/java/org/example/Foo.java`).

The join happens in two places:

1. **Coverage baseline (`coverage_baseline.json`)**:
   `orchestrator._collect_coverage_records` calls
   `_merge_coverage_records(coverage, inventory_paths)`, which
   uses `_normalize_coverage_path` to map each JaCoCo path to an
   inventory path via suffix matching.
2. **Risk score step (`risk_scores.json`)**:
   `orchestrator.score` joins on `coverage_rows.get(row["path"])`.
   The `coverage_rows` dict is built from `coverage_baseline.json`,
   so the join only works if step 1 succeeded.

Reproduced on Broadleaf 2026-06-13 (the run that motivated this
story): 5/765 risk_scores records had non-zero `line_coverage`.
Investigation showed the root cause was **not** the
`_normalize_coverage_path` algorithm — that one is fine. The
root cause was that the previous `test-factory run` was invoked
with `--module admin`, which scopes the inventory to `admin/`
files only. The coverage report was for the `common/` module, so
its files did not appear in v2's inventory at all, and the
suffix-matching had no candidate to match against.

Re-running on the same Broadleaf checkout with `--module common`
produces 294/947 risk_scores records with non-zero
`line_coverage` (and 294/959 in `coverage_baseline.json`). The
294-vs-653 split is real data: the 653 are files JaCoCo saw
without any test coverage; the 294 are files that had at least
one test. This is the truth, not a parser bug.

## Why Now

The 5/765 measurement is alarming on its face. Without a
regression test, future refactors of `_normalize_coverage_path`
could regress this in a way that's hard to spot (every Broadleaf
run that uses `--module admin` for both inventory and report
would look fine, but a cross-module report would silently
fail). Story 022 puts a fence around the existing behavior so
the next refactor can't quietly break it.

## Approach

The new helper `resolve_jacoco_paths(coverage_records, repo_root,
inventory)` in `test_factory/analyzers/coverage_normalizer.py`
provides a deterministic, side-effect-free rewrite from JaCoCo
form to inventory form. It walks the repo's `pom.xml` /
`build.gradle*` files to discover module roots, then tries each
combination of (module_root, layout, record_path) and picks the
first on-disk match.

This helper is **redundant** with `_normalize_coverage_path` in
the happy case — suffix-matching already handles the Maven
default layout. It exists as a safety net for:

- Repos where the on-disk file path uses a different layout
  (`src/main/kotlin`, `src/main/groovy`) than the coverage report
  expects.
- Empty inventories: when `coverage()` is called before
  `inventory()`, `inventory_paths` is `[]` and
  `_normalize_coverage_path` returns the path unchanged.
- Future refactors of the orchestrator that may move the join
  point.

The story does not require `orchestrator.score` to be changed
to call `resolve_jacoco_paths` (it would be a no-op for the
existing happy case). The helper is exposed for future use and
is pinned by unit tests.

## Acceptance Scenarios

1. **Single-module Maven repo: every record maps back to
   `<repo>/src/main/java/...`.**
   Given a single-module Maven repo with a real
   `target/site/jacoco/jacoco.xml` containing one package
   `org/example` and one sourcefile `Foo.java`
   When `resolve_jacoco_paths(records, repo)` runs
   Then the record's `path` is rewritten from
   `org/example/Foo.java` to
   `src/main/java/org/example/Foo.java`. (Pin: this is the case
   where `_normalize_coverage_path` already works via suffix
   matching; the new helper also works, and the test pins the
   new helper's contract.)

2. **Multi-module Maven repo: each package resolves to its
   module's source tree.**
   Given a multi-module Maven repo with packages in
   `common/src/main/java/...` and
   `admin/foo/src/main/java/...`
   When `resolve_jacoco_paths(records, repo)` runs
   Then a class in package `org/broadleafcommerce/common/...`
   maps to
   `common/src/main/java/org/broadleafcommerce/common/...`
   AND a class in package `org/broadleafcommerce/openadmin/...`
   maps to
   `admin/foo/src/main/java/org/broadleafcommerce/openadmin/...`.
   (Pin: this is the case that motivated story 022. With
   per-module poms on disk, the resolver finds both module
   roots and rewrites both records correctly.)

3. **Files JaCoCo did not see stay unmatched (and so stay at
   0.0 in risk_scores).**
   Given v2's inventory lists a file at `common/src/main/java/.../X.java`
   but the report's only `<sourcefile>` is in a different package
   When v2 ingests
   Then `X.java`'s `line_coverage` is unchanged (0.0 — the v2
   risk formula treats "no coverage data" as a full gap).

4. **Anonymous inner classes map back to the outer file.**
   Given a JaCoCo report has a class
   `org/broadleafcommerce/.../Foo$1` with
   `sourcefilename="Foo.java"`
   When v2 ingests
   Then the coverage counters for the inner class are merged into
   the outer file's record (JaCoCo emits a single
   `<sourcefile name="Foo.java">` block at the package level
   that includes lines for both the outer and inner class).

5. **A class with no `sourcefilename` falls back to a synthetic
   record.**
   Given a class `<class name="a/b/C"/>` with no
   `sourcefilename`
   When v2 ingests
   Then the record is emitted as
   `path = "a/b/C.java"` and `resolve_jacoco_paths` does not
   raise. (No on-disk resolution attempted; the path stays in
   the synthetic form.)

## Executable Test Mapping

`tests/test_022_v2_jacoco_path_matching.py` — 5 unit tests
covering scenarios 1-5. Uses `tmp_path` for an in-memory
multi-module Maven repo (with per-module `pom.xml` files) and
synthesizes minimal `jacoco.xml` reports. Pins the
`resolve_jacoco_paths` contract.

## Done Criteria

- New helper `resolve_jacoco_paths(coverage_records, repo_root,
  inventory=None)` in
  `test_factory/analyzers/coverage_normalizer.py`.
- Helper handles scenarios 1, 2, 3, 4, 5.
- New BDD test file `test_022_v2_jacoco_path_matching.py` with
  5 unit tests, all passing.
- Existing v2 tests pass (no behavior change; the helper is
  additive, not a replacement for
  `_normalize_coverage_path`).
- A regression note in `memory/2026-06-13.md` explaining that
  the 5/765 measurement on 2026-06-13 was caused by
  `--module admin` scoping the inventory, not by a parser bug,
  and that the 294/947 figure on 2026-06-13 is the correct
  baseline for the broadleaf-common module.

## Out of Scope (Future Stories)

- Wiring `resolve_jacoco_paths` into `orchestrator.score` as a
  fallback path (the happy case is already covered by
  `_normalize_coverage_path`; a fallback would be a
  belt-and-suspenders change for the empty-inventory case).
- Multi-language support (Kotlin, Scala, Groovy) beyond the
  candidate-layout heuristic in `_JACOCO_LAYOUTS`.
- Caching JaCoCo reports across runs.

## End-to-End Evidence (Broadleaf, 2026-06-13, post-fix)

```
mvn -pl common test jacoco:report          # 817 classes, real jacoco.xml
test-factory run --module common --out /tmp/v2-broadleaf-common
# risk_scores.json: 947 records; 294 have non-zero line_coverage
# coverage_baseline.json: 959 records; 294 have non-zero line_coverage
```

The 294-vs-653 split reflects real Broadleaf data: 294 source
files had at least one test exercise them, 653 had none. The
mapping from JaCoCo's class-name paths to v2's
`<module>/src/main/java/...` inventory paths is handled by
`orchestrator._normalize_coverage_path` (suffix matching)
without any change to story 022's helper.

## Follow-ups Surfaced by This Story (Not In Scope)

- The broadleaf-common module's 653 zero-coverage files are
  real risk. A future story should surface these as
  `test_gap_queue` work items with high priority (they have
  zero coverage and are likely high-traffic class files).
- The flaky `MvelHelperTest` from story 021's e2e run
  (1/94 failures under load) is still a Broadleaf issue and
  should be filed against the Broadleaf repo.
- A `--module auto` mode that runs `mvn test` on every module
  and ingests all reports would let v2 see real coverage for
  the whole repo, not just the `--module` scoped slice.
