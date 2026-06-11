# Story 004: Ledger Rendering

## Goal

As a workflow user, I need `TODO_mutation-testing.md` rendered from structured state so the ledger is reliable and reviewable.

## Acceptance Scenarios

### Scenario 004.1: Ledger is rendered from state

Given state contains repo metadata, config, command records, blockers, and validation statuses
When the ledger renderer runs
Then `TODO_mutation-testing.md` is generated
And includes all required sections.

### Scenario 004.2: Missing mutation score is not invented

Given no mutation result exists
When the ledger is rendered
Then no numeric mutation score is shown
And mutation results are marked `NOT_RUN`.

### Scenario 004.3: Blockers are rendered with evidence

Given a blocker exists in state
When the ledger is rendered
Then the blocker reason and evidence appear in the Markdown.

### Scenario 004.4: Ledger task IDs are stable

Given ledger tasks exist in state
When the ledger is rendered multiple times
Then task IDs remain stable.

## Executable Test Mapping

`tests/bdd/test_004_ledger_rendering.py`

## Done Criteria

- Ledger renderer exists.
- `TODO_mutation-testing.md` is generated.
- Required sections exist.
- Missing mutation evidence is explicit.
- Blockers render with evidence.
- Task IDs are stable.
