# OpenClaw Workflow Prompt: App Developer Discovery

> This file is the canonical prompt that drives the `app-dev-discovery` workflow.
> It is passed to the executing agent (via `agent --message`, subagent spawn, or
> a TaskFlow job). Keep it in sync with the spec — the spec is in `../SPEC.md` or
> the version this was generated from.

---

## Runtime Inputs

The workflow accepts exactly one required runtime variable:

- `GITHUB_PROJECT_URL` — the GitHub repository to analyze (e.g. `https://github.com/<org>/<repo>`).

Optional environment variables consumed by the runner script:

- `WORKSPACE_DIR` — working directory for the analysis. Default: the cloned repository.
- `KEEP_TEMP` — if `true`, the `.openclaw/app-dev-discovery/` evidence directory is preserved on success. Default: `false`.
- `DRY_RUN` — if `true`, do not commit or push. Default: `false`.

## Mission

You are an AI coding agent operating inside an existing source-code workspace.

Your task is to produce a reliable, evidence-backed technical onboarding document for a developer who has just joined this project.

Do not guess. Ground every material claim in repository evidence.

The final document must explain:

- architecture
- features
- main flows
- key components
- technology stack
- database/schema
- APIs
- integrations
- testing
- error handling
- logging
- security
- build/deploy/infrastructure
- architecture risks
- developer productivity guidance
- discovery confidence

## Operating Principles

Optimize for: reliability, recoverability, bounded context, validation, observability, synthesis quality, platform fit, evidence discipline.

Rules:

1. Analyze the full project/workspace.
2. Do not rely only on README files.
3. Prefer source code, config, schemas, tests, and deployment files as primary evidence.
4. Mark uncertain conclusions explicitly.
5. Never invent technologies, flows, APIs, diagrams, or dependencies.
6. Use concise representative snippets only.
7. Keep diagrams high-level.
8. Use GitHub commit-pinned URLs for all code references.
9. Generate one final onboarding document that rolls up the data from all sections.
10. Use temporary intermediate evidence files only for workflow recoverability.
11. Do not generate the final document until validation passes.
12. Commit generated docs only after validation passes.

## Execution Discipline (added by runner)

- **Use absolute paths** in every `read`, `write`, `edit`, and `exec` call. The runner
  passes the absolute `WORKSPACE_DIR` in runtime context — use that, not relative paths.
- **Do not spawn sub-agents for the analysis phases.** Do the work inline so evidence
  is consistent and the workflow is atomic. Sub-agents are fine only for isolated
  read-only research, never for mutating the evidence directory.
- **Do not run `openclaw agent`, `openclaw gateway restart`, or any other lifecycle
  command** from inside this workflow.
- **Do not modify or commit anything** — the runner script handles branch creation,
  commit, and push. Your job is to produce the docs/ artifacts and stop.
- **Write short evidence, not essays.** Aim for evidence files of 2-10KB each. The
  final document is the rolled-up synthesis.

## Working Directory Layout

Create inside the target repository (or the cloned checkout):

```
.openclaw/app-dev-discovery/
  00-run-metadata.md
  01-file-inventory.md
  02-documentation-evidence.md
  03-stack-evidence.md
  04-structure-evidence.md
  05-components-evidence.md
  06-flows-evidence.md
  07-data-evidence.md
  08-dependencies-integrations-evidence.md
  09-api-evidence.md
  10-testing-evidence.md
  11-error-logging-evidence.md
  12-security-evidence.md
  13-build-deploy-evidence.md
  14-risk-hygiene-evidence.md
  15-contradiction-detection.md
  16-final-validation.md
```

Final deliverables (in the target repository):

```
docs/<yyyy-mm-dd>-<repo-name>-app-dev-discovery.md
docs/adr/000-template.md
docs/adr/001-current-architecture-baseline.md
```

## Phases

### Phase 0 — Repository Acquisition and Metadata

1. Read `GITHUB_PROJECT_URL`.
2. Clone the repository if needed.
3. If already cloned, confirm the remote matches `GITHUB_PROJECT_URL`.
4. Fetch latest metadata without destructive changes.
5. Determine: owner, repo name, default branch, checked-out branch, current commit hash, remote URL, current date.
6. Build the GitHub source URL prefix: `https://github.com/<org>/<repo>/blob/<commit>/`
7. Save metadata to `.openclaw/app-dev-discovery/00-run-metadata.md`.
8. **Failure rule:** if repository access fails, stop immediately and report the URL, failure, and remediation.

### Phase 1 — Full Repository Inventory

Generate a complete inventory. Include: path, file type, apparent role, whether reviewed directly, whether excluded, exclusion reason.

Exclude only low-value generated/vendor files: `.git/`, `node_modules/`, build artifacts, coverage outputs, binary/media files (unless docs/deploy relevant), lockfile internals.

Do not exclude: application source, configuration, tests, migrations, scripts, infrastructure, CI/CD, docs, public assets.

Save to `.openclaw/app-dev-discovery/01-file-inventory.md`.

### Phase 2 — Documentation and Instruction Review

Find and review: `README.md`, `LEIAME.md`, `CONTRIBUTING.md`, `docs/`, architecture notes, setup guides, runbooks, changelogs, important script comments.

Summarize: project overview, setup/run instructions, conventions, contribution process, documentation gaps.

Save to `.openclaw/app-dev-discovery/02-documentation-evidence.md`.

### Phase 3 — Technology Stack Detection

Inspect: `package.json`, lockfiles, `pom.xml`, `build.gradle`, `.csproj`, `requirements.txt`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `.tool-versions`, `.nvmrc`, `Dockerfile`, `docker-compose`, CI files, env/config templates.

Identify: languages and versions, frameworks, package managers, build tools, database technologies, cloud SDKs/platforms, containerization, message brokers, caching, search/indexing, architecture style, test frameworks, lint/format tools.

Every stack item must include a commit-pinned GitHub URL. Save to `.openclaw/app-dev-discovery/03-stack-evidence.md`.

### Phase 4 — Project Structure and Entry Point Mapping

Identify: main entry points, bootstrap files, routing files, controllers/handlers, services/use cases, models/entities, persistence layer, frontend entry points, background jobs/workers, scripts, configuration files, infrastructure files.

Create a recommended reading path. Save to `.openclaw/app-dev-discovery/04-structure-evidence.md`.

### Phase 5 — Key Component Analysis

For each important component include: name, GitHub URL, responsibility, important classes/functions, dependencies, downstream consumers, representative snippet, reason it matters.

Prioritize components that affect: app startup, request handling, domain logic, persistence, authn/authz, integrations, background processing, deployment/runtime.

Save to `.openclaw/app-dev-discovery/05-components-evidence.md`.

### Phase 6 — Execution and Data Flow Analysis

Trace critical flows end-to-end (auth, request handling, CRUD, jobs, message processing, file upload/download, external API interaction).

For each flow include: trigger, entry point, major steps, data read/write behavior, error handling, key files/functions, persistence target, external services involved.

Save to `.openclaw/app-dev-discovery/06-flows-evidence.md`.

### Phase 7 — Database and Schema Analysis

If persistence exists, identify: database type, ORM/query layer, entities/tables/collections, relationships, migrations, seed data, repository/DAO patterns, critical indexes/constraints.

If none found, state explicitly: "no clear persistence layer was found" with evidence. Save to `.openclaw/app-dev-discovery/07-data-evidence.md`.

### Phase 8 — Dependencies, Integrations, and APIs

Analyze: major libraries and their role, SDKs, external APIs, auth providers, payment/email/storage/search/queue integrations, message brokers, API documentation mechanisms.

For APIs identify: endpoint definitions, routing structure, OpenAPI/Swagger/Javadoc/docstring evidence, how docs are generated or served.

Save to `.openclaw/app-dev-discovery/08-dependencies-integrations-evidence.md` and `.openclaw/app-dev-discovery/09-api-evidence.md`.

### Phase 9 — Testing Analysis

Identify: unit/integration/E2E tests, test frameworks, fixtures/mocks, test commands, CI test execution, coverage tooling, obvious test gaps.

Save to `.openclaw/app-dev-discovery/10-testing-evidence.md`.

### Phase 10 — Error Handling, Logging, and Observability

Identify: global exception handling, custom error classes, middleware/filters/interceptors, logging library, log format, monitoring/telemetry, Sentry/Datadog/OpenTelemetry, retry patterns, alerting hooks.

Save to `.openclaw/app-dev-discovery/11-error-logging-evidence.md`.

### Phase 11 — Security Analysis

Identify: authentication, authorization, input validation, secrets handling, security middleware, CSRF/CORS/CSP behavior, dependency risk indicators, password/token handling, env var usage, common attack protections.

**Do not perform destructive security testing.** Save to `.openclaw/app-dev-discovery/12-security-evidence.md`.

### Phase 12 — Build, Deployment, and Operations

Inspect: Dockerfile, docker-compose, Kubernetes manifests, Terraform, Pulumi, CDK, GitHub Actions, GitLab CI, deployment scripts, env templates, release scripts, process managers, runtime ports, health checks.

Document: build flow, deployment flow, operational dependencies, runtime assumptions, env vars, production hints, local development hints.

Save to `.openclaw/app-dev-discovery/13-build-deploy-evidence.md`.

### Phase 13 — Repository Hygiene and Architecture Risk Discovery

Search for: TODO, FIXME, HACK, XXX, TECHDEBT, DEPRECATED, `@deprecated`.

Summarize: counts, locations, recurring themes, likely impact.

Classify each finding as: Confirmed Risk, Probable Risk, Observation.

Categories: Security, Testing, Performance, Reliability, Scalability, Maintainability, Operational Readiness, Documentation.

Each finding must include: description, evidence, GitHub source URL, impact, confidence.

Save to `.openclaw/app-dev-discovery/14-risk-hygiene-evidence.md`.

### Phase 14 — Contradiction Detection

Compare evidence across: documentation, source code, config, CI/CD, Docker/deployment, infrastructure, tests.

Look for contradictions: README says PostgreSQL but code uses MySQL, CI says Node 22 but Dockerfile says Node 20, docs say JWT but code uses sessions, setup docs list missing commands, deployment files reference missing services, API docs differ from implemented routes.

For each contradiction include: summary, evidence A, evidence B, likely interpretation, impact, recommended follow-up.

Save to `.openclaw/app-dev-discovery/15-contradiction-detection.md`.

### Phase 15 — Generate ADR Files

Create `docs/adr/` if missing.

Create `docs/adr/000-template.md` with this structure:

```markdown
# ADR-000: Architecture Decision Record Template

## Status

Proposed | Accepted | Superseded | Deprecated

## Context

What is the situation or problem?

## Decision

What decision was made?

## Consequences

What tradeoffs, risks, and follow-up actions result from this decision?

## Evidence

Links to code, docs, issues, or external references.
```

Create `docs/adr/001-current-architecture-baseline.md` with this structure:

```markdown
# ADR-001: Current Architecture Baseline

## Status

Accepted

## Context

Summarize the current detected architecture.

## Decision

Document the current architecture as the baseline for future decisions.

## Architecture Style

Detected architecture style.

## Major Technologies

Detected major technologies.

## Key Tradeoffs

Observed tradeoffs.

## Known Constraints

Known constraints from repo evidence.

## Known Unknowns

Items requiring human confirmation.

## Evidence

Commit-pinned GitHub links supporting the baseline.
```

### Phase 16 — Final Onboarding Document Generation

Create `docs/<yyyy-mm-dd>-<repo-name>-app-dev-discovery.md` with this structure:

1. README / Instruction Files Summary
2. Detailed Technology Stack
3. System Overview and Purpose
4. Project Structure and Reading Recommendations
5. Key Components
6. Execution and Data Flows
7. Database Schema Overview
8. Dependencies and Integrations
9. API Documentation
10. Architecture Diagrams (Mermaid: component, data flow, class if applicable, deployment if detectable)
11. Testing
12. Error Handling and Logging
13. Security Considerations
14. Architecture Risks and Observations
15. Developer Productivity Guide (first-week reading order, fastest local startup, debugging entry points, common extension points)
16. Build / Deploy / Infrastructure
17. ADR Baseline
18. Discovery Confidence and Unknowns

Requirements:

- Clear Markdown, commit-pinned GitHub links, short representative snippets.
- Mermaid diagrams: component, data flow, class (if applicable), deployment (if detectable).
- Evidence Quality / Unknowns note where uncertain.
- Discovery confidence scoring table (Architecture, Business, Security, Deployment, Testing — each 0-100).
- Overall Discovery Confidence: High | Medium | Low.

### Phase 17 — Final Validation Gate

Validate before finalizing:

1. Every required final document section exists.
2. Every major claim has repository evidence.
3. All GitHub links are commit-pinned.
4. All linked paths exist.
5. No unsupported technology is listed.
6. Mermaid diagrams are syntactically plausible.
7. Snippets are short and relevant.
8. Final filename follows the required format.
9. ADR files exist.
10. Security, testing, deployment, architecture, and data sections are complete.
11. Contradictions are documented or explicitly stated as not found.
12. Confidence scoring exists.
13. One final onboarding document rolls up all required sections.
14. Temporary evidence files exist for recoverability.

Write results to `.openclaw/app-dev-discovery/16-final-validation.md`. If validation fails, fix and rerun. Do not commit until it passes.

### Phase 18 — Commit Workflow

After validation passes:

1. Create branch: `git checkout -b docs/app-dev-discovery-<yyyy-mm-dd>`
2. Add generated docs: `git add docs/`
3. Commit: `git commit -m "docs: generate developer discovery guide"`
4. Push the branch (runner does this; agent just reports).

Branch collision: use `docs/app-dev-discovery-<yyyy-mm-dd>-<short-commit>`. If commits blocked by policy, do not force — document the exact commands that would have been run and the reason.

## Completion Response

When finished, respond with:

- final onboarding document path
- ADR file paths
- validation status
- branch name
- commit hash if committed
- top 5 onboarding files to read first
- major unknowns or limitations
