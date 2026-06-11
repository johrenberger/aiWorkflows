# Story 001: CLI and Config Contract

## Goal

As a workflow user, I need a stable CLI and config contract so that mutation workflows can be run consistently across repositories.

## Acceptance Scenarios

### Scenario 001.1: CLI exposes expected commands

Given `mutationctl` is installed or runnable as a module
When I run `mutationctl --help` or `python -m mutationctl --help`
Then the help output lists the supported subcommands.

### Scenario 001.2: Run command accepts workflow inputs

Given I provide repo URL, branch, mode, thresholds, and safety flags
When config is parsed
Then the resulting config object contains normalized values
And defaults are applied for omitted optional values.

### Scenario 001.3: Unsafe commit defaults to blocked

Given no explicit commit permission is provided
When config is parsed
Then `allow_commit` is false.

### Scenario 001.4: Invalid thresholds fail closed

Given invalid mutation target thresholds
When config is parsed
Then a configuration error is raised
And no workflow run starts.

## Executable Test Mapping

`tests/bdd/test_001_cli_and_config_contract.py`

## Done Criteria

- CLI exists.
- CLI help lists expected commands.
- Config object exists.
- Safety defaults are enforced.
- Invalid config fails closed.
