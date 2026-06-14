# Application Test Coverage Recovery

## Resume Procedure

1. Locate the ledger. The ledger is `TODO_test-coverage.md` at the
   root of the project being analyzed (per `workflows/shared/output-rules.md`).
   For a single-project repository that is the repository root; for a
   subpath project (e.g. `skill-governance-pipeline/`) it is the
   project subpath. The `TC-CTX-1 [Repository]` field of the ledger
   records the exact path. If no ledger exists at the project root,
   search the repository: `find . -name TODO_test-coverage.md -not
   -path './.git/*'`. If a misplaced ledger is found at the input
   repository root for a subpath project, it is a `TC-BLK-LedgerMisplaced`
   and should be moved to the project root.
2. Open the ledger and find the last completed checkpoint.
3. Run `git status --short` at the project root.
4. Verify no unrelated user changes would be overwritten.
5. Continue from the next incomplete phase.

## v2-aware resume

If the workflow used `application-test-automation-v2` (Phase 2.5), the deterministic analysis lives in `<ARTIFACTS_DIR>/v2/`. On resume:

1. Verify the v2 outputs are still present (`ls <ARTIFACTS_DIR>/v2/v2_summary.md`). If they're missing or stale, re-run `workflows/shared/integrate-v2.sh <REPO_PATH> <ARTIFACTS_DIR> 50 [--generate-coverage]`.
2. Re-read `v2_summary.md` to recover the work batch (Phase 8) and per-file work-item specs (`v2/ai_work_items/wi-*.md`).
3. Do not re-run v2 if the pre-batch `coverage_baseline.json` is still accurate — only re-run if the source tree has changed since the last v2 run.

If the pre-flight (Phase 0.5) was completed but Phase 2.5 was not, check whether `test-factory` is on PATH before resuming. If it's missing, the resume continues in manual-detect mode (Phases 3-9) and should record `TC-BLK-V2NotInstalled` in the ledger.

## Checkpoints

```markdown
- [ ] TC-CKPT-1 INPUT_VALIDATED
- [ ] TC-CKPT-2 REPO_READY
- [ ] TC-CKPT-3 FRAMEWORK_DETECTED
- [ ] TC-CKPT-4 BASELINE_TESTS_COMPLETE
- [ ] TC-CKPT-5 BASELINE_COVERAGE_COMPLETE
- [ ] TC-CKPT-6 ELIGIBLE_FILES_CLASSIFIED
- [ ] TC-CKPT-7 COVERAGE_GAPS_MAPPED
- [ ] TC-CKPT-8 WORK_BATCH_SELECTED
- [ ] TC-CKPT-9 TESTS_IMPLEMENTED
- [ ] TC-CKPT-10 FOCUSED_VALIDATION_COMPLETE
- [ ] TC-CKPT-11 COVERAGE_RECHECK_COMPLETE
- [ ] TC-CKPT-12 FINAL_VALIDATION_COMPLETE
- [ ] TC-CKPT-13 LEDGER_FINALIZED
```
