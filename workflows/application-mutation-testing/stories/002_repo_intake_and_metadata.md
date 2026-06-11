# Story 002: Repository Intake and Metadata

## Goal

As the mutation workflow, I need to validate repository inputs and capture local Git metadata so all evidence is tied to a specific branch and commit.

## Acceptance Scenarios

### Scenario 002.1: GitHub repository URL is validated

Given a valid GitHub repository URL
When repo intake validates the input
Then the URL is accepted
And normalized.

### Scenario 002.2: Invalid repository URL is rejected

Given a malformed repository URL
When repo intake validates the input
Then the workflow fails closed
And produces a blocker/error.

### Scenario 002.3: Local Git metadata is captured

Given a local synthetic Git repository
When metadata capture runs
Then branch, commit SHA, dirty status, and timestamp are recorded.

### Scenario 002.4: Dirty tree is detected

Given a local Git repository with uncommitted changes
When metadata capture runs
Then dirty status is true.

## Executable Test Mapping

`tests/bdd/test_002_repo_intake_and_metadata.py`

## Done Criteria

- Repo URL validation works.
- Local path validation works.
- Local Git metadata capture works.
- Dirty tree detection works.
- Metadata model exists.
