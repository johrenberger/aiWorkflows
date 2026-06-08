# Component Test Generation Workflow

## Objective

Consume the analysis produced by **`component-test-analysis`** and **generate concrete, runnable test files** that close the prioritized gap backlog. The workflow is **project-agnostic**: it works against any GitHub repo where the analysis workflow has run. It detects the language, framework, build system, and test framework from the repo itself (re-derived, not trusted from the analysis), then emits tests in the project's idiomatic style and folder layout.

This workflow is the **build** counterpart to the analysis workflow's **spec**. Where the analysis answers "what's missing?", this workflow answers "produce the tests that cover it."

The workflow answers five questions:

1. What does this repo actually use? (language, framework, build, test framework — re-detected, not inherited)
2. Which gaps from the backlog should this run tackle? (priority, risk, scope filters)
3. What is the idiomatic test shape for each component? (template picked from the detected stack)
4. What code do the tests exercise? (the source files from the analysis)
5. What is the diff the user should review? (a PR with new/modified test files, plus a generation ledger)

## Inputs

```text
INPUT_GITHUB_REPO=<github-url>                     # REQUIRED: target repo to write tests into
INPUT_BRANCH=<optional branch, default: repo default>
INPUT_ANALYSIS_DIR=<path to component-test-analysis output>   # REQUIRED
                                              # must contain TODO_component-analysis.md + at least gap-backlog.json
GENERATION_PROFILE=safe|balanced|aggressive      # default: balanced
FOCUS_COMPONENT=<optional CTA-COMP-NNN>          # if set, only generate for this component
GAP_PRIORITY_FILTER=P0|P0-P1|P0-P2|all           # default: P0-P1
MAX_GAPS_PER_RUN=<int, default 10>               # hard cap on number of gaps to tackle in one run
MAX_REPAIR_ATTEMPTS_PER_FAILURE_CLASS=2
ALLOW_PRODUCTION_FIXES=false                     # safe/balanced never; aggressive may add testability hooks
ALLOW_TEST_CONFIG_CHANGES=false                  # safe/balanced never; aggressive may add test base classes
ALLOW_CI_CHANGES=false                           # any profile: default false
ALLOW_COMMIT=true                                # this workflow writes a branch and opens a PR
ALLOW_DEPENDENCY_INSTALL=true                    # may need to install test deps
OUTPUT_DIR=<optional, default: ./artifacts/test-generation-<date>-<runid>/
DRY_RUN=false                                    # if true, generate files but do not commit/branch/PR
```

### Profile semantics

| Profile | Production code | Test config | Dependencies | CI | PR opened |
|---|:---:|:---:|:---:|:---:|:---:|
| `safe` (default for repos you don't own) | NEVER touched | NEVER touched | only what's already declared | NEVER | YES (test-only diff) |
| `balanced` (default) | NEVER touched | may add `test/resources/` fixtures and `*TestConfig` classes | may add test-only deps (`testcontainers`, `pact-jvm`, etc.) to test scope | NEVER | YES |
| `aggressive` | may add minimal testability hooks: `protected` accessor, constructor injection, `@VisibleForTesting` | may add test base classes, profiles, tags | yes | may add a workflow file under `.github/workflows/` if missing | YES |

`aggressive` is gated by `ALLOW_PRODUCTION_FIXES=true` from the caller; the workflow will refuse to enable aggressive mode unless the input is set. `safe` and `balanced` always run with `ALLOW_PRODUCTION_FIXES=false` regardless of input.

### Defaults

- `GENERATION_PROFILE=balanced` is the default. Pick `safe` for repos where you have no commit rights or are auditing; pick `aggressive` for repos where you own the testability story.
- `GAP_PRIORITY_FILTER=P0-P1` keeps a run focused on the most valuable gaps; use `all` to drain the entire backlog.
- `MAX_GAPS_PER_RUN=10` is a safety rail. The full backlog may be 200+ gaps; running them all in one PR is a review disaster.
- `DRY_RUN=true` is useful for first contact with a repo — generates the files locally, prints the diff, opens no PR.

## Phases

The workflow has 9 phases. Phases 0.5-2 are environment + input. Phases 3-4 are re-detection (not inherited from the analysis). Phases 5-7 are the generation core. Phases 8-9 are assembly + handoff.

```
Phase 0.5  Environment pre-flight (always)
Phase 1    Input validation (always)
Phase 2    Repository acquisition (always, read-only)
Phase 3    Stack re-detection (always)        ← critical: never trust the analysis for this
Phase 4    Gap selection (always)
Phase 5    Test template selection (always)
Phase 6    Test generation (always)
Phase 7    Test execution + repair (always, gated by ALLOW_DEPENDENCY_INSTALL)
Phase 8    PR assembly (always)
Phase 9    Handoff manifest (always)
```

### Phase 0.5 — Environment pre-flight

Verifies:

- `git` on PATH and version ≥ 2.30.
- `python3` on PATH (≥ 3.8) for JSON parsing and the generation orchestrator.
- `jq` on PATH for JSON validation.
- `gh` on PATH AND authenticated — required for Phase 8 PR opening. If `DRY_RUN=true`, `gh` is not required.
- Disk free for `OUTPUT_DIR` (≥ 2 GB recommended; checkouts + generated fixtures can be large).
- GitHub auth scopes: `repo` (or `public_repo` for public repos) for the target repo.

The pre-flight fails fast with `CTG-BLK-PreFlight` if any required tool is missing.

### Phase 1 — Input validation

- Validate `INPUT_GITHUB_REPO` is a well-formed GitHub URL.
- Validate `INPUT_ANALYSIS_DIR` exists and contains at least `TODO_component-analysis.md` and `gap-backlog.json`.
- Validate `GENERATION_PROFILE ∈ {safe, balanced, aggressive}`.
- If `GENERATION_PROFILE=aggressive`, require `ALLOW_PRODUCTION_FIXES=true` from caller. Otherwise fail fast with `CTG-BLK-AggressiveRequiresFlag`.
- Validate `GAP_PRIORITY_FILTER` parses to a known set.
- Validate `MAX_GAPS_PER_RUN ≥ 1` and `<= 100`.
- If `DRY_RUN=true`, skip `gh` checks.

### Phase 2 — Repository acquisition

- Clone the target repo to `$OUTPUT_DIR/_repo/` (full clone, not shallow — we will commit and push).
- Create a working branch `test-generation/<runid>` from the default branch.
- Record the base commit SHA, branch, and timestamp in the ledger.

This is the only phase that touches the network for code.

### Phase 3 — Stack re-detection (CRITICAL)

**Do not trust the analysis for stack detection.** The analysis may be from a stale run (the repo may have changed), or it may be from a different branch. Re-derive:

- Primary language(s) from source file extensions.
- Build system: `pom.xml` (Maven), `build.gradle` / `build.gradle.kts` (Gradle), `package.json` (npm/pnpm/yarn), `pyproject.toml` / `setup.py` / `requirements.txt` (Python), `go.mod` (Go), `Cargo.toml` (Rust), `Gemfile` (Ruby), `build.sbt` (sbt), `Project.toml` or `Package.swift` (Swift), `*.cabal` (Haskell), `mix.exs` (Elixir).
- Test framework: detected from existing test files in the repo (do not assume from the analysis).
- Test layout: `src/test/` (Maven/Gradle), `test/` (Python), `__tests__/` (JS), `*_test.go` next to source (Go), `spec/` (Ruby/JS), etc.
- Coverage tool: `jacoco-maven-plugin`, `coverage.py`, `istanbul`/`nyc`/`vitest --coverage`, `go test -cover`, `cargo tarpaulin`, etc.

Emit a `detected-stack.json` so the user can see what the workflow decided. This file is part of the handoff manifest.

If the detected stack conflicts with the analysis, the analysis wins for **what to test** (the gap backlog is authoritative) but the detection wins for **how to test** (the framework, layout, conventions are project-truth).

### Phase 4 — Gap selection

1. Load `gap-backlog.json` from `INPUT_ANALYSIS_DIR`.
2. Apply `FOCUS_COMPONENT` filter if set.
3. Apply `GAP_PRIORITY_FILTER`:
   - `P0` → priority == "P0"
   - `P0-P1` → priority in {"P0", "P1"}
   - `P0-P2` → priority in {"P0", "P1", "P2"}
   - `all` → no filter
4. Sort by (priority asc, risk asc) — P0/T1 first.
5. Take the top `MAX_GAPS_PER_RUN`.
6. Validate each selected gap has a `source_file` and `target_test_file`. Gaps missing `source_file` are noted as "config-only" in the ledger and **deferred** (no test can be generated without a source path).
7. Validate each selected gap's `source_file` exists in the cloned repo. Gaps referencing missing files are noted in the ledger and **deferred** (the source has been deleted/renamed since the analysis).

Emit `selected-gaps.json` with the chosen subset + the deferred list + reasons.

### Phase 5 — Test template selection

For each selected gap, determine the **test template** to use. The template is picked from this decision tree:

```
Source file is Java?
  → Maven? → JUnit 5 (default), JUnit 4 (legacy), TestNG (rare)
       └ Test type from gap.test_type:
            unit        → JUnit 5 + Mockito + AssertJ, in same package as source
            component   → JUnit 5 + @SpringBootTest slice (per detected config)
            contract    → Spring Cloud Contract or Pact
            integration → Spring Boot Test + Testcontainers
            E2E         → out of scope for v1, mark as "manual E2E required"
  → Gradle? → same as Maven, build file is build.gradle

Source file is Python?
  → Test framework from detection: pytest | unittest | nose
       └ Test type from gap.test_type:
            unit        → pytest (default) or unittest, mirror module path
            component   → pytest with fixtures
            contract    → schemathesis or pact-python
            integration → pytest + testcontainers-python
            E2E         → out of scope for v1

Source file is JavaScript / TypeScript?
  → Test framework from detection: jest | vitest | mocha
       └ Test type from gap.test_type:
            unit        → jest/vitest, mirror source path under __tests__ or *.test.ts
            component   → React Testing Library (if React detected)
            contract    → Pact or MSW
            integration → supertest or playwright
            E2E         → playwright (out of scope for v1)

Source file is Go?
  → Test framework: standard `testing` package
       └ Test type: same naming convention (*_test.go next to source)

Source file is Rust?
  → Test framework: built-in `#[test]` + `#[cfg(test)]` modules

Source file is C# / .NET?
  → Test framework from detection: xUnit | NUnit | MSTest

Source file is Ruby?
  → Test framework: RSpec | Minitest

Source file is in any other language?
  → Emit "no template available for <language>" and defer the gap
```

Emit `templates-applied.json` mapping each gap to its template + framework + import list.

### Phase 6 — Test generation

For each selected gap, generate a test file. The generator is **deterministic and rule-based**, not LLM-fluency-based:

1. **Parse the source file.** Use the language-appropriate parser:
   - Java → `javaparser` (Python wrapper) or `tree-sitter-java` for AST
   - Python → `ast` module
   - JavaScript/TypeScript → `tree-sitter-javascript` / `tree-sitter-typescript`
   - Go → `go/parser` (if Go toolchain available) or `tree-sitter-go`
2. **Extract the public surface** (functions/methods on the class/module, signatures only).
3. **For each behavior implied by the gap** (from the gap's `trigger` and `expected_result`):
   - Identify the method/function to test.
   - Identify the inputs (from the trigger) and expected outputs (from the expected result).
   - Identify the dependencies the method needs (from the source AST or the analysis' `dependencies`).
4. **Emit test cases** following the template:
   - One test per behavior path (happy, negative, validation, error, boundary).
   - Use the project's existing test naming convention (do not invent a new one).
   - Use the project's existing assertion library (do not introduce AssertJ if the repo uses Hamcrest).
5. **Emit fixtures** for the dependencies the new tests need. Re-use existing fixtures if they exist; do not duplicate.
6. **Lint the generated file** with the project's linter (checkstyle/spotless for Java, ruff for Python, eslint for JS) if it exists. Fix what can be fixed deterministically; defer what cannot.

**Hard rules:**

- Never copy/paste the source code into the test — tests call the public API.
- Never invent methods that don't exist on the class.
- Never use `Reflection` to access private fields (this is the most common sign of a generated test that's not actually testing the contract). If a private field must be set, prefer a constructor/setter injection. If neither exists, mark the gap as "needs testability hook" and **defer** unless `aggressive` mode is on.
- Never use `Thread.sleep` or `time.sleep` (determinism rule).
- Never assert on `toString()` output of objects (brittle, low-signal).

### Phase 7 — Test execution + repair

If `ALLOW_DEPENDENCY_INSTALL=true` and the project has a runnable build, run the generated tests:

1. Detect the test command from the build system:
   - Maven: `mvn -q -Dtest=<TestClass> test` (or `mvn -q test` for the whole suite)
   - Gradle: `./gradlew test --tests <TestClass>`
   - npm: `npm test -- <TestClass>` or `npx jest <TestClass>`
   - pnpm: `pnpm test <TestClass>`
   - pytest: `pytest <test_file>::<TestClass> -q`
   - Go: `go test ./<package> -run <TestName>`
   - Rust: `cargo test <test_name>`
2. Execute. Capture results.
3. For each failing test, run the repair loop (max `MAX_REPAIR_ATTEMPTS_PER_FAILURE_CLASS` per failure class):
   | Failure class | Detection | Repair |
   |---|---|---|
   | **Import not found** | Compile/import error mentions missing symbol | Add the import; if symbol truly doesn't exist, defer |
   | **Constructor signature mismatch** | Compile error at construction | Re-parse source, update test instantiation |
   | **Fixture missing** | Runtime error about undefined fixture/bean | Add the fixture; if circular, defer |
   | **Assertion fails on first run** | AssertionError | Mark as `NEEDS_HUMAN_REVIEW` (the test exposes a real gap, not a generation bug) |
   | **Build environment error** | Java/Python/Node version mismatch | Re-install; if still failing, defer |
4. If after repair the test compiles but does not pass, **the test is still valuable as a placeholder for the gap** — keep it in the PR but mark it `@Disabled` (Java) / `@skip` (pytest) / `it.skip` (jest) with a comment explaining the assertion failure. This prevents the build from being broken, preserves the gap as a tracked item, and is a much better signal than a deleted test.

If `ALLOW_DEPENDENCY_INSTALL=false` or the build is not runnable, skip this phase. Note "execution skipped" in the ledger.

### Phase 8 — PR assembly

1. Commit the generated test files (and any testability hooks, if `aggressive`) with a structured message:
   ```
   test(component-test-generation): <N> tests across <M> components

   Generated from analysis run <analysis_run_id> (<date>).
   Profile: <profile>. Filter: <filter>. Selected <N> of <M> eligible gaps.

   Components covered:
   - <comp-1>: <N1> tests (<list gap IDs>)
   - <comp-2>: <N2> tests (<list gap IDs>)

   Gaps deferred (with reason):
   - <gap-id>: <reason>

   Generated-by: component-test-generation v1.0
   Co-Authored-By: OpenClaw <noreply@openclaw.ai>
   ```
2. Push the branch to origin.
3. Open a PR with title `test(generation): <N> tests from component analysis (<date>)` and body that includes:
   - A summary of what was generated.
   - The selected-gaps.json table (rendered as Markdown).
   - The test execution results (if Phase 7 ran).
   - A "deferred" list with reasons.
   - A "human review needed" list for tests that were `@Disabled` after failing.
4. If `DRY_RUN=true`, skip the push and PR — just produce the diff and print it to the ledger.

### Phase 9 — Handoff manifest

Emit `handoff-manifest.json` with this structure:

```json
{
  "produced_at": "<ISO-8601>",
  "profile": "safe|balanced|aggressive",
  "analysis_run_id": "<from INPUT_ANALYSIS_DIR>",
  "target_repo": "<url>",
  "target_branch": "<branch>",
  "generation_branch": "<branch>",
  "pr_url": "<url or null if DRY_RUN>",
  "artifacts": [
    {
      "file": "selected-gaps.json",
      "description": "Gaps selected for this run",
      "consumer": "human-review"
    },
    {
      "file": "detected-stack.json",
      "description": "Stack as re-detected from the target repo (may differ from analysis)",
      "consumer": "human-review"
    },
    {
      "file": "templates-applied.json",
      "description": "Test template + framework chosen per gap",
      "consumer": "human-review"
    },
    {
      "file": "test-execution-results.json",
      "description": "Results of running the generated tests (if Phase 7 ran)",
      "consumer": "human-review|application-mutation-testing"
    },
    {
      "file": "TODO_test-generation.md",
      "description": "The generation ledger",
      "consumer": "human-review"
    }
  ]
}
```

## Multi-module repositories

This workflow inherits the multi-module handling from `application-test-coverage`:

- For Maven `<modules>`, Gradle `include(...)`, npm/pnpm/yarn workspaces, Cargo workspace, sbt: treat each module as a separate test boundary.
- Tests are written to the module's test path (e.g. `core/broadleaf-framework/src/test/java/...`).
- The build is run per-module, not the whole repo, to keep iteration fast.

The selected gap's `target_test_file` is honored if the analysis workflow computed it correctly. The generation workflow re-validates the path and adjusts if the module structure has changed.

## Gap deferral (and the backlog lifecycle)

Not every gap in the analysis can be closed in one run. Deferral is a feature, not a failure. The deferral reasons are:

| Reason | Meaning | What to do |
|---|---|---|
| `source_file_missing` | The source file the gap references is no longer in the repo (renamed, deleted, or never existed) | Re-run `component-test-analysis`; the stale gap will be dropped |
| `no_test_template_for_language` | The source is in a language the generator doesn't support | Add the template to the workflow, or generate the test by hand |
| `needs_testability_hook` | The gap requires accessing private state and the source doesn't expose it | Re-run with `GENERATION_PROFILE=aggressive` and `ALLOW_PRODUCTION_FIXES=true` |
| `unresolvable_dependency` | The gap requires a dependency that can't be stubbed/wired (e.g. an external SaaS call) | Mark as integration/E2E and require a real environment |
| `no_source_file` | The gap is config-only or behavioral (e.g. "rate limiting works") with no source | Write an integration test in the right boundary; otherwise defer |
| `assertion_failed_first_run` | The generated test compiled but the assertion failed | Test is kept as `@Disabled` for human review |

A deferred gap's `deferral_reason` is recorded in `selected-gaps.json` so the user can see what to address.

## Strict rules

- **Trust the analysis for what to test.** The gap backlog is the source of truth for what's missing.
- **Trust the repo for how to test.** The detected stack is the source of truth for framework, layout, conventions.
- **Never modify production code** unless `GENERATION_PROFILE=aggressive` AND `ALLOW_PRODUCTION_FIXES=true`.
- **Never invent methods, fields, or behaviors** that don't exist in the source.
- **Never use reflection, Thread.sleep, or toString-based assertions** in generated tests.
- **Every generated test must compile.** A test that doesn't compile is worse than no test (CI noise, signal loss).
- **The PR is the deliverable.** The diff is the artifact; the JSONs are documentation of how it was built.

## Handoff contracts

- **To `application-mutation-testing`:** the generation branch from this workflow's PR is a valid mutation target. Use the branch as the baseline.
- **To `application-test-coverage`:** re-run coverage on the generation branch; the diff is a measurable increase in behavioral coverage. Compare against the pre-generation coverage captured in `test-execution-results.json`.
- **To humans:** the `TODO_test-generation.md` ledger is the primary review artifact. Read it first, then review the diff.

## Recovery

See `recovery.md`. Standard ledger-based resume pattern. The only stateful operation is the clone in Phase 2, which is cheap to redo if `--depth 1` is used.

## Validation

See `validation.md`. The gates are profile-aware.

## Outputs

See `output-template.md`. The Markdown ledger template + JSON schema docs.
