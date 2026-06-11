# Story 005: Language and Mutation Tool Detection

## Goal

As the workflow, I need deterministic language and mutation tool detection so supported mutation commands are selected from project evidence.

## Acceptance Scenarios

- Given Python project evidence, when detection runs, then Python and its evidence files are recorded.
- Given `mutmut`, Stryker, or PIT dependency evidence, when tool detection runs, then the matching tool is selected.
- Given no supported tool and installation is disabled, when detection runs, then a blocker is persisted.

## Executable Test Mapping

`tests/bdd/test_005_language_and_tool_detection.py`

## Done Criteria

- Local-only language and tool detection works.
- Detection evidence persists.
- Missing tooling produces a blocker.
- Ledger renders detection evidence.
