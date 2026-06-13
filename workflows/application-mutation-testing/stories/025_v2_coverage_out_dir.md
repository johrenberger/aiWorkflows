# Story 025 — External `--coverage-out` for generated coverage (v2)

## Why

Story 020 flipped `test-factory run` to generate coverage by default
(via `discover_coverage_command`). The user-visible cost: the target
repo gets a `target/site/jacoco/jacoco.exec` (Java/Maven),
`coverage.json` (Python/pytest-cov), or `coverage-final.json` /
`lcov.info` (JS) written into it.

This is a real ergonomics problem:
- The target repo's working tree now has untracked coverage files
  (JaCoCo's `target/` is gitignored, but `coverage.json` is not).
- `git status` on the target repo shows the writes as untracked noise.
- The user can't tell "did *I* add this file?" from "did v2 add this?".
- For Broadleaf, JaCoCo writes into `target/site/jacoco/` *per module* —
  i.e. it touches 5+ directories. Even if the user is fine with it,
  cleaning up after a run is annoying.

The natural answer: tell v2 where the *generated* coverage should
land (separately from the *parsed* artifacts that already go in
`--out`).

## What's in this PR

1. **New CLI flag `--coverage-out DIR`** on `run` (only meaningful
   with `--generate-coverage` or when `run(generate_coverage=True)`
   is set). Defaults to the target repo (current behavior). When
   set, the orchestrator tells the adapter to redirect the build
   tool's output to `DIR`. For tools that don't support per-run
   redirection (e.g. Gradle with a fixed build script), the
   orchestrator copies the freshly-written reports to `DIR` after
   the run and leaves the target repo clean (or as clean as the
   build tool left it; .gitignored target/ dirs stay).

2. **Per-adapter support**:
   - **Java/Maven**: pass `-Djacoco.destFile=DIR/jacoco.exec` and
     `-Djacoco.reportDir=DIR` so the agent's `prepare-agent` writes
     to `DIR` and the `report` goal reads from there.
   - **Java/Gradle**: best-effort `jacocoTestReport { reports {
     xml.outputLocation = file(DIR) } }` is *not* settable from the
     command line, so use the post-run copy fallback.
   - **Python/pytest-cov**: substitute `DIR/coverage.json` and
     `DIR/coverage.xml` into the `--cov-report=json:...` /
     `xml:...` arguments.
   - **JS/jest-vitest**: substitute `DIR` into `--coverageDirectory`.

3. **Post-run copy fallback**: if the adapter's build tool doesn't
   honor the redirect (Gradle today, possibly others), the
   orchestrator does:
   ```
   pre = snapshot(report paths in repo, mtimes)
   run build tool in repo
   post = snapshot(report paths in repo, mtimes)
   new = {p for p in post if post[p] > pre.get(p, 0)}
   for p in new: shutil.copy2(p, DIR / p.name)
   ```
   This guarantees `DIR` always contains the new reports, even
   if the repo was written to. (The repo is still mutated, but
   only by the build tool, not by v2. The user's complaint was
   about v2's writes, which is what `DIR` solves.)

4. **New artifact `coverage_run_external.json`** under
   `<--coverage-out>/` (or under `--out/coverage_runs/` if
   `--coverage-out` is unset) with the same shape as the current
   `coverage_runs/generate.json` plus a `coverage_out_dir` field
   showing where the reports were actually written.

## Acceptance scenarios (BDD)

1. `test-factory run --generate-coverage --coverage-out /tmp/cov`
   on a Python repo writes `coverage.json` to `/tmp/cov/`, NOT to
   the repo root. `git status` in the repo shows no new files.
2. Same command on a Maven repo writes `jacoco.exec` to
   `/tmp/cov/`, NOT to `target/site/jacoco/` (Maven 0.8.11+ honors
   `-Djacoco.destFile`).
3. Same command on a Gradle repo: post-run copy fallback kicks in
   — repo still has the original `build/reports/jacoco/...` files
   (build tool's choice), but `DIR` ALSO has a copy.
4. `test-factory run --generate-coverage` (no `--coverage-out`)
   on a Maven repo still writes to `target/site/jacoco/...` —
   behavior unchanged (default = repo).
5. `coverage()` reads from `--coverage-out` first, falls back to
   the repo if not set. (User can run `coverage` later without
   `--coverage-out` and v2 will look in the repo. But the
   *generated* report from the latest run is always under
   `--coverage-out`.)
6. `--coverage-out` errors clearly if the path is not writable.

## Scope limits

- We do NOT add a "build in a copy of the repo" mode (--coverage-tmp).
  That would be cleaner for Gradle but is ~3x the implementation
  effort and disk I/O. Post-run copy is the pragmatic middle ground.
- We do NOT change the *parsed* artifact location (still
  `analysis-artifacts/coverage_baseline.json` under `--out`).
  `--coverage-out` is purely for the *raw* reports that the build
  tool wrote.
- We do NOT try to clean up the repo after the run. If
  `--coverage-out` is unset, the build tool's writes stay. The
  user is responsible for `.gitignore` / `git clean -fdx target`.

## End-to-end evidence (after this story)

- Maven: `mvn test -Djacoco.destFile=/tmp/cov/jacoco.exec
  -Djacoco.reportDir=/tmp/cov` lands `jacoco.exec` and
  `jacoco.xml` in `/tmp/cov/`. Repo `target/` is empty.
- Python: `pytest --cov --cov-report=json:/tmp/cov/coverage.json`
  lands `coverage.json` in `/tmp/cov/`. Repo `coverage.json` is
  absent.
- Gradle: build tool writes to `build/...` as usual. v2 copies
  to `/tmp/cov/`. Repo `build/...` has the originals.

## Tests

- 8 new BDD tests covering: Maven/Python redirect, Gradle
  post-run copy, default-unchanged, missing-dir error,
  `coverage()` falls back, artifact shape, CLI flag.

## Out of scope

- Multi-aggregate reports (e.g. merging 10 modules' JaCoCo into
  one). That's a separate story.
- Cleaning up the repo post-run.
- PIT setup (C3).
