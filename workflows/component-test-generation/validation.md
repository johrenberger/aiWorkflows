# Component Test Generation — Validation

The workflow's quality gates are profile-aware. All gates start with prefix `CTG-` (Component Test Generation) to distinguish from `CTA-` (Component Test Analysis), `TC-` (Test Coverage), and `MT-` (Mutation Testing) gates.

## Pre-flight gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTG-VAL-1** | all | `git` on PATH and version ≥ 2.30 | fail fast with `CTG-BLK-PreFlight` |
| **CTG-VAL-2** | all | `python3` on PATH and version ≥ 3.8 | fail fast |
| **CTG-VAL-3** | all | `jq` on PATH (for JSON validation) | fail fast |
| **CTG-VAL-4** | all | `gh` on PATH AND authenticated, with `repo` or `public_repo` scope (skipped if DRY_RUN) | fail fast |
| **CTG-VAL-5** | all | OUTPUT_DIR exists and is writable | fail fast |
| **CTG-VAL-6** | all | OUTPUT_DIR has ≥ 2 GB free | warn (not block) |

## Input validation gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTG-VAL-7** | all | INPUT_GITHUB_REPO is a well-formed GitHub URL | fail fast with `CTG-BLK-InputInvalid` |
| **CTG-VAL-8** | all | INPUT_ANALYSIS_DIR exists | fail fast |
| **CTG-VAL-9** | all | INPUT_ANALYSIS_DIR contains `TODO_component-analysis.md` and `gap-backlog.json` | fail fast |
| **CTG-VAL-10** | all | GENERATION_PROFILE ∈ {safe, balanced, aggressive} | fail fast |
| **CTG-VAL-11** | aggressive | ALLOW_PRODUCTION_FIXES=true is set (required for aggressive) | fail fast with `CTG-BLK-AggressiveRequiresFlag` |
| **CTG-VAL-12** | all | GAP_PRIORITY_FILTER ∈ {P0, P0-P1, P0-P2, all} | fail fast |
| **CTG-VAL-13** | all | MAX_GAPS_PER_RUN ≥ 1 AND ≤ 100 | fail fast |
| **CTG-VAL-14** | safe/balanced | ALLOW_PRODUCTION_FIXES=false (safe/balanced MUST NOT touch production) | fail fast |
| **CTG-VAL-15** | safe | ALLOW_TEST_CONFIG_CHANGES=false (safe MUST NOT add test config) | fail fast |
| **CTG-VAL-16** | safe/balanced | ALLOW_CI_CHANGES=false (only aggressive may touch CI) | fail fast |

## Repository acquisition gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTG-VAL-17** | all | Clone succeeds (full clone, not shallow — we will push) | fail fast with `CTG-BLK-CloneFailed` |
| **CTG-VAL-18** | all | Working branch `test-generation/<runid>` created from base | fail fast |
| **CTG-VAL-19** | all | Base commit SHA recorded in ledger | fail fast |

## Stack re-detection gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTG-VAL-20** | all | At least one source file exists in the repo (else: nothing to test) | fail fast with `CTG-BLK-NoSourceFound` |
| **CTG-VAL-21** | all | Primary language detected from source extensions | fail fast |
| **CTG-VAL-22** | all | Test framework detected from existing test files (or NONE explicitly noted) | warn (not block) |
| **CTG-VAL-23** | all | `detected-stack.json` emitted with all required fields | fail fast |
| **CTG-VAL-24** | all | If conflicts with analysis detected, the conflict is documented in the ledger | fail fast |

## Gap selection gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTG-VAL-25** | all | `gap-backlog.json` parses as valid JSON | fail fast |
| **CTG-VAL-26** | all | Selected gaps have `source_file` and `target_test_file` populated | fail fast |
| **CTG-VAL-27** | all | Selected gaps' `source_file` exists in the cloned repo (else: defer with reason) | log + defer |
| **CTG-VAL-28** | all | Filter results in ≥ 0 selected gaps; 0 is acceptable (means backlog doesn't match filter) | log + continue |
| **CTG-VAL-29** | all | `selected-gaps.json` has `selected` and `deferred` arrays with reasons | fail fast |

## Template selection gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTG-VAL-30** | all | Each selected gap has a template assigned (or is deferred with `no_test_template_for_language`) | fail fast |
| **CTG-VAL-31** | all | `templates-applied.json` lists imports needed for each template | fail fast |

## Generation gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTG-VAL-32** | all | Generated test file parses as valid source code (no syntax errors) | fail fast |
| **CTG-VAL-33** | all | No method/field in the generated test doesn't exist in the source AST | fail fast with `CTG-BLK-InventedMethod` |
| **CTG-VAL-34** | all | No reflection in the generated test (unless `safe=false` AND the source has `@VisibleForTesting`) | warn |
| **CTG-VAL-35** | all | No `Thread.sleep` / `time.sleep` / `setTimeout` in the generated test | fail fast |
| **CTG-VAL-36** | all | No `toString()` assertion in the generated test | fail fast |
| **CTG-VAL-37** | safe | No file written outside the test path (`src/test/`, `test/`, `__tests__/`, `*_test.go` next to source) | fail fast with `CTG-BLK-SafeViolated` |
| **CTG-VAL-38** | safe | No manifest file (`package.json`, `pom.xml`, `requirements.txt`, etc.) modified | fail fast |
| **CTG-VAL-39** | safe/balanced | No production source file (`src/main/`, `src/`, `lib/`) modified | fail fast |
| **CTG-VAL-40** | balanced | Test-only deps added in test scope only (Maven `<scope>test</scope>`, npm `devDependencies`) | fail fast |
| **CTG-VAL-41** | aggressive | Each production-code change is a single-purpose, revertible commit | fail fast |
| **CTG-VAL-42** | safe/balanced | No CI file (`.github/workflows/`, `.gitlab-ci.yml`, etc.) modified | fail fast |

## Test execution gates (Phase 7)

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTG-VAL-43** | all (if Phase 7 ran) | Generated tests compile (or are deferred with reason) | fail fast |
| **CTG-VAL-44** | all (if Phase 7 ran) | Repair attempts ≤ MAX_REPAIR_ATTEMPTS_PER_FAILURE_CLASS per class | log + defer |
| **CTG-VAL-45** | all (if Phase 7 ran) | `test-execution-results.json` has summary + per-test results | fail fast |
| **CTG-VAL-46** | all (if Phase 7 ran) | NEEDS_HUMAN_REVIEW tests are `@Disabled` with a comment, not deleted | fail fast |
| **CTG-VAL-47** | all | If Phase 7 was skipped (no build available), the skip is noted in the ledger | log + continue |

## PR assembly gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTG-VAL-48** | all | Branch pushed to origin (skipped if DRY_RUN) | fail fast |
| **CTG-VAL-49** | all | PR opened on the target repo (skipped if DRY_RUN) | fail fast |
| **CTG-VAL-50** | all | PR title follows the convention `test(generation): <N> tests from component analysis (<date>)` | fail fast |
| **CTG-VAL-51** | all | PR body includes the selected-gaps table, the deferred list, and the needs-human-review list | fail fast |
| **CTG-VAL-52** | all | Commit message includes the analysis run id and the profile | fail fast |
| **CTG-VAL-53** | DRY_RUN | Diff printed to ledger, no push, no PR | fail fast (if push/PR attempted) |

## Output assembly gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTG-VAL-54** | all | `TODO_test-generation.md` exists and is non-empty | fail fast |
| **CTG-VAL-55** | all | Every produced JSON validates against its schema in `output-template.md` | fail fast |
| **CTG-VAL-56** | all | `handoff-manifest.json` lists all produced artifacts | fail fast |

## Profile gating enforcement

The `GENERATION_PROFILE` input gates which gates apply. `safe` enforces CTG-VAL-37/38/39/42. `balanced` enforces CTG-VAL-39/40/42. `aggressive` is the only profile allowed to add production-code changes (CTG-VAL-41) and CI changes (replaces CTG-VAL-42).

A gate that does not apply to the active profile is marked `N/A` in the ledger, not `PASS` or `FAIL`. This is important: a `safe` run should not "fail" `aggressive`-only gates.

## Gate results

The workflow's final report includes a gate summary table:

| Gate | Status | Evidence |
|---|---|---|
| CTG-VAL-1 | PASS | `git --version` returned `git version 2.43.0` |
| CTG-VAL-7 | PASS | URL `https://github.com/johrenberger/creative-ai` is well-formed |
| ... | | |
| CTG-VAL-50 | PASS | PR opened: `https://github.com/johrenberger/creative-ai/pull/3` |

If any gate that applies to the active profile is `FAIL`, the workflow is BLOCKED. The user must fix and re-run from the failed checkpoint.

## Inter-gate dependencies

- CTG-VAL-9 (analysis dir valid) must pass before CTG-VAL-25 (gap-backlog parses).
- CTG-VAL-19 (branch created) must pass before CTG-VAL-27 (source file exists check).
- CTG-VAL-27 (source file exists) must pass before CTG-VAL-32 (generated file parses).
- CTG-VAL-32 (generated file parses) must pass before CTG-VAL-43 (compiled).
- CTG-VAL-48 (pushed) must pass before CTG-VAL-49 (PR opened).

These dependencies are enforced by checkpoint order, not by a separate gate.
