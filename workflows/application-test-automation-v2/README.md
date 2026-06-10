# Application Test Automation v2

Deterministic workflow for discovering coverage gaps in large codebases, prioritizing the highest-risk work, preparing bounded GenAI-ready test tasks, validating generated tests, and optionally preparing PR-ready branches.

## Core principles

- Deterministic tooling owns discovery, inventory, coverage parsing, mapping, scoring, queueing, validation, mutation detection, reporting, and branch/commit safety.
- GenAI only receives bounded work items for semantic test creation and repair.
- The workflow never silently excludes files. Every exclusion is recorded in artifacts.

## CLI

```text
test-factory scan --repo PATH --out analysis-artifacts
test-factory coverage --repo PATH --out analysis-artifacts
test-factory score --repo PATH --out analysis-artifacts
test-factory queue --repo PATH --out analysis-artifacts
test-factory workitems --repo PATH --out analysis-artifacts --limit N
test-factory validate --repo PATH --out analysis-artifacts --work-item-id ID
test-factory mutate --repo PATH --out analysis-artifacts
test-factory report --repo PATH --out analysis-artifacts
test-factory run --repo PATH --out analysis-artifacts --limit N
test-factory branch --repo PATH --scope MODULE
test-factory commit --repo PATH --module MODULE
test-factory pr-summary --repo PATH --out analysis-artifacts
```

## Installation

This workflow is intentionally light on dependencies and uses the Python standard library plus `pytest` for tests.

```bash
python -m pip install -e .
python -m pytest
```

## Configuration

Copy `test_factory.yaml.example` into the repository root as `test_factory.yaml` and adjust thresholds, exclusions, or mutation settings as needed.

