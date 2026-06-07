# Application Test Coverage Validation

## Required Validation Gates

- [ ] **TC-VAL-1 [Repository Input]** GitHub URL captured and repository cloned/opened.
- [ ] **TC-VAL-2 [Runtime Metadata]** Branch, commit, working tree, and timestamp recorded.
- [ ] **TC-VAL-3 [Framework Detection]** Test framework and coverage tooling detected from evidence.
- [ ] **TC-VAL-4 [Baseline Tests]** Existing tests run or blocker documented.
- [ ] **TC-VAL-5 [Baseline Coverage]** Coverage run or blocker documented.
- [ ] **TC-VAL-6 [Eligible Files]** Eligible and excluded files classified with rationale.
- [ ] **TC-VAL-7 [Per-File Table]** Each eligible source file has baseline/final/status.
- [ ] **TC-VAL-8 [90% Target]** Each eligible source file reaches 90% or has blocker.
- [ ] **TC-VAL-9 [Test Quality]** Added tests follow AAA and deterministic design.
- [ ] **TC-VAL-10 [No Weakening]** Existing tests were not weakened to pass.
- [ ] **TC-VAL-11 [Focused Validation]** Changed-module tests pass or blocker recorded.
- [ ] **TC-VAL-12 [Full Validation]** Full suite/coverage run where feasible.
- [ ] **TC-VAL-13 [Ledger Complete]** `TODO_test-coverage.md` includes all required sections.

## Failure Handling

If validation fails, classify the failure:

- Baseline failure.
- New test failure.
- Environment failure.
- Coverage tooling failure.
- Production bug exposed.
- Timeout.
- Insufficient testability.

Record evidence and next action.
