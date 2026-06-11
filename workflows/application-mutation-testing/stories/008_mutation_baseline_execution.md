# Story 008: Mutation Baseline Execution

## Goal

As the workflow, I need scoped mutation commands executed through a controlled runner so baseline mutation evidence is captured consistently.

## Acceptance Scenarios

- Given a Python target and `mutmut`, when a command is built, then it is scoped to that file.
- Given fake success or timeout results, when baseline execution runs, then evidence persists.
- Given no detected tool, when execution is requested, then no command runs and a blocker is recorded.

## Executable Test Mapping

`tests/bdd/test_008_mutation_baseline_execution.py`

## Done Criteria

- Adapter interface and mutmut adapter exist.
- Fake baseline results and timeouts persist.
- Missing tools fail closed.
