# Story 030 — PIT policy: clarify the chained command + test classpath behavior

## Why

The code-review report (`tasks/2026-06-13-skill-progress-review/reports/code-review-report.md`)
flagged H2 as a risk:

> PIT's `mutationCoverage` goal re-runs the test suite. If the user's
> project requires test resources to be on the classpath, `test-compile`
> alone may produce classes that fail to load when PIT runs them.

Investigation (running `mvn test-compile` against the `java_pit_basic`
fixture and confirming Maven's lifecycle phases) shows that
**`test-compile` already includes `process-test-resources`**. Maven's
lifecycle runs ALL phases up to and including the named one, so:

```
mvn test-compile
  → validate
  → initialize
  → ...
  → process-resources
  → compile
  → process-test-sources
  → generate-test-resources
  → process-test-resources   <-- copies test resources
  → test-compile             <-- compiles tests
```

So H2 as written is **incorrect** — `test-compile` already handles
test resources. The real issues that H2 was gesturing at are smaller
and more tractable:

1. The current comment "users who want a fresh test pass before
   mutating can add `verify` to the front themselves" is misleading.
   `verify` runs `integration-test` which we DON'T want by default
   (and which PIT can't mutate). The right advice is `test` (re-runs
   tests; user pays the time cost).

2. The policy's `reasons` list doesn't include anything about
   test-classpath behavior, so a downstream consumer reading the
   decision can't tell that the command is "compile + mutate" rather
   than "mutate" (which would be wrong if you didn't already have
   the project built).

3. The existing test that asserts the command content should also
   assert the **phase order is sensible** (process-test-resources
   comes before test-compile in the lifecycle, so listing `test-compile`
   alone is enough).

## What's in this PR

1. **Fix the misleading comment** in `real_tool_policy.py`. Replace
   "users who want a fresh test pass before mutating can add
   `verify` to the front themselves" with "if you need a fresh test
   pass before mutating (e.g. fixtures change between runs), add
   `test` to the front — note this re-runs the entire test suite
   (2-5x slowdown) so use it only when you trust the test results
   are stale."

2. **Add a reason** to the decision's `reasons` list: "Test resources
   are processed by Maven's lifecycle (process-test-resources is
   included in test-compile); user need not chain it explicitly."

3. **Add 2 new BDD tests** to
   `tests/bdd/test_019_pit_policy_integration.py`:
   - `test_given_real_pit_when_command_built_then_command_does_not_chain_process_test_resources_explicitly`
     — asserts the command is `mvn test-compile org.pitest:...`
     (no explicit `process-test-resources`) AND that the reasons
     explain why.
   - `test_given_real_pit_when_decision_built_then_decision_documents_test_classpath_assumption`
     — asserts the reasons include the test-classpath note.

## Out of scope

- Changing the actual Maven command (test-compile is correct).
- Adding `--add-opens` or other JVM flags (PIT Maven goal handles
  its own JVM).
- The mutmut policy (story 018) which has the same comment, but
  fixing both is a separate story.

## Companion

- aiWorkflows PR #40 (story 026): shipped the PIT policy and the
  chained command.
- aiWorkflows PR #39 (story 025) + PR (story 029): sibling in v2
  for the orchestrator side.
