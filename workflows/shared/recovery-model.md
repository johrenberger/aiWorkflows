# Recovery Model

## Purpose

Make every workflow resumable after interruption, timeout, tool failure, or context exhaustion.

## Checkpoints

Each workflow ledger must include checkpoints:

```markdown
## Checkpoints

- [ ] DISCOVERY_COMPLETE
- [ ] FRAMEWORK_DETECTION_COMPLETE
- [ ] BASELINE_TESTS_COMPLETE
- [ ] BASELINE_COVERAGE_COMPLETE
- [ ] GAP_MAPPING_COMPLETE
- [ ] WORK_BATCH_SELECTED
- [ ] IMPLEMENTATION_COMPLETE
- [ ] FOCUSED_VALIDATION_COMPLETE
- [ ] COVERAGE_RECHECK_COMPLETE
- [ ] FINAL_VALIDATION_COMPLETE
- [ ] LEDGER_FINALIZED
```

## Resume Rule

On resume:

1. Read the existing ledger.
2. Identify the last completed checkpoint.
3. Validate current git status.
4. Continue from the next incomplete checkpoint.
5. Do not repeat expensive commands unless needed for correctness.

## Failure Classes

Classify failures as:

- Environment/dependency failure.
- Existing baseline test failure.
- New test failure.
- Production bug exposed.
- Coverage tooling failure.
- Mutation tooling failure.
- CI configuration mismatch.
- Timeout/runtime cap reached.

Each failure must include exact evidence and next action.
