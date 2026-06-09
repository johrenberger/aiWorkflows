# aiWorkflows — Project Notes

This file is the entry point for **project-level documentation**: smoke-test results, lessons learned, the design rationale behind the workflow layout, and links to reusable patterns. Workflows themselves live in their own subdirectories; this file stays thin and points to the rest.

## What this repo is

Reusable OpenClaw workflows for software engineering tasks. Each workflow is a self-contained bundle of:

- A **spec** (`prompt-implementation.md` or `prompt.md`) — the multi-phase procedure for an agent to follow.
- A **validation file** (`validation.md`) — the `*-VAL-*` gates that the workflow must pass.
- A **recovery file** (`recovery.md`) — how to recover from a partial run.
- An **output template** (`output-template.md`) — the schema for the per-run ledger.
- A **README** and **workflow.md** — overview and architectural notes.
- Optional **scripts** (gate validators, run scripts) and **templates** (per-phase forms).

Cross-workflow rules live in `workflows/shared/` — a single source of truth for evidence standards, output rules, recovery model, etc. Each workflow's prompt references those paths.

## Current workflows

| Workflow | Purpose | Status | Phase count |
|---|---|---|---|
| [`api-testing-workflow/`](api-testing-workflow/) | Smoke-test a live HTTP API (k6 + pytest) | Stable | 15 |
| [`app-dev-discovery/`](app-dev-discovery/) | Map a codebase's architecture, data, and tests | Stable | 17 |
| [`repo-discovery-analyzer/`](repo-discovery-analyzer/) | Build the deterministic repo discovery analyzer CLI | Prototype implementation in progress | 1 |
| [`application-test-coverage/`](application-test-coverage/) | Bring test coverage to 90%+ per file | **Smoke-tested 2026-06-07** | 15 |
| [`application-mutation-testing/`](application-mutation-testing/) | Mutation testing to validate test-suite quality | Smoke-tested 2026-06-07 (gates passed; tool install blocked by default) | 17 |
| [`component-test-analysis/`](component-test-analysis/) | Read-only analysis of a repo's component-level testing strategy; emits machine-readable gap backlog | Shipped 2026-06-08; first real run against `creative-ai` | 9 |
| [`component-test-generation/`](component-test-generation/) | Consumes `component-test-analysis` output and **generates runnable test files** in the target repo | Shipped 2026-06-08 | 9 |

## Layout convention

```
workflows/
├── <workflow-name>/
│   ├── README.md              # entry point for users
│   ├── workflow.md            # architectural notes
│   ├── prompt-implementation.md  # the multi-phase procedure
│   ├── validation.md          # *-VAL-* gates
│   ├── recovery.md            # recovery from partial runs
│   ├── output-template.md     # ledger schema
│   ├── scripts/               # optional: validate.sh, run.sh
│   └── templates/             # optional: per-phase forms
└── shared/                    # cross-workflow rules
    ├── evidence-standards.md
    ├── implementation-guardrails.md
    ├── output-rules.md
    ├── recovery-model.md
    ├── repo-discovery.md
    └── repo-input-contract.md
```

**Branch naming:** `workflows/<workflow-name>-YYYY-MM-DD` off `main`.

**Commit identity:** `clawdexter@openclaw.local` / `Clawdexter`.

## Smoke-test history

### 2026-06-07: coverage + mutation workflows against `pytest-fastapi-crud-example`

**Target repo:** https://github.com/johrenberger/pytest-fastapi-crud-example
**Test surface:** FastAPI + SQLAlchemy + pytest, 6 application source files.

**Run 1 — surface + block:**

- Aggregate coverage: 89.3% (computed, but **misleading** — 7 tests were silently failing).
- Pre-existing baseline failures: 7, traced to 3 production bugs:
  1. `except Exception` swallowed `HTTPException(404)` → 500 (4 tests)
  2. `userId: str` accepted garbage; SQLAlchemy `UUIDType` crashed → 500 (3 tests)
  3. `UserBaseSchema` required all fields on PATCH → 422 (1 test)
- Coverage workflow stopped at TC-CKPT-9 per spec rule "don't implement on broken baseline."
- Mutation workflow: blocked, no mutation tool installed (`ALLOW_DEPENDENCY_INSTALL=false`).
- Result: 10/13 TC-VAL-* gates passed; 3 deferred per blocker (TC-VAL-2/5/7 needed v2 ledger).
- **Fix:** PR #3 on target repo (`fix(user): correct 404/422/partial-patch behavior to match tests + contract`), merged 15:14 UTC.

**Run 2 — re-run after fix:**

- Baseline: 0 failures, 53/60 tests pass, 2 skip.
- Coverage workflow: 6/6 files at 90%+, aggregate 95.7%, all 13 TC-VAL-* gates pass.
- 6 tests added (PR #4 on target repo), merged.
- Coverage breakdown post-run:

  | File | Baseline | Final | Δ |
  |---|---:|---:|---:|
  | `app/__init__.py` | 100.0% | 100.0% | — |
  | `app/database.py` | 66.7% | 100.0% | +33.3pp |
  | `app/main.py` | 100.0% | 100.0% | — |
  | `app/models.py` | 100.0% | 100.0% | — |
  | `app/schemas.py` | 100.0% | 100.0% | — |
  | `app/user.py` | 71.8% | 91.0% | +19.2pp |
  | **TOTAL** | **83.9%** | **95.7%** | **+11.8pp** |

- The 7 missing lines in `user.py` are defensive `except HTTPException: raise` arms that require contrived tests; documented as `TC-GAP-1` in the ledger, not a blocker.

## Reusable test patterns

- **[Wrapped-commit pattern](_docs/test-pattern-wrapped-commit.md)** — for testing exception handlers in code that uses a real database. Generalizable across ORMs and HTTP frameworks.

## Open follow-ups

- **CI** for the workflows themselves: a `.github/workflows/ci.yml` that runs the gate validators on every PR.
- **Mutation workflow run** against `pytest-fastapi-crud-example` (codebase is now stable and well-covered). Needs `ALLOW_DEPENDENCY_INSTALL=true` to install `mutmut`.
- **"How to contribute" guide** for adding new workflows (the file layout is convention, not enforced).
- **`component-test-generation` smoke test** against `creative-ai` analysis output (PR #2 on `johrenberger/creative-ai`). Profile: `safe` + `DRY_RUN=true` for first contact.
