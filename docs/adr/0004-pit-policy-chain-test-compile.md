# ADR 0004: PIT policy chains `test-compile` ahead of `mutationCoverage`

* **Status:** Accepted (2026-06-12; revised 2026-06-13 with docstring fix)
* **Context:** Story 026 of mutation work, PR #40; story 030 (docstring fix) PR #41
* **Deciders:** software-engineer, test-automation, code-review-agent
* **Tags:** mutation, pit, real-tool-policy, maven-lifecycle

## Context and Problem Statement

The mutation-testing workflow supports PIT (Pitest) as an
optional real mutation tool. PIT runs the project's test suite
against mutated code; it needs both the production classes and
the test classes compiled. The current `evaluate_real_pit_policy`
in `mutationctl/workflow/real_tool_policy.py` constructs:

```
mvn test-compile org.pitest:pitest-maven:mutationCoverage \
    -DtargetClasses=<FQCN>
```

The question: is `test-compile` sufficient, or should we chain
`process-test-resources` ahead of it? (And should we add
`verify` for a "fresh test pass"?)

## Considered Options

1. **`mvn test-compile org.pitest:pitest-maven:mutationCoverage`**
   (chosen). `test-compile` already includes
   `process-test-resources` in Maven's lifecycle (it depends on
   `process-test-resources` transitively).
2. **`mvn process-test-resources test-compile org.pitest:pitest-maven:mutationCoverage`**:
   Redundant. `test-compile` chains `process-test-resources` for
   us.
3. **`mvn verify ...`**: Wrong. `verify` runs the
   `integration-test` phase, which is for integration tests, not
   the unit tests PIT mutates against.
4. **`mvn test org.pitest:pitest-maven:mutationCoverage`**:
   Runs unit tests AND mutates in one go. This is actually the
   PIT-recommended invocation in many docs. But it runs all
   tests, not just the ones for the target class. For
   per-target-class mutation runs, `test-compile` is faster
   (compile only, no test execution) and we let PIT
   re-execute the tests against the mutants.

## Decision Outcome

**Chosen option: 1 (just `test-compile`).**

Investigation showed:

- `mvn test-compile` already includes `process-test-resources`
  in Maven's lifecycle. Adding it explicitly is redundant.
- `mvn verify` runs the integration-test phase, which is for
  integration tests, not the unit tests PIT mutates against.
  Adding `verify` would slow the PIT run significantly (it
  spins up the integration-test environment).
- The original story's docstring said "add `verify` for fresh
  test pass" — this is wrong (see "Revision" below).

`test-compile` is sufficient. The `org.pitest:pitest-maven:mutationCoverage`
goal inherits the test-classpath (because `test-compile`
compiles both main and test classes) and mutates only the
target class via `-DtargetClasses=<FQCN>`.

## Revision (2026-06-13, story 030)

The original docstring in `real_tool_policy.py` said:

> Users can add `verify` for fresh test pass before mutating.

This is wrong. `verify` runs the integration-test phase. The
fix (story 030, PR #41) is to:

1. Remove the misleading "add `verify`" comment.
2. Add a reason note documenting the test-classpath assumption
   (i.e., that `test-compile` is sufficient because Maven
   lifecycle chains `process-test-resources` transitively).
3. Add 2 BDD tests that pin this contract:
   - `test_given_real_pit_when_command_built_then_command_does_not_chain_process_test_resources_explicitly`
   - `test_given_real_pit_when_decision_built_then_decision_documents_test_classpath_assumption`

## Consequences

### Positive
- The PIT policy is correct: `test-compile` is sufficient.
- The 2 BDD tests pin the contract. Future regressions (someone
  adding `verify`, removing the chain, etc.) are caught at
  test time.
- The docstring now correctly documents the Maven lifecycle
  reasoning, so future readers don't have to re-derive it.

### Negative
- None directly. The fix is documentation + 2 tests; no
  behavior change.

### Neutral
- The mutmut policy (`evaluate_real_mutmut_policy`) has the
  same `test-compile` semantics and is consistent with this
  decision. The pre-existing finding P2 (in the 2026-06-13
  code-review) noted that mutmut policy wasn't updated; this
  ADR documents the design decision that applies to both.

## Follow-up

- (PR #40) PIT policy with `test-compile` chain.
- (PR #41, story 030) Docstring fix + 2 BDD tests.
- (future) If PIT ever requires `process-test-resources`
  explicitly (e.g. for a non-standard test resources phase),
  the test will fail and the docstring will be updated.

## More Information

- Story markdown: `workflows/application-mutation-testing/stories/026_pit_policy_setup.md`
- Story markdown (docstring fix): `workflows/application-mutation-testing/stories/030_pit_policy_doc_clarify.md`
- PR (PIT setup): https://github.com/johrenberger/aiWorkflows/pull/40
- PR (docstring fix): https://github.com/johrenberger/aiWorkflows/pull/41
- Merge commits: `20b184a` (PIT), `5e49257` (docstring fix)
- Calibration: this ADR was identified by `code-change-review`
  reproducer as finding "design decision about Maven lifecycle
  chain" on the PR #40 and PR #41 diffs (calibration pass #5 of 5+).
- **Lesson logged in memory:** the original review's H2 said
  "should chain `process-test-resources`" — wrong. The actual
  right fix was documentation. The reproducer correctly
  identified H2 as a documentation issue (calibration test
  passed).
