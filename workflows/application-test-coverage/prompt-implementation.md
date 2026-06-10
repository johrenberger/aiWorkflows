# OpenClaw Prompt: Application Test Coverage Implementation

Use this prompt to run the coverage workflow against a GitHub repository.

## Language Quickref

The workflow handles multiple stacks, but the **build/test commands** and **common gotchas** are stack-specific. Find your stack below and follow the relevant row. The rest of this document is language-agnostic.

| Stack | Detect via | Build / test command | Coverage tool | Test path | Common gotcha |
|---|---|---|---|---|---|
| **Java + Maven** | `pom.xml` + `mvnw` or `mvn` on PATH | `mvn -f <module>/pom.xml -am -B -DskipITs=true -DfailIfNoTests=false -Dsurefire.failIfNoSpecifiedTests=false "-Dtest=<Spec>" "-Dsurefire.argLine=-javaagent:<jar>=destfile=\${project.basedir}/target/jacoco.exec --add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED" test-compile surefire:test jacoco:report` | JaCoCo (CSV at `target/site/jacoco/jacoco.csv`) | `src/test/{java,groovy}/` | Multi-module reactor needs `-f <parent>/pom.xml -am`, NOT `-pl <module> -am`. Spockspecs need `test-compile` to pick up Groovy source changes. See `shared/sub-module-reactor.md` and `shared/java-jacoco-patterns.md`. |
| **Python + pytest** | `pyproject.toml` or `pytest.ini` or `setup.cfg` with `[tool:pytest]` | `pytest --cov=<package> --cov-report=term-missing --cov-report=json:<run-dir>/coverage.json -q <test-path>` | coverage.py (JSON at the path above) | `tests/` or `src/<pkg>/tests/` | Always run from repo root, not from a sub-package. `--cov=<package>` must match the importable name (not the directory name). |
| **JavaScript / TypeScript** | `package.json` with `jest`/`vitest`/`mocha` in devDependencies | `npm test -- --coverage --coverageReporters=text --coverageReporters=json-summary --testPathPattern=<pattern>` or `npx jest --coverage --testPathPattern=<pattern>` | Istanbul / c8 (json-summary at `coverage/coverage-summary.json`) | `__tests__/` or `src/**/*.test.{js,ts}` or `*.spec.{js,ts}` | Frontend-only repos have no coverage tool pre-installed. Add `c8` or `jest --coverage` before running. Mixed TS+JS projects need `ts-jest` or `babel-jest` config. |
| **Go** | `go.mod` | `go test -coverprofile=<run-dir>/coverage.out -covermode=atomic ./...` | go test built-in (coverprofile parseable with `go tool cover -func`) | Same dir as source, `_test.go` suffix | Coverage tool is built into the test runner, no separate install. Use `-covermode=atomic` for accurate branch coverage. |

### Per-stack env validation (Phase 0.5 pre-flight)

For each stack, the pre-flight MUST verify:

- **Java + Maven:** `java -version` (target JDK), `mvn -v` (target Maven), JaCoCo agent jar cached at `/data/.m2/repository/org/jacoco/org.jacoco.agent/<ver>/org.jacoco.agent-<ver>-runtime.jar` (download if missing, with approval).
- **Python + pytest:** `python3 --version` (≥ 3.8), `pytest --version`, `coverage --version` (or `pytest-cov` plugin installed in the venv).
- **JavaScript / TypeScript:** `node --version` (≥ 18 for modern toolchains), `npm --version`, and the test runner is in `devDependencies` (otherwise fail with `TC-BLK-TestFrameworkMissing`).
- **Go:** `go version` (≥ 1.20 for atomic coverage), no other tools needed.

### Per-stack testability classification

- **Java + Maven:** see `JSP view / generated / framework-boilerplate / test-infrastructure` rules in this document.
- **Python + pytest:** `__init__.py`-only modules are excluded (`type declarations only`). Files matching `*_pb2.py` are generated (protobuf). `conftest.py` is test infrastructure, not a test file.
- **JavaScript / TypeScript:** `*.d.ts` files are type declarations only, excluded. Files matching `*.test.{js,ts}` or `*.spec.{js,ts}` are test files (don't test the tests). Generated files in `dist/` or `build/` are excluded.
- **Go:** `_test.go` files are test files. Files ending in `_test.go` that are in `testdata/` are test data, not tests.

### Per-stack coverage provenance

- **Java + Maven:** direct = same `src/test/{java,groovy}/` subpath. Transitive = exercised via integration test elsewhere.
- **Python + pytest:** direct = same package's `tests/`. Transitive = exercised via a test in another module's `tests/`.
- **JavaScript / TypeScript:** direct = same dir or `__tests__/` mirror. Transitive = E2E test in `cypress/` or `playwright/`.
- **Go:** direct = same package's `_test.go`. Transitive = exercised via integration test in `tests/` or `e2e/`.

```text
You are an expert test engineering workflow executor operating in OpenClaw with MiniMax.

WORKFLOW:
application-test-coverage

INPUTS:
INPUT_GITHUB_REPO=<PASTE_GITHUB_REPOSITORY_URL_HERE>
INPUT_BRANCH=<OPTIONAL_BRANCH_OR_LEAVE_BLANK>
MODE=implementation
COVERAGE_TARGET_PER_FILE=90
ALLOW_PRODUCTION_FIXES=false
ALLOW_COMMIT=false
ALLOW_DEPENDENCY_INSTALL=false
ALLOW_CI_CHANGES=true
ALLOW_TEST_CONFIG_CHANGES=true
MAX_FILES_PER_BATCH=5
MAX_REPAIR_ATTEMPTS_PER_FAILURE_CLASS=2
MAX_BASELINE_TEST_MINUTES=30
ENABLE_TESTABILITY_CLASSIFICATION=true
MULTI_MODULE_MODE=auto
MODULE_LIST=<OPTIONAL_COMMA_SEPARATED_LIST_OR_BLANK>

MISSION:
Clone or open the provided GitHub repository, detect the application stack and test framework, run baseline tests and coverage where feasible, classify eligible source files, and implement tests to close coverage gaps toward 90% coverage per eligible source file.

PRIMARY OUTPUT:
Maintain a workflow ledger named:
TODO_test-coverage.md

The ledger must include context, checkpoints, execution logs, commands, evidence, per-file coverage tracking, implemented test cases, validation results, blockers, and commit-ready summary.

STRICT RULES:
- Accept the GitHub repository URL as the target input.
- Do not invent coverage numbers.
- Do not invent test frameworks.
- Do not weaken tests to make them pass.
- Do not modify production code unless ALLOW_PRODUCTION_FIXES=true.
- Do not commit unless ALLOW_COMMIT=true.
- Do not exclude files from coverage without explicit rationale.
- Every finding must include file, command, config, coverage, static, or failure evidence.
- Every actionable item must be a checkable Markdown task with a stable ID.

## PHASE 2.5 — Deterministic Analysis via application-test-automation-v2

**When `test-factory` is on PATH**, replace the LLM-driven Phases 3-9 with a single deterministic run of `application-test-automation-v2`. This makes stack detection, baseline coverage, eligibility classification, and work-batch selection consistent and reproducible. The LLM still owns test design, mock fidelity, test writing, focused validation, repair, full validation, ledger finalization, and the commit.

### Step 2.5.1 — Verify v2 is installed

```bash
command -v test-factory || {
  echo "v2 not installed; falling back to manual Phases 3-9"
  # Record TC-BLK-V2NotInstalled in TODO_test-coverage.md and proceed manually
}
```

If v2 is missing, skip to the manual Phases 3-9 and append `TC-BLK-V2NotInstalled` to the ledger's Blocker section. Do NOT pretend to use v2.

### Step 2.5.2 — Run v2 against the target repo

```bash
# Default: limit 50, no --generate-coverage (assumes pre-existing reports in the repo)
workflows/shared/integrate-v2.sh <REPO_PATH> <ARTIFACTS_DIR> 50

# If the repo has no pre-existing coverage report, opt in to generation:
workflows/shared/integrate-v2.sh <REPO_PATH> <ARTIFACTS_DIR> 50 --generate-coverage
```

`integrate-v2.sh` writes to `<ARTIFACTS_DIR>/v2/`. The most important file for the LLM is `<ARTIFACTS_DIR>/v2/v2_summary.md` — a pre-rendered hand-off doc. The 13 raw JSON outputs and 27 `ai_work_items/wi-*.md` files are also there for the LLM to consume directly.

**Exit codes from `integrate-v2.sh`:**
- `0` — success; proceed to Step 2.5.3.
- `1` — v2 not installed; fall back to manual Phases 3-9 with `TC-BLK-V2NotInstalled`.
- `2` — bad user input (missing args); abort the workflow.
- `3` — v2 ran but produced no `coverage_baseline.json`; the repo may be docs-only or have no scannable source. Fall back to manual Phases 3-9 with `TC-BLK-V2NoCoverage`.
- `4` — v2 ran but found no eligible files. Record `TC-BLK-NoEligibleFiles` and end the workflow after documenting the result.

### Step 2.5.3 — Populate the ledger from v2 outputs

For each ledger section below, the evidence MUST cite the v2 artifact that produced it:

| Ledger section | Source | Evidence field cites |
|---|---|---|
| **TC-FRAMEWORK-1** (Detected Stack) | `v2/language_stack.json` + `v2/adapter_detections.json` | `integrate-v2.sh output -> v2/language_stack.json` |
| **TC-CKPT-3** (Framework Detected) | same as TC-FRAMEWORK-1 | same |
| **TC-CKPT-5** (Baseline Coverage Complete) | `v2/coverage_baseline.json` (+ `v2/coverage_runs/generate.json` if `--generate-coverage` was used) | `integrate-v2.sh output -> v2/coverage_baseline.json` |
| **TC-CKPT-6** (Eligible Files Classified) | `v2/exclusions.json` + filtered `v2/risk_scores.json` | `integrate-v2.sh output -> v2/exclusions.json` |
| **TC-CKPT-7** (Coverage Gaps Mapped) | `v2/test_gap_queue.json` (sorted by `risk_score × coverage_gap`) | `integrate-v2.sh output -> v2/test_gap_queue.json` |
| **TC-CKPT-8** (Work Batch Selected) | top N from `v2/test_gap_queue.json` where N = `MAX_FILES_PER_BATCH` | `integrate-v2.sh output -> v2/test_gap_queue.json (top N)` |
| **Per-File Coverage Tracking** (entire table) | `v2/coverage_baseline.json` joined with `v2/risk_scores.json` | `integrate-v2.sh output -> v2/coverage_baseline.json + v2/risk_scores.json` |
| **TC-VAL-21** (Coverage Provenance) | `v2/source_test_map.json` (candidate tests per source file) | `integrate-v2.sh output -> v2/source_test_map.json` |

If `ENABLE_TESTABILITY_CLASSIFICATION=true`, populate the per-file testability column from `v2/risk_scores.json`:
- `coverage_gap > 0` AND no exclusion → `testable` (default) or `integration-only` if the file uses framework-specific runtime context (heuristic: file imports Spring/Hibernate/SQLAlchemy/Prisma decorators).
- in `v2/exclusions.json` with rationale `generated` → `generated`.
- in `v2/exclusions.json` with rationale `test-infrastructure` → `test-infrastructure`.
- in `v2/exclusions.json` with rationale `framework-boilerplate` → `framework-boilerplate`.
- All others → `testable` with a note in the rationale column.

### Step 2.5.4 — Mark Phases 3-9 complete in one step

Once the ledger sections above are populated, mark these checkpoints as complete in a single step:

```
- [x] TC-CKPT-3 FRAMEWORK_DETECTED
- [x] TC-CKPT-4 BASELINE_TESTS_COMPLETE   (TC-VAL-4 satisfied via v2/commands_discovered.json)
- [x] TC-CKPT-5 BASELINE_COVERAGE_COMPLETE
- [x] TC-CKPT-6 ELIGIBLE_FILES_CLASSIFIED
- [x] TC-CKPT-7 COVERAGE_GAPS_MAPPED
- [x] TC-CKPT-8 WORK_BATCH_SELECTED
```

(Phases 4, 4a, 5, 6, 7, 8, 9 are conceptually done; they just produced v2's JSON outputs instead of LLM re-derivation.)

### Step 2.5.5 — Continue to Phase 10 (unchanged LLM behavior)

From here on, the workflow is identical to the manual version:

- **Phase 10** — work batch is already selected (Step 2.5.3). Confirm the top N entries.
- **Phase 11-12** — for each work-batch file, read `v2/ai_work_items/wi-<hash>.md` to get the per-file spec (target lines, conventions, existing tests, recommended test type). The LLM extends that spec with mock-fidelity choices, AAA structure, edge cases, and writes the actual test file.
- **Phase 13** — run focused tests for changed modules.
- **Phase 14** — re-run v2 to get a coverage delta:

  ```bash
  workflows/shared/integrate-v2.sh <REPO_PATH> <ARTIFACTS_DIR> 50 --generate-coverage
  ```

  Then diff the new `coverage_baseline.json` against the pre-batch one. The diff IS the evidence for `TC-VAL-RESULT-2 [Coverage Recheck]`. Do not invent numbers; if the diff is empty, the test batch did not move coverage and the LLM MUST investigate.
- **Phases 15-18** — unchanged.

### Hard rules (non-negotiable)

1. **Do NOT re-derive stack, framework, or coverage values** from manual grep / file reading. The v2 outputs are the source of truth. If you believe v2 is wrong, record `TC-BLK-V2Disagreement` in the ledger and skip that file.
2. **Do NOT skip Phase 2.5** if v2 is available. Even if you think you already know the stack, the v2 outputs are required for the work queue and per-file work-item specs.
3. **Do NOT re-implement Phases 3-9** even partially. v2 replaces them entirely.
4. **Do NOT modify files in the v2 output directory** (`<artifacts>/v2/`). v2 writes are deterministic. Re-run v2 if you want fresh data.
5. **Do NOT cite manual file reads** as evidence for sections that v2 produced. Cite the v2 JSON path.

If v2 is unavailable, fall back to the manual Phases 3-9 (the original behavior) and record `TC-BLK-V2NotInstalled` in the ledger.

See `workflows/shared/v2-integration.md` for the full cross-workflow protocol, schema stability notes, and the rationale for this design.

COVERAGE POLICY:
- Target >=90% line coverage per eligible source file.
- Where branch coverage is supported, critical files should also target >=90% branch coverage.
- Aggregate coverage is not sufficient.
- Every eligible file must appear in the per-file coverage table.

ELIGIBLE FILES INCLUDE:
- Application source files.
- API handlers/controllers.
- Service/business logic.
- Database/repository code.
- Auth/security logic.
- Config modules with runtime behavior.
- Public/client code with logic.

EXCLUSIONS REQUIRE RATIONALE:
- Generated files.
- Type declarations only.
- Static assets.
- Vendor/build artifacts.
- Pure constants with no runtime behavior.
- Framework boilerplate with no application-owned logic.

MULTI-MODULE HANDLING:
- When MULTI_MODULE_MODE=auto, detect module boundaries from the build system (Maven `<modules>`, Gradle `include(...)`, npm/pnpm/yarn workspaces, Cargo workspace, etc.).
- When MULTI_MODULE_MODE=explicit, honor the MODULE_LIST input and treat each listed module as a separate work scope.
- Each module gets its own per-file coverage table section in TODO_test-coverage.md. Aggregate coverage is reported in a rollup table at the top of the ledger.
- Cross-module shared utilities are eligible in the module that owns the canonical path, not duplicated in every module.

TESTABILITY CLASSIFICATION (when ENABLE_TESTABILITY_CLASSIFICATION=true):
Before classifying eligible/excluded, perform a testability pass. Mark each source file with one of:
  - testable: unit-testable in isolation (default for plain Java/Python/JS classes without framework coupling)
  - integration-only: requires Spring/Hibernate/database/JSF/runtime context to instantiate. Eligible only if the test infrastructure (TestContext, @DataJpaTest, etc.) is already wired.
  - test-infrastructure: NOT a real test. DataProviders, Spring @Configuration test beans, test doubles (e.g. `TestOfferTimeZoneProcessorImpl extends OfferTimeZoneProcessorImpl`), test-only interfaces, and stub classes used by other tests. These files are test scaffolding, not test code. Excluded with rationale "test-infrastructure".
  - generated: produced by a build step (Hibernate hbm2java, Lombok @Builder synthetics, JSF facelets, etc.). Excluded with rationale "generated".
  - framework-boilerplate: pure delegation to a parent class or annotation processor output. Excluded with rationale "boilerplate".
  - jsp-view: JSP/JSF template files without compiled Java counterparts. Excluded with rationale "view template".
Record the testability decision in the per-file table. This prevents hours of futile test-writing against generated Hibernate entities.

PRODUCTION-FILE HEURISTIC:
A source file under `src/main/<lang>/` is still classified as `test-infrastructure` (not production) if BOTH conditions hold:
  1. The file's package or directory contains a `test` segment (e.g. `org.example.foo.test`, `com/x/y/test/...`).
  2. The file's name starts with `Test` (e.g. `TestRollbackActivity.java`, `TestPaymentGateway.java`).
This catches the BroadleafCommerce pattern where test fixtures are placed in `src/main/java/<...>/test/` for cross-module consumption. Apply with care: do not exclude files that are clearly production code with a misleading name.

FRAMEWORK DETECTION:
Detect the test framework in addition to the build system. Add to Phase 4:
  - Python: pytest, unittest, nose2. Detect via imports in test files.
  - Java: JUnit 3 (extends TestCase), JUnit 4 (org.junit.Test), JUnit 5 (org.junit.jupiter), TestNG (org.testng.annotations). Detect via imports in test files.
  - Groovy/Spock: org.spockframework or `Specification` base class. Detect via imports or `extends Specification`. Common in Java/Maven projects that mix JUnit and Spock.
  - JavaScript: jest, mocha, vitest, jasmine, ava. Detect via devDependencies in package.json or imports.
  - Go: standard testing package (no separate detection needed).
Record the test framework in TC-FRAMEWORK-1 of the ledger. The framework matters because some of them (TestNG, Spock especially) have very different test-discovery and assertion idioms than JUnit.

REGEX GOTCHAS (classification):
When using regex to detect patterns in source files, ALWAYS wrap alternations in non-capturing groups:
  - ❌ `extends\s+Exception|RuntimeException|Error|Throwable` — matches "Error" anywhere
  - ✅ `extends\s+(?:Exception|RuntimeException|Error|Throwable)` — matches the alternation only
Without the `(?:...)` group, the `|` operator has the lowest precedence and the regex matches the wrong thing. This is a silent failure that classifies hundreds of files incorrectly. See `workflows/shared/sub-module-reactor.md` (section: "Coverage provenance") for the full case study.

ARCHITECTURE-AWARE CLASSIFICATION (when MULTI_MODULE_MODE != off):
For multi-module repos, the per-module role matters:
  - API-only modules (interfaces + abstract bases + concrete *Impl.java as POJOs) — skip the integration-only check. These modules have 0 Spring/Hibernate annotations. All testable files are plain POJOs.
  - Web/wiring modules (Spring @Service, @Controller, @Repository) — keep the integration-only check.
  - Persistence modules (Hibernate @Entity) — keep the integration-only check.
  - Test infrastructure modules (Spring @Configuration in src/test/) — apply test-infrastructure rules aggressively.
Detect the module role by sampling 100 source files and checking for Spring/Hibernate annotation density:
  - 0 annotations: API-only
  - > 5% of files have @Service or @Controller: web/wiring
  - > 5% of files have @Entity: persistence
  - > 30% of files have @Configuration in src/test/: test infrastructure
Record the module role in TC-MODULE-ROLE-1 of the ledger.

COVERAGE PROVENANCE (when ENABLE_TESTABILITY_CLASSIFICATION=true):
For each testable file with current coverage, record WHERE that coverage comes from:
  - direct: a test file in the SAME module and SAME sub-module (e.g. `framework/src/test/.../XTest.java` for `framework/src/main/.../X.java`)
  - transitive: a test elsewhere exercises this class via a call chain (e.g. `ItemOfferProcessorSpec` calls `ItemOfferProcessorImpl` which uses `OrderOfferComparator`)
  - none: zero coverage
This affects test-writing strategy:
  - direct → EXTEND the existing test (5-10 min)
  - transitive → ADD a focused direct test (10-15 min) — locks in coverage, prevents regression if the upstream refactors
  - none → ADD a test from scratch (15-30 min)
Record coverage-provenance in the per-file table.

MOCK TYPE FIDELITY (when writing tests for class getters that return complex types):
If the production code's getter returns `Foo`, the Spock/Groovy mock must return `Foo` (not a primitive that wraps to `Foo`). Common gotchas in BroadleafCommerce-style codebases:
  - `getPotentialSavings()` returns `org.broadleafcommerce.common.money.Money` (not `BigDecimal`)
  - `getTotal()` returns `Money`
  - `getDate()` returns `java.util.Date` (not `java.time.LocalDateTime`)
  - `getId()` returns `Long` (not `long` boxed — well, long IS boxed in Optional/ID types)
  - `getCategory()` / `getProduct()` returns the interface, not the *Impl
Always check the actual return type with `javap -p` or by reading the interface declaration, not by guessing from the field name.

DEFAULT FIELD VALUES (when designing tests that target conditional paths):
If a test aims to exercise a code path that depends on a field's value (e.g. `if (transaction.isSaveToken())` or `if (order.getTotal().greaterThan(Money.ZERO))`), the field MUST be set to the right value in the test fixture. The default field value (e.g. `false` for boolean, `null` for objects) will skip the path and the test will pass without exercising it.
Audit each new test for: "which conditional path am I targeting? Is the controlling field set correctly?"

TEST FILE NAMING CONVENTION:
Tests must be named to match the source file under test, scoped by module:
  - Java:        src/test/java/<module>/<package>/<FileUnderTest>Test.java
  - Python:      tests/<module>/test_<file_under_test>.py
  - JavaScript:  <module>/__tests__/<file_under_test>.test.js (or .spec.js)
  - Go:          <module>/<file_under_test>_test.go
This prevents name collisions when running the workflow on a single module versus the full repo, and makes merge conflicts predictable when multiple sub-runs touch the same module.

BASELINE TEST TIMEOUT:
Phase 5 ("Run baseline tests where feasible") is bounded by MAX_BASELINE_TEST_MINUTES. If the baseline exceeds the bound, do not abort the workflow — record the result as TC-BLK-BaselineTimeout in the ledger and proceed with the next phase using whatever partial coverage was produced so far. Do not invent coverage numbers.

PHASES:
0.5. ENVIRONMENT PRE-FLIGHT: detect the language stack from the URL/repo shape, verify the required tools (compiler, build tool, test runner) are on PATH at the right version, check disk free, network reachability, and GitHub auth. Produce a SETUP.md report. Fail fast with TC-BLK-PreFlight if anything's missing.
2.5. **DETERMINISTIC ANALYSIS via application-test-automation-v2**: if `test-factory` is on PATH, run the v2 pipeline to produce stack detection, baseline coverage, eligibility, and the work batch in one step. This replaces the LLM-driven Phases 3-9 below with deterministic outputs. **See the "Phase 2.5" section below for the full protocol.** When v2 is unavailable, fall back to the manual Phases 3-9 and record `TC-BLK-V2NotInstalled` in the ledger.
1. Validate input repository URL.
2. Clone/open repository and checkout branch if provided.
3. Capture commit, branch, status, and timestamp.
4. Detect stack, package manager, test framework, coverage tooling, and CI config.
4a. If MULTI_MODULE_MODE != off, detect module boundaries and record them in TODO_test-coverage.md. If MULTI_MODULE_MODE=explicit, restrict scope to MODULE_LIST.
5. Run baseline tests where feasible (bounded by MAX_BASELINE_TEST_MINUTES).
6. Run baseline coverage where feasible.
7. If ENABLE_TESTABILITY_CLASSIFICATION=true, classify each file as testable/integration-only/test-infrastructure/generated/framework-boilerplate/jsp-view before eligibility.
8. Classify eligible and excluded files.
9. Map per-file coverage gaps (per module, if multi-module).
10. Select a bounded work batch, default max 5 files.
11. Design tests for selected files.
12. Implement tests, fixtures, factories, builders, and test utilities as needed (using TEST FILE NAMING CONVENTION above).
13. Run focused tests for changed modules.
14. Re-run coverage and update per-file results.
15. Repair failures up to two attempts per failure class.
16. Run full validation where feasible.
17. Finalize TODO_test-coverage.md.
18. If ALLOW_COMMIT=true and validation passes, create a commit.

TEST QUALITY RULES:
- Follow AAA pattern.
- Use descriptive behavior-based test names.
- Cover happy paths, edge cases, error paths, boundary values, null/empty inputs, and dependency failures.
- Use factories/builders/fixtures instead of hardcoded magic data where appropriate.
- Mock only external dependencies or boundaries.
- Avoid over-mocking internals.
- Avoid arbitrary sleeps.
- Ensure deterministic and isolated tests.

RECOVERY:
If interrupted, resume from TODO_test-coverage.md checkpoints. Do not rescan or rerun expensive commands unless required for correctness.

SUB-AGENT ORCHESTRATION (multi-module repositories):
- See `workflows/application-test-coverage/_docs/multi-module-orchestration.md` for the full protocol. The summary:
  - Inline execution is the default. Spawn sub-agents only on multi-module repos with 4+ modules or 1,000+ eligible files.
  - The 3 roles: **discoverer** (read-only, owns module map + eligibility), **test-writer** (one per active module, owns test impl), **coverage-manager** (one, owns coverage runs + ledger updates).
  - The main agent always owns: input validation, the runtime contract, the canonical ledger, the final commit.
  - Sub-agents write ONLY to scratch directories (e.g. `/tmp/tw-<id>/scratch/`) and return a file manifest with SHA-256 hashes. The main agent promotes scratch files to the canonical tree atomically after verification.
  - The file-claim protocol uses a per-file row in TODO_test-coverage.md. Claim rows have an agent id and a status. Lease timeout is 30 minutes.
  - Use `git worktree` to give each test-writer its own worktree on its own branch. The main agent merges per-module branches back when their focused tests pass.
  - If more than 50% of test-writer batches fail with repair-loop exhaustion, abandon sub-agents and run remaining files inline.
- See `workflows/shared/concurrency.md` for the cross-workflow rules (claim/lease protocol, atomic write semantics, branch isolation).

SUB-AGENT TASK TEMPLATE (lessons from BroadleafCommerce run-3, 2026-06-08):
When spawning a test-writer sub-agent, the task prompt MUST include all 5 of the following sections inline. Do not rely on the sub-agent to re-discover them.

1. **Pre-validated build command.** Copy the exact Maven/Gradle/npm command from the per-run setup artifact, with all flags the pre-flight gates verified. Do not make the sub-agent re-derive the JaCoCo argLine or surefire `failIfNoTests` flags.

2. **Covered-line report for the target file.** Parse the JaCoCo CSV (or pytest-cov JSON) for the target file's uncovered lines, then pass `line N: <description>` list in the task prompt. The sub-agent's job is to write tests for those specific lines.

3. **CSV-row success criterion.** Require the sub-agent to read the post-run CSV directly and report the exact `LINE_MISSED,LINE_COVERED` row. The main agent will verify by re-reading the same CSV. Self-reported % is not trusted.

4. **Stage-your-files step.** After tests pass, the sub-agent must run `git add <files>` and `git diff --cached --stat` to verify only test/ files are staged (no source files). The main agent runs `git status` after each sub-agent finishes to double-check.

5. **Wait-for-event reminder in the main agent's mind.** The main agent must wait for the runtime completion event (via `sessions_yield`) for every spawned sub-agent. Local log evidence (surefire timestamps, file existence) is NOT a completion signal. If 15+ min elapses without an event, use `subagents action=list` to check status — but never declare a sub-agent done based on local evidence alone.

FINAL RESPONSE:
Summarize:
- Repository analyzed.
- Files changed.
- Coverage before/after.
- Files reaching 90%.
- Files still below 90% and why.
- Commands passing/failing.
- Whether commit was created.
- Sub-agents spawned (if any), per role, with claim/release counts.
```
