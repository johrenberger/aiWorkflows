# Application Test Coverage Validation

## Required Validation Gates

- [ ] **TC-VAL-1 [Repository Input]** GitHub URL captured and repository cloned/opened.
- [ ] **TC-VAL-2 [Runtime Metadata]** Branch, commit, working tree, and timestamp recorded.
- [ ] **TC-VAL-3 [Framework Detection]** Test framework and coverage tooling detected from evidence.
- [ ] **TC-VAL-4 [Baseline Tests]** Existing tests run or blocker documented.
- [ ] **TC-VAL-5 [Baseline Coverage]** Coverage run or blocker documented.
- [ ] **TC-VAL-6 [Eligible Files]** Eligible and excluded files classified with rationale.
- [ ] **TC-VAL-7 [Per-File Table]** Each eligible source file has baseline/final/status.
- [ ] **TC-VAL-8 [90% Target]** Each eligible source file reaches 90% or has blocker.
- [ ] **TC-VAL-9 [Test Quality]** Added tests follow AAA and deterministic design.
- [ ] **TC-VAL-10 [No Weakening]** Existing tests were not weakened to pass.
- [ ] **TC-VAL-11 [Focused Validation]** Changed-module tests pass or blocker recorded.
- [ ] **TC-VAL-12 [Full Validation]** Full suite/coverage run where feasible.
- [ ] **TC-VAL-13 [Ledger Complete]** `TODO_test-coverage.md` includes all required sections.
- [ ] **TC-VAL-14 [Pre-Flight]** If `ALLOW_DEPENDENCY_INSTALL=false`, the build/test commands used in phases 4-5 are pre-existing in the repo (no new tool installs). If install is required, it is recorded as `TC-BLK-PreFlight`.
- [ ] **TC-VAL-15 [Testability Classification]** When `ENABLE_TESTABILITY_CLASSIFICATION=true`, each source file has a testability label (testable / integration-only / **test-infrastructure** / generated / framework-boilerplate / jsp-view) recorded in the per-file table. `test-infrastructure` covers DataProviders, Spring @Configuration test beans, test doubles, and test-only interfaces. Generated, boilerplate, and test-infrastructure files are excluded with rationale.
- [ ] **TC-VAL-16 [Orchestration Boundaries]** If sub-agents were spawned, each one is limited to its declared role (discoverer / test-writer / coverage-manager). No sub-agent wrote directly to the canonical ledger or to files outside its scratch directory. The main agent's SHA-256 of the canonical ledger matches before and after each sub-agent's batch.
- [ ] **TC-VAL-17 [Environment Verified]** Phase 0.5 pre-flight completed. The required tools for the detected language stack (compiler, build tool, test runner) are on PATH at the correct version. Disk free, network reachability, and GitHub auth are all OK. SETUP.md is present in the artifacts directory. If any tool is missing, the workflow has a `TC-BLK-PreFlight` blocker with install commands.
- [ ] **TC-VAL-18 [Java + JaCoCo Verified]** For Java + Maven projects, the JaCoCo agent is properly attached during surefire test execution. `surefire.argLine` is set to a command-line override (`-Dsurefire.argLine='-javaagent:.../jacocoagent.jar=destfile=${project.basedir}/target/jacoco.exec ...'`) OR the POM uses `@{argLine}` late-binding. `target/jacoco.exec` exists after the test run, with size > 0. JDK ≥ 17, and `--add-opens` flags are present for Spring/Hibernate modules. See `workflows/shared/java-jacoco-patterns.md`.
- [ ] **TC-VAL-19 [Sub-Module Reactor Verified]** For Maven multi-module projects, the reactor includes the expected sub-modules (not just the parent POM). The build invocation is `mvn -f <parent>/pom.xml -am test` (NOT `-pl <parent>`). The reactor summary shows the expected number of sub-modules. The build duration is at least 30 sec (a sub-second BUILD SUCCESS indicates the parent-only failure mode). See `workflows/shared/sub-module-reactor.md`.
- [ ] **TC-VAL-20 [Per-Sub-Module Test Presence Reported]** For each sub-module in the reactor, the pre-flight reports the source file count and existing test file count. Sub-modules with 0 tests are flagged as `low-priority` or `out-of-scope` depending on user config. The pre-flight decision tree: (1) if user set `MODULE_LIST`, restrict to that list. (2) for each sub-module in scope, report test/source ratio. (3) if ratio < 1%, warn that coverage will be 0% for most classes. See `workflows/shared/sub-module-reactor.md`.
- [ ] **TC-VAL-21 [Coverage Provenance Recorded]** For each testable file with current coverage, the classification table records provenance: `direct` (test in same sub-module), `transitive` (test elsewhere), or `none`. This determines whether the test-writing strategy is EXTEND (direct) or ADD (transitive/none). See `workflows/shared/sub-module-reactor.md`.
- [ ] **TC-VAL-22 [v2 Analysis Consumed]** If `test-factory` was on PATH at run start, the artifacts directory contains `v2/v2_summary.md` AND the ledger cites at least 5 of the 13 v2 JSON outputs in evidence fields. The presence of `v2_summary.md` and at least 5 cited JSONs proves the LLM consumed the deterministic analysis instead of re-deriving it. If `test-factory` was not on PATH, this gate is satisfied by a `TC-BLK-V2NotInstalled` entry in the Blocker section.
- [ ] **TC-VAL-23 [No Re-Detection]** Each of TC-FRAMEWORK-1, TC-CKPT-5, TC-CKPT-7, and TC-CKPT-8 has an evidence field that cites a v2 JSON artifact (or, if v2 was unavailable, a documented `TC-BLK-V2NotInstalled`). If the LLM disagrees with any v2-derived value, the disagreement is recorded in TC-OBS-1 with the v2 path being disagreed with, and the LLM either fell back to the v2 value or skipped the file with `TC-BLK-V2Disagreement`. Re-deriving values without recording the disagreement is a failure of this gate.
- [ ] **TC-VAL-24 [v2 Re-Run After Each Batch]** After implementing each test batch (Phase 12), the workflow re-runs `workflows/shared/integrate-v2.sh` (with `--generate-coverage` if the pre-batch run used it) to produce a fresh `coverage_baseline.json`. The diff between the pre-batch and post-batch `coverage_baseline.json` is the evidence for `TC-VAL-RESULT-2 [Coverage Recheck]`. An empty diff means the batch did not move coverage and MUST be investigated before proceeding to Phase 15.
- [ ] **TC-VAL-25 [Ledger Co-Located With Project]** `TODO_test-coverage.md` is written at the root of the project being analyzed, not at the root of the input repository. For a single-project repository, the project root is the repository root. For a repository that contains the target project as a subdirectory, the project root is the smallest directory containing the project's source files (e.g. `skill-governance-pipeline/`). The chosen path is recorded in `TC-CTX-1 [Repository]` and matches the smallest common ancestor of all per-file coverage rows in the per-file table. If the ledger is found at the input repository root when a subpath project was analyzed, this gate fails with `TC-BLK-LedgerMisplaced`.

## Failure Handling

If validation fails, classify the failure:

- Baseline failure.
- New test failure.
- Environment failure.
- Coverage tooling failure.
- Production bug exposed.
- Timeout.
- Insufficient testability.
- Pre-flight (build/install prerequisite missing) — TC-BLK-PreFlight.
- Baseline timeout — TC-BLK-BaselineTimeout.
- Environment verification (tool missing, disk full, network down) — TC-BLK-PreFlight.
- Ledger written at wrong path (repo root instead of project root) — TC-BLK-LedgerMisplaced.

Record evidence and next action.
