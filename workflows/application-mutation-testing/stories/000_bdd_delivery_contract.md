# Story 000: Establish BDD-First Delivery Contract

## Goal

As the application builder, I need a BDD-first delivery structure so that every capability is specified before implementation.

## Acceptance Scenarios

### Scenario 000.1: Stories directory exists

Given the project is initialized
When I inspect the repository
Then a `stories/` directory exists
And each first-pass story file has a goal, acceptance scenarios, executable test mapping, and done criteria.

### Scenario 000.2: BDD test directory exists

Given the project is initialized
When I inspect the test structure
Then a `tests/bdd/` directory exists
And each first-pass story has a corresponding pytest file.

### Scenario 000.3: Pytest can collect BDD tests

Given the project skeleton exists
When pytest collection runs
Then the BDD tests are discoverable
And import errors do not prevent collection.

## Executable Test Mapping

`tests/bdd/test_000_bdd_delivery_contract.py`

## Done Criteria

- `stories/` exists.
- `tests/bdd/` exists.
- First-pass story files exist.
- First-pass BDD test files exist.
- Pytest can collect tests.
