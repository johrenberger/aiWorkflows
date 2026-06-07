# Component Test Analysis — Recovery

Standard ledger-based resume pattern. The workflow is **idempotent on re-run from the same checkpoint** — the only stateful operation is the clone in Phase 2, and shallow clones are cheap to redo.

## Interruption recovery

If interrupted, resume from `TODO_component-analysis.md` checkpoints. Do not re-clone or re-scan unless required for correctness.

**Steps:**

1. Read `TODO_component-analysis.md` and find the last completed checkpoint (the one with `[x]`).
2. Skip to the next checkpoint (the one with `[ ]`).
3. Verify the artifact files in `OUTPUT_DIR/` exist for completed work (e.g. `component-inventory.json` should exist if CTA-CKPT-4 is marked done).
4. If an expected artifact is missing, fall back to its producing phase and re-run.

**Cheap re-runs:** Phase 2 (clone) is cheap. Phase 3-4 (stack + component detection) is fast. Phase 5+ can be slow for large repos.

## Repair patterns

The `MAX_REPAIR_ATTEMPTS_PER_FAILURE_CLASS=2` input controls how many times a single failure class is retried before the workflow blocks.

| Failure class | Detection | Repair |
|---|---|---|
| **Clone failed** | `git clone` returns non-zero | Verify URL, network, auth (none needed for public); retry with explicit `--single-branch` |
| **Language detection ambiguous** | Multi-language repo with no dominant primary | Pick the one with the most source files; document the choice in the assumptions section |
| **Component boundary unclear** | Source tree has no clear domain structure | Fall back to package-level components; mark each `UNCLEAR` with rationale; do not invent boundaries |
| **No test files exist** | `find $REPO -path '*/test*' -name '*.java' -o -name '*_test.go' -o -name 'test_*.py'` returns empty | Note this as a finding in Section 8; produce gap backlog with 100% of behaviors as gaps; do not invent test files |
| **No coverage artifacts** | `find $REPO -name 'jacoco.csv' -o -name 'coverage.json' -o -name 'lcov.info' -o -name 'coverage-summary.json'` returns empty | Note in Section 8; Section 7 behavioral coverage can still be derived from test file inspection, but mark it as "estimated from test file presence" not "measured" |
| **JSON schema validation fails** | `jq empty <file>` returns non-zero | Check the field causing the failure against the schema in `output-template.md`; fix and re-emit; do not regenerate upstream analysis |
| **Target repo modified** | `git status` in `$REPO_DIR` is clean → check `git diff` against the cloned commit | If modified, this is a workflow bug. Mark `CTA-BLK-TargetModified` and block. The target must not be touched. |
| **Sub-agent not returning** | Sub-agent runtime does not return an event within 15 min | See "Sub-agent handling" below |

## Sub-agent handling

This workflow does not typically spawn sub-agents — the analysis is sequential and read-only. But for very large repos (> 10K source files), the following sub-agent split can be used:

| Role | Scope | Authority |
|---|---|---|
| **Detector** (1) | Per-directory: detect language, framework, components in this subtree | Read-only |
| **Aggregator** (1, main agent) | Merge per-directory results into a global component inventory | Owns the global inventory |

Sub-agents for this workflow are read-only by design and do not have the protocol issues from `application-test-coverage`. Apply the 5 lessons from PR #8 (wait for events, inlined command, etc.) if sub-agents are used.

## Phase 5 gap-classification repair

If `CTA-VAL-23` (gap field completeness) fails, the repair loop:

1. Identify which gaps are missing fields.
2. Re-classify each one with `TBD` + rationale for fields that cannot be determined (do not invent).
3. Re-emit `gap-backlog.json`.
4. Re-validate. If still failing, mark gaps as `REQUIRES_HUMAN_REVIEW` and continue with partial data.

## EMIT_EMPTY_JSONS repair

If the user later wants the missing JSONs (e.g. for downstream pipeline testing), set `EMIT_EMPTY_JSONS=true` and re-run only the output assembly phase. This does not re-do the analysis — it just emits stub files.

## Multi-run artifacts

Running the workflow multiple times on the same repo will produce different OUTPUT_DIRs (if `<date>` is in the path). The artifacts in each dir are self-contained. Compare across runs:

```bash
diff -r artifacts/component-analysis-2026-06-08/ artifacts/component-analysis-2026-06-15/
```

This is useful for tracking how the repo's testing strategy evolves over time.

## When to abandon

This workflow does not have a "50% of test-writer batches failed, abandon sub-agents" exit because it does not write tests. The only abandon case is if the target repo is not actually a code repo (e.g. it's a documentation-only repo) — in which case `CTA-VAL-13` (≥ 1 source file) will fail, and the user should run `app-dev-discovery` instead.

## Resume from a partial JSON

If a JSON file is partial (e.g. only some components serialized before interruption), do not resume from the partial file — re-run the producing phase and re-emit the full file. The schema validation gate (CTA-VAL-44) will catch any partial files and force a re-emit.
