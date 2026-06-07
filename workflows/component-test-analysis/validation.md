# Component Test Analysis — Validation

The workflow's quality gates are profile-aware. All gates start with prefix `CTA-` (Component Test Analysis) to distinguish from `TC-` (Test Coverage) and `MT-` (Mutation Testing) gates.

## Pre-flight gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTA-VAL-1** | all | `git` on PATH and version ≥ 2.30 | fail fast with `CTA-BLK-PreFlight` |
| **CTA-VAL-2** | all | `python3` on PATH and version ≥ 3.8 | fail fast |
| **CTA-VAL-3** | all | `jq` on PATH (for JSON validation) | fail fast |
| **CTA-VAL-4** | all | OUTPUT_DIR exists and is writable | fail fast |
| **CTA-VAL-5** | all | OUTPUT_DIR has ≥ 1 GB free | warn (not block) |

Note: this workflow does **NOT** require test-execution tooling (no `mvn`, `pytest`, `npm test`, etc.). It is read-only.

## Input validation gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTA-VAL-6** | all | INPUT_GITHUB_REPO is a well-formed GitHub URL (https://github.com/<owner>/<repo>) | fail fast with `CTA-BLK-InputInvalid` |
| **CTA-VAL-7** | all | INPUT_BRANCH, if specified, exists on the remote | fail fast |
| **CTA-VAL-8** | all | ANALYSIS_PROFILE ∈ {lite, standard, full} | fail fast |
| **CTA-VAL-9** | all | OUTPUT_DIR is not the repo root (avoid polluting the target) | fail fast |

## Repository acquisition gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTA-VAL-10** | all | Clone succeeds (network reachable, repo exists, auth not required for public) | fail fast with `CTA-BLK-CloneFailed` |
| **CTA-VAL-11** | all | Clone is shallow (--depth 1) — full history not needed for analysis | warn |
| **CTA-VAL-12** | all | Commit SHA recorded in ledger | fail fast |

## Stack detection gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTA-VAL-13** | all | At least one language detected from source files | fail fast with `CTA-BLK-NoSourceFound` |
| **CTA-VAL-14** | all | Build system detected (or NONE explicitly noted) | fail fast |
| **CTA-VAL-15** | all | Test framework detected (or NONE explicitly noted) | warn (not block) |
| **CTA-VAL-16** | all | Assumptions section in ledger is populated | fail fast |

## Component detection gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTA-VAL-17** | all | ≥ 1 component detected OR rationale for why 0 components | fail fast |
| **CTA-VAL-18** | all | Every component has name, responsibility, public interface, risk tier, test boundary | fail fast |
| **CTA-VAL-19** | all | Components with `UNCLEAR` state have a rationale | fail fast |
| **CTA-VAL-20** | all | Multi-module repos (if detected) treat each module as a top-level component | fail fast |

## Phase 5 (LITE+) gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTA-VAL-21** | LITE+ | `component-inventory.json` validates against its schema | fail fast |
| **CTA-VAL-22** | LITE+ | `behavior-coverage.json` has a coverage_percent field per component and aggregate | fail fast |
| **CTA-VAL-23** | LITE+ | `gap-backlog.json` has all required fields per gap (severity, risk, complexity, effort, owner, priority) | fail fast |
| **CTA-VAL-24** | LITE+ | Gap IDs are unique (CTA-GAP-001, CTA-GAP-002, ...) | fail fast |
| **CTA-VAL-25** | LITE+ | Behavioral coverage score is calculated honestly (not 100% by default) | fail fast with `CTA-BLK-InventedCoverage` |
| **CTA-VAL-26** | LITE+ | Every gap references a source file or explicitly notes "no source file — config only" | fail fast |

## Phase 6 (STANDARD+) gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTA-VAL-27** | STANDARD+ | `dependency-risk-matrix.json` validates; every risk score = failure_impact × likelihood | fail fast |
| **CTA-VAL-28** | STANDARD+ | `state-transition-matrix.json` has START and at least one terminal state per component | fail fast |
| **CTA-VAL-29** | STANDARD+ | `contract-inventory.json` covers every public API detected in the source | fail fast |
| **CTA-VAL-30** | STANDARD+ | Test fidelity matrix has rationale (not just "Real" with no why) | fail fast |
| **CTA-VAL-31** | STANDARD+ | Decision tree is deterministic ("if X then Y"), not heuristic | fail fast |

## Phase 7 (STANDARD+) gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTA-VAL-32** | STANDARD+ | `risk-priority-ranking.json` validates; every component has a risk score | fail fast |
| **CTA-VAL-33** | STANDARD+ | Quality gates have thresholds AND action-on-failure | fail fast |
| **CTA-VAL-34** | STANDARD+ | Rollout plan has 6 phases with success criteria | fail fast |
| **CTA-VAL-35** | STANDARD+ | Test pyramid distribution adds to 100% | fail fast |

## Phase 8 (FULL) gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTA-VAL-36** | FULL | Security coverage matrix has all 7 categories per component | fail fast |
| **CTA-VAL-37** | FULL | OWASP ASVS references are valid IDs (V1.1.1, V2.1.1, etc.) | fail fast |
| **CTA-VAL-38** | FULL | Architecture validation backlog references ArchUnit (Java) or Dependency Cruiser (JS) rules | fail fast |
| **CTA-VAL-39** | FULL | Java playbook matches the actual build system (Maven or Gradle) | fail fast |
| **CTA-VAL-40** | FULL | JavaScript playbook matches the actual test framework (Jest, Vitest, Mocha) | fail fast |
| **CTA-VAL-41** | FULL | `mutation-roadmap.json` has PIT version, targets, exclusions, thresholds | fail fast |
| **CTA-VAL-42** | FULL | `test-creation-input-schema.json` is a valid JSON Schema (Draft 7+) | fail fast |

## Output assembly gates

| Gate | Profile | Description | Failure action |
|---|---|---|---|
| **CTA-VAL-43** | all | `TODO_component-analysis.md` exists and is non-empty | fail fast |
| **CTA-VAL-44** | all | Every produced JSON validates against its schema in `output-template.md` | fail fast |
| **CTA-VAL-45** | all | `handoff-manifest.json` lists all produced JSONs | fail fast |
| **CTA-VAL-46** | all | `EMIT_EMPTY_JSONS=false` (default) is respected — no empty stubs emitted | fail fast |
| **CTA-VAL-47** | all | Target repo was NOT modified (no files in `_repo/` differ from clone) | fail fast with `CTA-BLK-TargetModified` |

## Profile gating enforcement

The `ANALYSIS_PROFILE` input gates which gates apply. LITE does NOT require CTA-VAL-27 through CTA-VAL-42 to pass (they're STANDARD+/FULL only). LITE does require CTA-VAL-21 through CTA-VAL-26 (its own gates).

A gate that does not apply to the active profile is marked `N/A` in the ledger, not `PASS` or `FAIL`. This is important: a LITE run should not "fail" STANDARD+ gates.

## Gate results

The workflow's final report includes a gate summary table:

| Gate | Status | Evidence |
|---|---|---|
| CTA-VAL-1 | PASS | `git --version` returned `git version 2.43.0` |
| CTA-VAL-2 | PASS | `python3 --version` returned `Python 3.11.9` |
| ... | | |
| CTA-VAL-46 | PASS | `EMIT_EMPTY_JSONS=false`; 5 of 8 JSONs emitted, 3 skipped (dataset-integrity, contract-inventory, mutation-roadmap) |

If any gate that applies to the active profile is `FAIL`, the workflow is BLOCKED. The user must fix and re-run from the failed checkpoint.

## Inter-gate dependencies

- CTA-VAL-10 (clone) must pass before CTA-VAL-13 (language detection) runs.
- CTA-VAL-17 (component count) must pass before CTA-VAL-21 (component-inventory.json schema).
- CTA-VAL-23 (gap fields) must pass before CTA-VAL-32 (risk ranking) can rank gaps.

These dependencies are enforced by checkpoint order, not by a separate gate.
