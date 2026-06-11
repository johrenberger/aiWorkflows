# mutationctl

`mutationctl` is a deterministic control plane for application mutation testing workflows. The current foundation covers CLI/configuration, repository intake, durable state, local tool and coverage evidence, bounded target selection, fake baseline execution, result normalization, survivor packets, deterministic pre-classification, fake-only LLM contracts, patch safety, validation gates, fake mutation recheck, branch-safe commit planning, synthetic end-to-end runs, opt-in real-mutmut policy, and Markdown reporting.

## Deterministic vs Future LLM-Driven

Deterministic in this pass:

- CLI contract and safe command stubs
- GitHub URL and local path intake
- Local Git metadata capture
- SQLite-backed checkpoint state
- Python, JavaScript, and Java mutation-tool evidence detection
- TODO ledger, Cobertura XML, and LCOV coverage ingestion
- bounded deterministic target scoring and selection
- scoped `mutmut` command construction through a controlled runner
- fixture-driven mutmut, Stryker, and PIT result normalization
- compact source/test survivor packets with deterministic truncation
- evidence-backed deterministic survivor pre-classification
- schema-validated fake LLM classification requests and responses
- conservative unified-diff parsing and test-weakening detection
- controlled synthetic-workspace patch application and revert
- evidence-backed `MT-VAL-1` through `MT-VAL-12` validation gates
- fixture-driven mutation recheck using the original baseline scope
- branch-safe commit plans and fake Git execution
- report-only and fake-implementation synthetic workflows
- final summary rendering
- explicit real-mutmut policy with clean-tree, executable, target, timeout, and platform checks
- `TODO_mutation-testing.md` rendering from state

Future phases may harden schemas and reporting, expand real-tool policies to Stryker and PIT, or connect the application-test-coverage ledger as first-class targeting input.

## Safety Defaults

- `allow_commit = false`
- `allow_dependency_install = false`
- `allow_production_fixes = false`
- `allow_test_changes = false`
- default mode is `report`

## Run The CLI

```bash
python -m mutationctl --help
```

## Run Tests

```bash
python -m pytest tests/bdd
python -m pytest
```

## Current Scope

Stories `000–018`:

- BDD delivery contract
- CLI and config contract
- repo intake and metadata
- state and checkpointing
- ledger rendering
- language and mutation-tool detection
- coverage ingestion
- deterministic target selection
- fake mutation baseline execution
- mutation result normalization
- survivor packet generation
- deterministic survivor classification
- fake-only LLM contracts
- test patch safety
- validation gates
- mutation recheck
- commit gate and branch-safe planning
- end-to-end synthetic workflow
- opt-in real mutmut integration policy
