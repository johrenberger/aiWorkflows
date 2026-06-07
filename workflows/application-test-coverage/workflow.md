# Application Test Coverage Workflow

## Objective

Close application test coverage gaps by implementing deterministic, maintainable tests until each eligible source file reaches at least 90% coverage, or until an evidence-backed blocker prevents completion.

## Inputs

```text
INPUT_GITHUB_REPO=<github-url>
INPUT_BRANCH=<optional branch>
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
MODULE_LIST=<optional comma-separated list>
```

## Multi-Module Repositories

For repositories with a multi-module build (Maven `<modules>`, Gradle `include(...)`, npm workspaces, Cargo workspace), `MULTI_MODULE_MODE=auto` is the default. The workflow:

1. **Detects module boundaries** from the build system in Phase 3a.
2. **Scopes each per-file coverage table** to a module section in `TODO_test-coverage.md`.
3. **Reports aggregate coverage** in a rollup table at the top of the ledger.
4. **Does not duplicate** cross-module shared utilities — they appear once, under the module that owns the canonical path.

Use `MULTI_MODULE_MODE=explicit` with `MODULE_LIST=core,common` to restrict the run to a subset of modules. This is the recommended first run on a large repository — it bounds scope and lets you validate the orchestration before expanding.

`MULTI_MODULE_MODE=off` reverts to the single-scope behavior of earlier versions.

## Environment Pre-Flight

Before any work begins (Phase 0.5), the workflow verifies the runtime environment. See [`workflows/shared/environment-pre-flight.md`](../shared/environment-pre-flight.md) for the full rules.

The pre-flight detects the language stack from the URL or repo shape, then verifies the required tools for that stack are on PATH at the correct version. It fails fast with `TC-BLK-PreFlight` if anything is missing, producing a `SETUP.md` report with install commands.

**Why this matters:** without the pre-flight, the agent tries to run a missing tool (e.g. `mvn` for a Java/Maven repo) and either silently fails or starts a 30+ min install. The pre-flight is a 30-second check that prevents hours of wasted work.

## Java + Maven Specifics

For Java + Maven projects, additional checks are required:

- **JaCoCo agent attachment** — see [`workflows/shared/java-jacoco-patterns.md`](../shared/java-jacoco-patterns.md). The most common failure: `<argLine>${surefire.argLine}</argLine>` evaluates at parse time, before `prepare-agent` runs. The agent is never attached, and `target/jacoco.exec` doesn't exist.
- **Multi-module reactor** — see [`workflows/shared/sub-module-reactor.md`](../shared/sub-module-reactor.md). The most common failure: `mvn -pl parent -am test` only builds the parent POM, not its sub-modules. The correct invocation is `mvn -f parent/pom.xml -am test`.

These two runbooks cover the 3 most common silent failures when running coverage on a Java + Maven project.

## Phases

### Phase 0 — Input Validation

- Validate `INPUT_GITHUB_REPO` exists.
- Validate URL format.
- Capture optional branch.
- Capture workflow config values.

### Phase 0.5 — Environment Pre-Flight

- Detect language stack from the URL or repo shape.
- Verify required tools are on PATH at the correct version (see `workflows/shared/environment-pre-flight.md`).
- Check disk free, network reachability, GitHub auth.
- Generate `SETUP.md` with environment state and install commands.
- Fail fast with `TC-BLK-PreFlight` if anything is missing.

### Phase 1 — Clone / Open Repository

- Clone the repo if not present.
- Checkout branch if provided.
- Capture commit hash and working tree status.

### Phase 2 — Runtime Contract

- Create/update `TODO_test-coverage.md`.
- Record repo metadata.
- Record workflow settings.
- Add checkpoints.

### Phase 3 — Stack and Test Framework Detection

Detect from config and files:

- Language stack.
- Package manager.
- Test framework.
- Coverage tooling.
- CI workflows.
- Build system module layout (if multi-module).

### Phase 3a — Multi-Module Scope Detection (when MULTI_MODULE_MODE != off)

- Detect module boundaries from the build system.
- If `MULTI_MODULE_MODE=explicit`, validate that `MODULE_LIST` matches actual modules.
- Record module list and per-module file count in the ledger.
- Restrict subsequent phases to the active module scope.

### Phase 3b — Testability Pre-Classification (when ENABLE_TESTABILITY_CLASSIFICATION=true)

For each source file, label it as one of:

- testable
- integration-only
- generated
- framework-boilerplate
- jsp-view

Record in the per-file table. Generated/boilerplate/jsp-view files are excluded with rationale.

### Phase 4 — Baseline Test Execution

Run existing tests when feasible, bounded by `MAX_BASELINE_TEST_MINUTES`.

If baseline tests fail:

- Classify the failure.
- Record evidence.
- Do not hide or weaken failures.
- Continue only if safe.

### Phase 5 — Baseline Coverage Execution

Run coverage command from project config or framework convention.

Do not invent coverage values.

### Phase 6 — Eligible File Classification

Classify source files as:

- Eligible.
- Excluded.
- Blocked.

Every exclusion requires rationale.

### Phase 7 — Per-File Coverage Gap Mapping

Create a table:

```markdown
| File | Baseline | Target | Final | Status | Notes |
|---|---:|---:|---:|---|---|
```

Target for every eligible file:

```text
>=90% line coverage
```

Where branch coverage is supported, critical files should also target:

```text
>=90% branch coverage
```

### Phase 8 — Work Batch Selection

Prioritize:

1. High-risk files below 50%.
2. Files with 0% coverage.
3. Critical path files.
4. Branch-heavy logic.
5. Files near 90% needing small additions.

Default batch limit:

```text
MAX_FILES_PER_BATCH=5
```

### Phase 9 — Test Design

For each selected file, define:

- Behaviors.
- Happy paths.
- Edge cases.
- Error paths.
- Boundary values.
- Fixtures/factories/builders.
- Mocking strategy.
- Determinism strategy.

### Phase 10 — Test Implementation

Implement tests and supporting test utilities.

Allowed by default:

- Test files.
- Fixtures.
- Factories/builders.
- Test utilities.
- Test config.
- Coverage config.
- CI test/coverage commands.

Production code changes are prohibited unless `ALLOW_PRODUCTION_FIXES=true`.

### Phase 11 — Focused Validation

Run tests for changed modules first.

### Phase 12 — Per-File Coverage Recheck

Re-run coverage.

Update per-file coverage table.

### Phase 13 — Repair Loop

Repair failures up to:

```text
MAX_REPAIR_ATTEMPTS_PER_FAILURE_CLASS=2
```

Then document blocker.

### Phase 14 — Full Validation

Run broader validation when feasible:

- Full test suite.
- Coverage command.
- Lint/typecheck if configured.
- CI-equivalent command if known.

### Phase 15 — Ledger Finalization

Finalize `TODO_test-coverage.md` with:

- Commands run.
- Files changed.
- Coverage before/after.
- Remaining gaps.
- Blockers.
- Commit-ready summary.

### Phase 16 — Optional Commit

If `ALLOW_COMMIT=true` and validation passes:

```bash
git add <changed files>
git commit -m "test: improve per-file coverage"
```
