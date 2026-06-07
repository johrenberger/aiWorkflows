# api-testing-workflow

OpenClaw workflow that analyzes a target API project and produces a complete,
evidence-backed API testing package: surface inventory, normalized contract,
executable test suites, security baseline, observability recommendations, and
defect reports.

The target is provided as a **GitHub repository URL**. The workflow clones it,
runs an AI agent through 17 stages (intake → discovery → contract → planning
→ tests → security → perf plan → resilience plan → observability → execution
→ triage → drift → summary), validates the output, and commits a
`docs/api-testing-<date>` branch back to the target repo (best-effort).

## What it produces

```
<target-repo>/
├── docs/
│   ├── api-testing-<yyyy-mm-dd>.md           # single, human-readable summary
│   └── adr/
│       ├── 000-template.md
│       └── 001-api-contract-baseline.md
├── artifacts/                                # all machine-readable evidence
│   ├── api_testing_context.md
│   ├── api_inventory.json
│   ├── openapi.normalized.yaml
│   ├── api_test_plan.md
│   ├── api_security_findings.md
│   ├── api_performance_plan.md
│   ├── api_resilience_plan.md
│   ├── api_observability_recommendations.md
│   ├── api_test_results.json
│   ├── api_defect_report.md
│   ├── api_change_log.md
│   ├── api_workflow_summary.md
│   └── history/                              # baseline for repeat-run drift
├── tests/
│   ├── api/                                  # pytest + httpx functional tests
│   ├── contract/                             # schemathesis / jsonschema contract tests
│   ├── performance/                          # (plan-only by default)
│   └── resilience/                           # (plan-only by default)
├── scripts/
│   ├── discover_api.py
│   ├── normalize_openapi.py
│   ├── run_api_tests.sh
│   └── generate_api_report.py
├── tests/api/client.py
├── tests/api/conftest.py
└── TODO_api-tester.md                        # human-readable task tracker
```

## Usage

```bash
# from the workflow dir, or anywhere with the absolute path
./run.sh https://github.com/<org>/<repo>

# with options
./run.sh https://github.com/<org>/<repo> \
  --workspace /tmp/api-test \
  --keep-temp       # keep .openclaw/api-testing/ after success
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

- The spec is the authoritative contract. It's transcribed verbatim into
  `prompt.md`.
- `run.sh` is a thin shim around the spec: it handles the boring parts (clone,
  scaffold, commit, push) so the agent can focus on the 17 analysis stages.
- `validate.sh` enforces Stage 16 mechanically. It checks artifact presence,
  test-file presence, required sections in the summary, and the safety gates
  (no secrets in artifacts, destructive tests gated, etc.).

## Input

The spec accepts many input shapes (local path, base URL, OpenAPI, Postman,
local tests, etc.). **This runner restricts input to a GitHub URL.** If you
need a different input, copy the spec into a new variant of `run.sh` and
adapt the acquisition phase.

## Safe defaults

The spec defines safe defaults that the agent MUST follow unless explicitly
overridden in the run command:

- `patch_application_code: false`
- `commit_changes: false` (the runner commits on its own after validation)
- `allow_destructive_tests: false`
- `allow_production_load_tests: false`
- `include_performance_tests: false` (plan only)
- `include_resilience_tests: false` (plan only)
- `include_chaos_tests: false` (plan only)
- `fail_on_contract_drift: true`

## When to use it

- Pre-release API hardening (security baseline, contract tests).
- Onboarding to a new API surface.
- Drift detection between API states across releases.
- Producing an evidence-backed "is this API production-ready?" assessment.

## When not to use it

- The repo is huge (>1M LoC) without a narrow scope — agent context overflows.
- You only need a single endpoint smoke test — `curl` + a shell script is faster.
- The repo is private and you don't have clone access.

## Customizing

- Edit `prompt.md` to add repo-specific instructions before invoking.
- Edit `templates/0?-*.md` to pre-fill structure (e.g. a known framework) so
  the agent doesn't have to rediscover it.
- The 15 evidence files are intentionally minimal — the agent should fill
  them from real evidence, not from assumptions.
