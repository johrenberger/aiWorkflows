# aiWorkflows

Curated, reusable OpenClaw workflows. Each workflow is a self-contained bundle:
runner script + agent prompt + validation gate + evidence templates.

## Workflows

| Workflow | Description | Status |
| --- | --- | --- |
| [`workflows/app-dev-discovery/`](workflows/app-dev-discovery/) | Analyzes a GitHub repo and generates a developer onboarding / architecture discovery guide | v1 (tested on johrenberger/creative-ai) |
| [`workflows/repo-discovery-analyzer/`](workflows/repo-discovery-analyzer/) | Builds the deterministic Python CLI that analyzes a local GitHub checkout and emits structured evidence JSON | prototype implementation in progress |

## Conventions

- Each workflow is a single directory: `<workflow-name>/`
- Contains: `run.sh` (entrypoint), `prompt.md` (agent prompt), `scripts/validate.sh` (validation), `templates/` (evidence scaffolds), `README.md` (usage)
- Workflows use `GITHUB_TOKEN` (env) → `GH_TOKEN` → `gh auth token` → anonymous (priority order) for git auth
- Workflows suppress the global git `credential.helper` to avoid token leaks
- All output goes to `docs/` in the target repo; evidence scaffolding goes to `.openclaw/<workflow>/` and is cleaned up by default

## How a workflow is added

1. Create a directory under `workflows/<name>/`
2. Implement the four-file minimum: `run.sh`, `prompt.md`, `scripts/validate.sh`, `README.md`
3. Add evidence `templates/` if the workflow needs intermediate artifacts
4. Open a PR; CI will run the workflow's `validate.sh --selftest` if defined
