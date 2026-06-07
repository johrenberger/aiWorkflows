# OpenClaw Prompt: Application Test Coverage Implementation

Use this prompt to run the coverage workflow against a GitHub repository.

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
