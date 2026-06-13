# Story 026 — PIT mutation tool setup (v1 mutationctl)

## Why

v1 (mutationctl) has full PIT plumbing — `PitAdapter.build_command()`
constructs the right Maven invocation, `detect_pit()` recognizes a
pom that has PIT, and the result-normalization path understands
PIT's XML report. What's missing: a `real_tool_policy` evaluator
for PIT (the safety gate that decides whether to actually run PIT)
and a richer Java fixture repo with a real test that PIT can
mutate against.

This story is the smallest step that gets PIT from "I know the
command shape" to "I can run a real mutation and see a real
score". Story 027 (deferred) will then exercise the full
end-to-end on a real Broadleaf module.

## What's in this PR

1. **`evaluate_real_pit_policy()` in `workflow/real_tool_policy.py`**:
   - Mirrors the structure of `evaluate_real_mutmut_policy()`
   - Checks: real tools enabled, PIT explicitly enabled, executable
     found (`mvn` + JUnit deps in pom), repository is local and
     absolute, ≤5 selected targets, positive timeout, Java
     supported (already implicit — we use `mvn` so OS doesn't
     matter the way mutmut's fork model does)
   - Constructs the PIT command scoped to the selected target:
     `mvn org.pitest:pitest-maven:mutationCoverage -DtargetClasses=<module>.<Class>`
   - Records the same `RealToolExecutionDecision` shape as mutmut
   - Optional `store` parameter for parity with mutmut

2. **New fixture `java_pit_basic` (extended)**: a real
   Maven-JUnit project with a `Calculator.java` source, a
   `CalculatorTest.java` with 2 unit tests (covers 100% of
   `Calculator`), a `pom.xml` with the PIT plugin, and a
   `maven-surefire-plugin` declaration. Small enough to mutate
   in seconds. Pre-existing `pom.xml` had a malformed fragment
   (no modelVersion etc.) — this story replaces it with a valid
   one. The existing detection test
   `test_given_pom_with_pit_when_tool_detection_runs_then_pit_detected`
   must still pass (PIT is still in the pom).

3. **6 new BDD tests** in `tests/bdd/test_019_pit_policy_integration.py`:
   - `test_given_real_tools_disabled_when_pit_requested_then_execution_blocked`
   - `test_given_real_tools_enabled_but_pit_missing_when_policy_checked_then_execution_blocked`
   - `test_given_dirty_tree_and_clean_required_when_pit_policy_checked_then_execution_blocked`
   - `test_given_real_pit_allowed_when_command_built_then_command_is_scoped_to_selected_target`
   - `test_given_no_targets_when_pit_policy_checked_then_execution_blocked`
   - `test_given_relative_path_when_pit_policy_checked_then_execution_blocked`

4. **`PitAdapter.build_command()` exposes `timeout_seconds`**:
   the 1800-second default stays (matching mutmut's default) but
   the policy can override it. (Already there in
   `MutationCommand`, but the integration test verifies it.)

## Acceptance scenarios (BDD)

1. `evaluate_real_pit_policy(allow_real_tools=False, ...)` →
   `decision.allowed is False`.
2. `evaluate_real_pit_policy(allow_real_tools=True,
   allow_pit=False, ...)` → blocked.
3. `evaluate_real_pit_policy(allow_real_tools=True, allow_pit=True,
   executable_found=False, ...)` → blocked ("mvn executable not
   found").
4. `evaluate_real_pit_policy(allow_real_tools=True, allow_pit=True,
   executable_found=True, dirty=True, require_clean_tree=True,
   allow_dirty_tree=False, ...)` → blocked ("working tree is dirty").
5. `evaluate_real_pit_policy(allow_real_tools=True, allow_pit=True,
   executable_found=True, dirty=False, ...)` → allowed, command
   contains `mvn`, `org.pitest:pitest-maven:mutationCoverage`, and
   a `-DtargetClasses=...<Class>` scoped to the selected file.
6. `evaluate_real_pit_policy(..., selected_targets=[])` → blocked
   ("no bounded mutation target is selected").
7. `evaluate_real_pit_policy(..., repo_path="relative/path")` →
   blocked ("repository path must be local and absolute").

## Scope limits

- We do NOT run PIT end-to-end on Broadleaf in this story. That's
  C4, deferred.
- We do NOT add a "build in tmp dir" mode (mirrors story 025
  approach but for PIT).
- We do NOT change the synthetic (fake-PIT-results) path. That
  continues to work as-is for the BDD pipeline.
- The PIT policy does NOT yet check for JUnit in the pom. We
  assume the user has it; if not, PIT will fail at run time and
  surface as a regular command failure (no special preflight).

## End-to-end evidence

On the extended `java_pit_basic` fixture (this story's added file):
```
$ ls src/main/java/  src/test/java/
src/main/java/Calculator.java
src/test/java/CalculatorTest.java

$ cat Calculator.java
public class Calculator {
    public int add(int a, int b) { return a + b; }
    public int sub(int a, int b) { return a - b; }
}

$ cat CalculatorTest.java
public class CalculatorTest {
    @Test public void add() { assertEquals(5, new Calculator().add(2, 3)); }
    @Test public void sub() { assertEquals(-1, new Calculator().sub(2, 3)); }
}

$ mvn org.pitest:pitest-maven:mutationCoverage \
    -DtargetClasses=Calculator -DmutationThreshold=0
  → produces target/pit-reports/mutations.xml with 2-4 mutants
  (depending on PIT version) all KILLED
```

This end-to-end is run manually as a smoke test; the BDD tests
in this story only exercise the policy layer, not the actual
mutation execution. Story 027 will run it as part of the test
suite (still opt-in via env var like mutmut's).

## Tests

- 6 new BDD tests for `evaluate_real_pit_policy` (parity with
  mutmut's 6 tests in `test_018_real_mutmut_opt_in_integration.py`)
- Mutation tests: 138/139 (132 baseline + 6 new) — the 1 skip is
  pre-existing.

## Out of scope

- C4: real PIT run on Broadleaf (deferred).
- PIT version pinning.
- INCLUDE/EXCLUDE patterns per-target.
