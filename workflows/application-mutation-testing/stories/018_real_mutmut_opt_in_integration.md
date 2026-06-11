# Story 018: Real Mutmut Opt-In Integration

## Goal

Expose a real `mutmut` path only when explicit local safety policy permits it.

## Acceptance Scenarios

- Real tools and mutmut are disabled by default.
- Existing executable, local repository, clean tree, bounded targets, and timeout are required.
- Integration execution tests are environment-gated.

## Executable Test Mapping

`tests/bdd/test_018_real_mutmut_opt_in_integration.py`

## Done Criteria

- Policy and command decisions persist and render.
- Normal tests never execute real mutmut.
