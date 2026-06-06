# app-dev-discovery

OpenClaw workflow that analyzes a GitHub repository and generates a complete developer
onboarding / architecture discovery guide.

## What it does

Given a GitHub repository URL, the workflow:

1. Clones (or fetches) the repo.
2. Runs an AI agent through 18 phases of analysis (file inventory → stack detection →
   flows → risks → contradiction detection → onboarding doc generation).
3. Validates the output against a checklist (commit-pinned URLs, required sections,
   Mermaid diagrams, confidence scoring).
4. Creates a `docs/app-dev-discovery-<date>` branch, commits the generated docs, and
   pushes (best-effort).

The agent writes 16 evidence files to `.openclaw/app-dev-discovery/` for recoverability,
then rolls them up into a single onboarding document at
`docs/<yyyy-mm-dd>-<repo-name>-app-dev-discovery.md` plus two ADRs.

## Files

```
app-dev-discovery/
├── README.md            # this file
├── prompt.md            # the agent prompt (single source of truth for phases 1-16)
├── run.sh               # runner: parse args, clone, scaffold, invoke agent, validate, commit
├── scripts/
│   └── validate.sh      # Phase 17 validation gate
└── templates/
    ├── 00-run-metadata.md
    ├── 01-file-inventory.md
    ├── 02-documentation-evidence.md
    ├── 03-stack-evidence.md
    ├── 04-structure-evidence.md
    ├── 05-components-evidence.md
    ├── 06-flows-evidence.md
    ├── 07-data-evidence.md
    ├── 08-dependencies-integrations-evidence.md
    ├── 09-api-evidence.md
    ├── 10-testing-evidence.md
    ├── 11-error-logging-evidence.md
    ├── 12-security-evidence.md
    ├── 13-build-deploy-evidence.md
    ├── 14-risk-hygiene-evidence.md
    ├── 15-contradiction-detection.md
    └── 16-final-validation.md
```

## Usage

```bash
# from the workflow dir, or anywhere with the absolute path
./run.sh https://github.com/<org>/<repo>

# with options
./run.sh https://github.com/<org>/<repo> \
  --workspace /tmp/discover \
  --keep-temp       # keep .openclaw/app-dev-discovery/ after success
  --dry-run         # scaffold + write prompt, do not invoke agent
```

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | success |
| 2 | bad usage |
| 3 | repository acquisition failed |
| 4 | agent invocation failed |
| 5 | validation failed (no commit) |
| 6 | push failed (commit is still local) |

## The spec ↔ the runner

- The spec from `app-dev-discovery-workflow---83cb00a0.md` is the authoritative
  contract. It's transcribed verbatim into `prompt.md`.
- `run.sh` is a thin shim around the spec: it handles the boring parts (clone,
  scaffold, commit, push) so the agent can focus on the 18 analysis phases.
- `validate.sh` enforces Phase 17 mechanically. It checks file presence, section
  presence, commit-pinned URL pattern, Mermaid blocks, and confidence scoring.

## When to use it

- Joining an unfamiliar repo and need a fast, evidence-backed map of it.
- Generating onboarding docs as part of a docs-as-code workflow.
- Producing an architecture baseline (ADR-001) before the next refactor.
- Doing diligence on an open-source dependency.

## When not to use it

- The repo is huge (>1M LoC) without a narrow scope — agent context will overflow.
- You only need a quick look — `tree` + `README` will be faster.
- The repo is private and you don't have clone access.

## Customizing

- Edit `prompt.md` to add repo-specific instructions (e.g. "ignore the
  `legacy/` directory") before invoking.
- Edit `templates/0?-*.md` to pre-fill structure (e.g. a known CI provider)
  so the agent doesn't have to rediscover it.
- The 16 evidence files are intentionally minimal — the agent should fill them
  from real evidence, not from assumptions.
