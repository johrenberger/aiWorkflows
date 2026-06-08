# Component Test Generation Workflow

**Purpose:** Consume the analysis produced by [`component-test-analysis`](../component-test-analysis/README.md) and **generate concrete, runnable test files** in the target repo that close the prioritized gap backlog. **Project-agnostic** — works against any GitHub repo where the analysis workflow has run.

**Origin:** Built as the natural counterpart to `component-test-analysis`. Where that workflow answers "what's missing?", this workflow answers "produce the tests that cover it."

## When to use

Use this workflow when you want to:

- **Close gaps from a prior analysis run.** The `gap-backlog.json` is the input; the test files are the output.
- **Automate test creation at scale.** Instead of writing 50 tests by hand from a 200-gap backlog, generate the high-priority subset and review.
- **Bootstrap test coverage in a new project** that has an analysis run but no tests.
- **Establish a baseline** before mutation testing — the generated tests are a known-good starting point for `application-mutation-testing` to evaluate.

Do **not** use this workflow to:

- **Analyze a repo** (use `component-test-analysis` first).
- **Measure test effectiveness** (use `application-mutation-testing`).
- **Discover the repo at a high level** (use `app-dev-discovery`).

## How it relates to the analysis workflow

```
┌────────────────────────┐    gap-backlog.json    ┌──────────────────────────┐
│ component-test-        │  ───────────────────►  │ component-test-          │
│ analysis               │  TODO_...md            │ generation  (this wf)    │
│                        │  component-inventory.. │                          │
│ (reads repo, writes    │  contract-inventory..  │ (reads analysis, writes  │
│  analysis only)        │  risk-priority-...     │  test files + opens PR)  │
└────────────────────────┘                        └──────────────────────────┘
                                                          │
                                                          │ branch + PR
                                                          ▼
                                                   ┌──────────────────────────┐
                                                   │ target repo              │
                                                   │ (with new test files)    │
                                                   └──────────────────────────┘
```

The two workflows are **independent**: the analysis never knows the generator exists, and the generator never modifies the analysis. The handoff is the `gap-backlog.json` file. Either workflow can evolve without breaking the other.

## Generation profiles

| Profile | Production code | Test config | Dependencies | CI | When to use |
|---|:---:|:---:|:---:|:---:|---|
| **`safe`** | NEVER | NEVER | only existing | NEVER | Auditing a repo you don't own; want zero source impact |
| **`balanced`** (default) | NEVER | may add test resources + base classes | may add test-only deps | NEVER | Default for repos you own; tests may need new fixtures |
| **`aggressive`** | may add testability hooks | may add profiles, tags, base classes | yes | may add workflow | Repos where you own the testability story end-to-end |

`aggressive` requires `ALLOW_PRODUCTION_FIXES=true` to be set by the caller. The workflow refuses to enable it otherwise.

## Inputs

See `workflow.md` for the full input contract. The minimum is:

```text
INPUT_GITHUB_REPO=<github-url>
INPUT_ANALYSIS_DIR=<path to component-test-analysis output>
GENERATION_PROFILE=safe|balanced|aggressive   # default: balanced
GAP_PRIORITY_FILTER=P0|P0-P1|P0-P2|all        # default: P0-P1
MAX_GAPS_PER_RUN=10                            # hard cap
DRY_RUN=false                                  # set true for first contact
```

## Outputs

The primary output is **a PR on the target repo** with the generated test files. The workflow also emits these artifacts in `OUTPUT_DIR/`:

| File | Always | Description |
|---|:---:|---|
| `TODO_test-generation.md` | ✅ | The generation ledger (review this first) |
| `selected-gaps.json` | ✅ | The gaps selected for this run + the deferral list |
| `detected-stack.json` | ✅ | Stack as re-detected from the target repo (may differ from analysis) |
| `templates-applied.json` | ✅ | Test template + framework + import list chosen per gap |
| `test-execution-results.json` | if Phase 7 ran | Results of running the generated tests |
| `handoff-manifest.json` | ✅ | One-line descriptions + consumer mappings |
| `<test files>` | ✅ | The actual test files (in the target repo, also copied to `OUTPUT_DIR/_repo/` for inspection) |

## Profiles in detail

### `safe` (read-only test addition)

- Adds new test files only. Never touches `src/main/`, `src/`, `lib/`, `package.json` `dependencies`, etc.
- Never adds new test dependencies.
- Never adds CI changes.
- Result: a PR with test files diff only. Easy to review, easy to revert.

### `balanced` (default — test infrastructure allowed)

- Adds new test files.
- May add new files under `src/test/resources/` (fixtures, expected outputs).
- May add new test-only dependencies (e.g. add `pact-jvm` to Maven's `<scope>test</scope>`).
- May add test base classes (e.g. `AbstractIntegrationTest.java`) and configuration.
- Never touches production code or CI.

### `aggressive` (testability changes allowed)

- Everything in `balanced`.
- May add minimal testability hooks to production code:
  - `protected` accessors for private fields
  - Constructor injection for `@Autowired` fields
  - `@VisibleForTesting` annotations
  - Method extraction (small, surgical refactors)
- May add `.github/workflows/test-generation-validation.yml` if missing.
- May add `package.json` dependencies.
- Each production-code change must be a single-purpose, revertible commit. Document each in the PR description.

## Pipeline position

```
component-test-analysis     ← you start here
       │
       │ produces gap-backlog.json + TODO_*.md
       ▼
component-test-generation   ← this workflow
       │
       │ opens PR with new test files
       ▼
PR review + merge           ← human-in-the-loop
       │
       ▼
application-mutation-testing  ← optional, evaluate the new tests
application-test-coverage      ← optional, re-measure coverage
```

The `component-test-generation` workflow is **synchronous** in the pipeline: it reads the analysis, generates tests, opens a PR, and stops. The next stage (review, mutation, coverage) is the user's call.

## Files

- `workflow.md` — objective, inputs, phases, handoff contracts.
- `prompt-implementation.md` — the executor prompt.
- `output-template.md` — the Markdown ledger template + JSON schema docs.
- `validation.md` — quality gates and CTG-VAL-* checks.
- `recovery.md` — interruption and repair patterns.
- `_docs/handoffs.md` — explicit handoff contracts to other workflows.
- `_docs/profile-tiers.md` — per-profile behavior matrix.

## Anti-patterns (do not do these)

- **Do not let the generator invent methods.** If the source AST doesn't show a method, the test cannot call it. Defer the gap.
- **Do not let the generator use reflection to bypass access modifiers.** This is the #1 sign of a generated test that doesn't actually test the contract. Use `aggressive` mode + a real testability hook instead.
- **Do not generate tests that don't compile.** A non-compiling test is worse than no test. The Phase 7 repair loop is the safety net.
- **Do not run with `MAX_GAPS_PER_RUN=1000` on the first run.** Start with 5-10. See what the generator produces. Tune the priority filter. Then scale up.
- **Do not trust the analysis for stack detection.** The analysis may be from a stale run. Phase 3 re-detects the stack from the current repo state.

## Versioning

This is v1.0 of the workflow. Future versions will add:

- **Larger language coverage** (Rust, Ruby, Go are partially supported; Swift, Kotlin native, C# coming).
- **Contract test generation** from `contract-inventory.json` (Pact/SCC stubs).
- **Mutation-aware generation** — generate tests specifically targeted at the mutations in `mutation-roadmap.json`.
- **Auto-handoff** from the analysis workflow (set `AUTO_HANDOFF=true` on the analysis side).
