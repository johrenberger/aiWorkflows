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
- [ ] **TC-VAL-16 [Orchestration Boundaries]** If sub-agents were spawned, each one is limited to its declared role (discoverer / test-writer / coverage-manager). No sub-agent wrote directly to the canonical ledger or to files outside its scratch directory. The main agent's SHA-256 of the canonical ledger matches before and after each sub-agent's batch.

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

Record evidence and next action.
