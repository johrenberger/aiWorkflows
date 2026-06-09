# repo-discovery-analyzer

OpenClaw workflow for building the deterministic `repo-discovery-analyzer` Python
CLI in a target repository.

## What it does

Given a GitHub repository URL, this workflow:

1. Clones or reuses the target repo.
2. Guides an agent through implementing the analyzer package, CLI, tests, and
   validation helpers described in the requirements.
3. Validates that the expected repository structure exists.
4. Commits the generated implementation on a feature branch and pushes it when
   credentials are available.

The workflow is designed to produce the implementation artifacts expected by the
requirements document:

`repo_discovery_analyzer/`, `tests/`, `pyproject.toml`, and supporting docs.

The repository also carries a local implementation prototype under
`implementation/` so the analyzer can be exercised and iterated on in this
workspace.

Analyzer runs finish by rendering `analysis_report.md` from the generated JSON
evidence. The report summarizes repository scale, stack, structure, entry
points, routes, data models, dependencies, integrations, tests, security,
operations, hygiene findings, contradictions, warnings, and evidence files.

## Files

```text
repo-discovery-analyzer/
├── README.md
├── workflow.md
├── prompt.md
├── run.sh
├── recovery.md
├── output-template.md
├── scripts/
│   └── validate.sh
└── implementation/
    ├── README.md
    ├── pyproject.toml
    ├── repo_discovery_analyzer/
    └── tests/
└── templates/
    ├── 00-run-metadata.md
    ├── 01-implementation-plan.md
    └── 02-validation-checklist.md
```

## Usage

```bash
./run.sh https://github.com/<org>/<repo>
```

Optional flags:

```bash
./run.sh https://github.com/<org>/<repo> \
  --workspace /tmp/repo-discovery-analyzer \
  --keep-temp \
  --dry-run
```

## When to use it

- You need the analyzer implemented from a requirements brief.
- You want a deterministic, evidence-backed Python CLI package.
- You want the generated code to be validated before commit.

## Relationship to the requirements

This workflow operationalizes the attached `repo-discovery-analyzer`
requirements by turning them into a repeatable agent prompt and a validation gate.
