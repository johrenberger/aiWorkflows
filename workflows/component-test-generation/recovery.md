# Component Test Generation — Recovery

Standard ledger-based resume pattern. The workflow is **idempotent on re-run from the same checkpoint**.

## Interruption recovery

If interrupted, resume from `TODO_test-generation.md` checkpoints. Do not re-clone or re-scan unless required for correctness.

**Steps:**

1. Locate the ledger. The ledger is `TODO_test-generation.md` at the
   same path as the input `TODO_component-analysis.md` from the prior
   workflow pass (per `workflows/shared/output-rules.md`). For a
   subpath project, that means the project subpath (e.g.
   `skill-governance-pipeline/`), not the input repository root. The
   `JSON OUTPUTS` (`selected-gaps.json`, `test-execution-results.json`,
   etc.) live in `OUTPUT_DIR` as configured; the ledger is
   co-located with the project.
2. Read the ledger and find the last completed checkpoint (the one with `[x]`).
3. Skip to the next checkpoint (the one with `[ ]`).
4. Verify the artifact files in `OUTPUT_DIR/` exist for completed work.
5. If an expected artifact is missing, fall back to its producing phase and re-run.

**Cheap re-runs:**

- Phase 2 (clone) is the only expensive step. Full clone, not shallow.
- Phase 3 (stack detection) is fast.
- Phase 6 (generation) is moderately expensive (AST parsing per source file) but deterministic.
- Phase 7 (test execution) can be re-run cheaply if the test command is cached by the build system.

## Repair patterns

The `MAX_REPAIR_ATTEMPTS_PER_FAILURE_CLASS=2` input controls how many times a single failure class is retried before the workflow blocks.

| Failure class | Detection | Repair |
|---|---|---|
| **Clone failed** | `git clone` returns non-zero | Verify URL, network, auth (gh must be authenticated); retry with explicit `--no-single-branch` |
| **Branch already exists** | `git checkout -b` fails because the branch is already there | Check out the existing branch and resume from that point |
| **Source file not in repo** | `ls` on the gap's `source_file` returns ENOENT | Defer the gap with `source_file_missing`; do not invent the file |
| **Test framework not detected** | No test files in the repo and no test dep in manifest | Note "no tests exist" in the ledger; this is a valid state, not a failure |
| **AST parse error** | Parser raises an exception on the source file | Defer the gap with `parse_error`; do not try to generate a test for unparseable source |
| **Invented method detected** | Test references a method not in the source AST | Re-parse the source; if the method is truly missing, defer with `invented_method_blocked` |
| **Test doesn't compile** | Compile error in the generated test | Re-parse source, re-generate the test, retry; after MAX_REPAIR_ATTEMPTS, defer |
| **Test fails assertion on first run** | AssertionError after compile succeeds | Mark `NEEDS_HUMAN_REVIEW`, keep the test in PR as `@Disabled` with comment |
| **Build environment error** | Wrong Java/Python/Node version, missing toolchain | Defer the test; do not try to install the toolchain (out of scope) |
| **PR push fails** | `git push` returns non-zero | Check gh auth; check branch protection rules; the workflow can re-push |
| **PR open fails** | `gh pr create` returns non-zero | Check gh auth scopes; check repo permissions; the workflow can retry |
| **Sub-agent not returning** | Sub-agent runtime does not return an event within 15 min | See "Sub-agent handling" below |

## Sub-agent handling

This workflow may spawn sub-agents for very large generations (> 30 gaps). The split is per-component:

| Role | Scope | Authority |
|---|---|---|
| **Generator** (N) | Per-component: parse source AST, generate tests for that component's selected gaps | Writes to the local clone; can run the test command for its component |
| **Aggregator** (1, main agent) | Merge per-component results, run final PR assembly, push, open PR | Owns the branch and the PR |

Sub-agents inherit the protocol lessons from PR #8 of `application-test-coverage` (wait for events, inlined command, etc.) and the orchestration protocol from that workflow.

Each Generator sub-agent must:
- Read its selected gaps from `selected-gaps.json` (filtered to its component).
- Write test files into the local clone.
- Run the per-module test command for its component.
- Report results back via the standard sub-agent completion event.

The Aggregator sub-agent must:
- Wait for all Generators to complete (use `sessions_yield`).
- Merge `test-execution-results.json` from each Generator.
- Commit, push, and open the PR.

## Phase 6 repair (generation)

If `CTG-VAL-32` (generated file parses) fails, the repair loop:

1. Identify the syntactic error.
2. Re-parse the source AST to confirm the structure.
3. Re-generate the test file with corrected syntax.
4. Re-validate.
5. If still failing, mark the gap as `deferred` with reason `generation_failed_after_retry`.

## Phase 7 repair (execution)

If `CTG-VAL-43` (generated tests compile) fails, the repair loop:

1. Identify the failing test file.
2. Categorize the failure:
   - `import_not_found` → add the import
   - `constructor_mismatch` → re-parse source constructor, update test
   - `fixture_missing` → add the fixture or use an existing one
   - `assertion_failed` → mark `NEEDS_HUMAN_REVIEW`, `@Disabled` the test
   - `build_error` → defer
3. Apply the repair.
4. Re-run the test command for that file.
5. After MAX_REPAIR_ATTEMPTS, mark `deferred` with reason matching the failure class.

## EMIT behavior

Unlike `component-test-analysis`, this workflow **always** emits the core JSONs (`selected-gaps.json`, `detected-stack.json`, `templates-applied.json`, `handoff-manifest.json`). `test-execution-results.json` is emitted only if Phase 7 ran (i.e., the build is runnable and `ALLOW_DEPENDENCY_INSTALL=true`).

The `selected-gaps.json` `deferred` array is the source of truth for "what didn't we tackle in this run." A user re-running the workflow should look at the deferred list and the analysis `gap-backlog.json` to decide which gaps to address next.

## Multi-run artifacts

Running the workflow multiple times on the same repo + analysis will produce different generation branches (the `<runid>` includes a timestamp). The artifacts in each `OUTPUT_DIR/` are self-contained. Compare across runs:

```bash
diff -r artifacts/test-generation-2026-06-08-001/ artifacts/test-generation-2026-06-15-001/
```

This is useful for tracking how the generation improves over time as the templates and detection logic get refined.

## When to abandon

This workflow has two main abandon cases:

1. **The analysis is fundamentally incompatible with the repo.** Example: the analysis is from a JavaScript repo, but the cloned repo is now a Python repo. The detected stack won't have any matching gap (the source files are gone). Mark `CTG-BLK-AnalysisStale` and tell the user to re-run the analysis.

2. **The build is not runnable and cannot be installed.** Example: the repo has a 3-hour Maven build with custom plugins. The workflow generates the tests, skips Phase 7, and tells the user "tests are not validated; please run them locally." This is a graceful skip, not a hard abandon.

There is no "N out of M tests failed, abandon" exit. Even if all generated tests fail on first run, the `@Disabled` placeholders are still valuable as a tracked backlog.

## Resume from a partial JSON

If a JSON file is partial (e.g. only some components serialized before interruption), do not resume from the partial file — re-run the producing phase and re-emit the full file. The schema validation gate (CTG-VAL-55) will catch any partial files and force a re-emit.

## Resume from a partial PR

If the branch was pushed but the PR was not opened (CTG-VAL-49 failed), the recovery is:

1. Re-run from CTG-CKPT-8 (PR assembly).
2. The push (CTG-VAL-48) is idempotent — re-pushing the same commit is a no-op.
3. Re-attempt the PR open.
4. If the PR open keeps failing (e.g. branch protection requires reviews), note the branch URL in the ledger and tell the user "branch pushed, PR open failed, please open manually."

## Resume from a failed test execution

If the test command itself fails (e.g. Maven crashes mid-build), the recovery is:

1. Re-run from CTG-CKPT-7.
2. The generated test files are unchanged.
3. Re-attempt the test execution.
4. If the build keeps crashing, mark Phase 7 as "execution aborted, see `<log file>`" and continue to Phase 8 with a note.
