# Application Mutation Testing Recovery

## Resume Procedure

1. Locate the ledger. The ledger is `TODO_mutation-testing.md` at the
   root of the project being analyzed, next to the
   `TODO_test-coverage.md` ledger from the prior pass (per
   `workflows/shared/output-rules.md`). For a subpath project, that
   means the project subpath (e.g. `skill-governance-pipeline/`), not
   the input repository root. If no ledger is found, the workflow has
   not been started.
2. Open the ledger and find the last completed checkpoint.
3. Run `git status --short` at the project root.
4. Verify no unrelated changes would be overwritten.
5. Continue from the next incomplete phase.

## Checkpoints

```markdown
- [ ] MT-CKPT-1 INPUT_VALIDATED
- [ ] MT-CKPT-2 REPO_READY
- [ ] MT-CKPT-3 COVERAGE_CONTEXT_READ
- [ ] MT-CKPT-4 MUTATION_TOOL_DETECTED
- [ ] MT-CKPT-5 TARGETS_SELECTED
- [ ] MT-CKPT-6 BASELINE_MUTATION_COMPLETE
- [ ] MT-CKPT-7 SURVIVORS_CLASSIFIED
- [ ] MT-CKPT-8 TESTS_HARDENED
- [ ] MT-CKPT-9 FOCUSED_VALIDATION_COMPLETE
- [ ] MT-CKPT-10 MUTATION_RECHECK_COMPLETE
- [ ] MT-CKPT-11 LEDGER_FINALIZED
```
