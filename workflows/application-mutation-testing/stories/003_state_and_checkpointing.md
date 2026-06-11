# Story 003: State and Checkpointing

## Goal

As a long-running workflow, I need durable checkpoint state so mutation testing can resume without losing evidence.

## Acceptance Scenarios

### Scenario 003.1: State database initializes

Given a new run directory
When state initialization runs
Then `.mutation-workflow/state.sqlite` is created
And required tables exist.

### Scenario 003.2: Run metadata is persisted

Given workflow config and repo metadata
When a run is initialized
Then a run record is stored
And can be read back.

### Scenario 003.3: Commands are recorded append-only

Given a command result
When it is recorded
Then command, exit code, duration, status, stdout path, and stderr path are stored.

### Scenario 003.4: Blockers are persisted

Given a blocker is recorded
When state is queried
Then the blocker is returned with status, reason, and evidence.

## Executable Test Mapping

`tests/bdd/test_003_state_and_checkpointing.py`

## Done Criteria

- `state.sqlite` initializes.
- Required directories initialize.
- Run metadata persists.
- Commands persist.
- Blockers persist.
- State APIs are covered by tests.
