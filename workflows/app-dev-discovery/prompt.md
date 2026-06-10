# OpenClaw Workflow Prompt: App Developer Discovery (Analyzer-Accelerated)

> This is the **analyzer-accelerated** version of the app-dev-discovery prompt.
> The deterministic evidence-gathering phases (1, 3, 4, 7, 8, 9, 10, 11, 13,
> 14, 15) are pre-computed by the `repo-discovery-analyzer` workflow and
> written to the evidence directory by `synthesize-evidence.sh` BEFORE the
> agent runs. The agent's job is narrowed to:
>
> 1. **Read** the pre-computed evidence files (00–15).
> 2. **Fill in the LLM-only sections** (narrative in 02, 05, 06, 14, 15; the
>    confidence scoring in 16).
> 3. **Synthesize the final onboarding document** (Phase 16) by rolling up
>    the evidence into a 18-section deliverable with Mermaid diagrams.
> 4. **Validate** (Phase 17) and report.

This is a major change from the previous prompt where the agent had to do
all 18 phases from scratch. The new design trades a small amount of
flexibility for ~10x speed, deterministic accuracy on facts (URLs, paths,
versions), and consistent evidence quality across runs.

---

## Runtime Inputs

The workflow accepts exactly one required runtime variable:

- `GITHUB_PROJECT_URL` — the GitHub repository to analyze.

Optional environment variables consumed by the runner script:

- `WORKSPACE_DIR` — working directory for the analysis. Default: the cloned repository.
- `KEEP_TEMP` — if `true`, the `.openclaw/app-dev-discovery/` evidence directory is preserved on success.
- `DRY_RUN` — if `true`, do not commit or push.

## Mission

You are an AI coding agent operating inside an existing source-code workspace.

Your task is to produce a reliable, evidence-backed technical onboarding document
for a developer who has just joined this project.

The bulk of the evidence is already on disk in `.openclaw/app-dev-discovery/`,
produced deterministically by the `repo-discovery-analyzer` workflow. **Do not
re-discover facts that are already in the evidence files** — your job is to
synthesize, narrate, and validate.

The final document must explain:

- architecture, features, main flows, key components, technology stack
- database/schema, APIs, integrations
- testing, error handling, logging, security
- build/deploy/infrastructure, architecture risks
- developer productivity guidance
- discovery confidence

## Operating Principles

Optimize for: **reliability, recoverability, bounded context, validation,
observability, synthesis quality, platform fit, evidence discipline**.

Rules:

1. **Read the evidence files first** — `.openclaw/app-dev-discovery/00-*.md`
   through `15-*.md` are already on disk. Treat them as ground truth.
2. Do not rely only on README files. Use the evidence + source code.
3. Prefer source code, config, schemas, tests, and deployment files as
   additional evidence when the analyzer's evidence is sparse.
4. Mark uncertain conclusions explicitly.
5. Never invent technologies, flows, APIs, diagrams, or dependencies.
6. Use concise representative snippets only.
7. Keep diagrams high-level.
8. **All GitHub links must be commit-pinned.** The analyzer produces
   commit-pinned URLs in the evidence files; preserve the format.
   **Concrete rule for the final onboarding document:**
   - Every backticked filename (`\`Foo.java\``, `\`pom.xml\``, etc.) and
     every plain-text reference to a repo path that the agent cites in
     the final document MUST be a markdown link of the form
     `[name](https://github.com/<owner>/<repo>/blob/<sha>/<path>)`.
   - The pin prefix is `https://github.com/<owner>/<repo>/blob/$(git rev-parse HEAD)/`.
     Read `CURRENT_COMMIT` from `00-run-metadata.md` and use it consistently.
   - This applies to: §4 (reading order, bootstrap table), §5 (component
     inventory), §6 (flow steps), §7 (schema tables), §10 (mermaid block
     participants), §11 (testing tables), §14 (risk table), §15 (first-week
     reading order, debugging entry points, extension points).
   - **Do not leave bare filenames in §4, §10, §11, §15.** The Phase 17
     validation gate fails on this check; the prompt alone will not
     produce it.
9. Generate one final onboarding document that rolls up the data from all
   evidence sections.
10. **The 16 evidence files are already on disk** — do not re-create them
    from scratch. Edit / extend them where the prompt asks for LLM
    judgment.
11. Do not generate the final document until validation passes.
12. The runner script handles branch creation, commit, and push.

## Execution Discipline (added by runner)

- **Use absolute paths** in every `read`, `write`, `edit`, and `exec` call.
- **Do not spawn sub-agents** for the analysis phases.
- **Do not run `openclaw agent`, `openclaw gateway restart`, or any other
  lifecycle command** from inside this workflow.
- **Do not modify or commit anything** — the runner script handles that.
- **Write short evidence, not essays.** Aim for evidence files of 2-10KB
  each. The final document is the rolled-up synthesis.

## Evidence Directory Layout

The runner has already executed `synthesize-evidence.sh` which produced:

```
.openclaw/app-dev-discovery/
  00-run-metadata.md             (deterministic — analyzer)
  01-file-inventory.md           (deterministic — analyzer)
  02-documentation-evidence.md   (SKELETON — agent fills in)
  03-stack-evidence.md           (deterministic — analyzer)
  04-structure-evidence.md       (deterministic — analyzer)
  05-components-evidence.md      (SKELETON — agent fills in)
  06-flows-evidence.md           (SKELETON — agent fills in)
  07-data-evidence.md            (deterministic — analyzer)
  08-dependencies-integrations-evidence.md (deterministic — analyzer)
  09-api-evidence.md             (deterministic — analyzer)
  10-testing-evidence.md         (deterministic — analyzer)
  11-error-logging-evidence.md   (deterministic — analyzer)
  12-security-evidence.md        (deterministic — analyzer)
  13-build-deploy-evidence.md    (deterministic — analyzer)
  14-risk-hygiene-evidence.md    (PARTIAL — analyzer lists findings; agent interprets)
  15-contradiction-detection.md  (PARTIAL — analyzer lists candidates; agent interprets)
```

Also on disk for the agent's reference (raw analyzer JSON outputs):

```
.openclaw/analyzer-output/
  analysis_manifest.json
  repo_inventory.json
  tech_stack.json
  project_structure.json
  entry_points.json
  routes.json
  db_schema.json
  dependencies.json
  integrations.json
  tests.json
  error_logging.json
  security_signals.json
  build_deploy.json
  hygiene_findings.json
  contradiction_candidates.json
  loc_metrics.json
  github_links.json
  validation_report.json
```

Final deliverables (in the target repository):

```
docs/<yyyy-mm-dd>-<repo-name>-app-dev-discovery.md
docs/adr/000-template.md
docs/adr/001-current-architecture-baseline.md
```

## Phases

### Phase 0 — Repository Acquisition and Metadata

**Already done by `run.sh`.** No action required from the agent. Read
`.openclaw/app-dev-discovery/00-run-metadata.md` for context.

### Phase 1 — Full Repository Inventory

**Already done by analyzer.** Read `.openclaw/app-dev-discovery/01-file-inventory.md`.
The analyzer's inventory uses the same `path | type | role | reviewed |
excluded | reason` schema as the previous agent-driven version. No
additional action required.

If the agent discovers significant inventory drift (e.g. a build artifact
that should have been excluded but wasn't), it may amend the file with a
note, but should not delete existing rows.

### Phase 2 — Documentation and Instruction Review

**LLM-only — agent fills in `.openclaw/app-dev-discovery/02-documentation-evidence.md`.**

Read README.md, CONTRIBUTING.md, docs/, architecture notes, setup guides,
runbooks, changelogs, and important script comments. Summarize: project
overview, setup/run instructions, conventions, contribution process,
documentation gaps.

### Phase 3 — Technology Stack Detection

**Already done by analyzer.** Read `.openclaw/app-dev-discovery/03-stack-evidence.md`.
The file contains a complete commit-pinned table. The agent may add a
1-2 sentence "Architecture Style" paragraph at the bottom.

### Phase 4 — Project Structure and Entry Point Mapping

**Already done by analyzer.** Read `.openclaw/app-dev-discovery/04-structure-evidence.md`.
The file contains top-level layout, notable directories, detected entry
points, recommended reading order, and bootstrap/config files.

### Phase 5 — Key Component Analysis

**LLM-only — agent fills in `.openclaw/app-dev-discovery/05-components-evidence.md`.**

The file already contains a "Component Inventory (deterministic)" table
from the analyzer. The agent's job is to write 1-3 short paragraphs per
important component describing: name, responsibility, dependencies,
downstream consumers, and why it matters.

Prioritize components that affect: app startup, request handling, domain
logic, persistence, authn/authz, integrations, background processing,
deployment/runtime.

### Phase 6 — Execution and Data Flow Analysis

**LLM-only — agent fills in `.openclaw/app-dev-discovery/06-flows-evidence.md`.**

The file already contains a "Detected Triggers (deterministic)" table.
The agent's job is to trace critical flows end-to-end and write 1-3
sentences per flow: trigger, entry point, major steps, data read/write
behavior, error handling, persistence target, external services.

### Phase 7 — Database and Schema Analysis

**Already done by analyzer.** Read `.openclaw/app-dev-discovery/07-data-evidence.md`.
The file contains the entities table + per-entity details.

If the analyzer's file says "No clear persistence layer was found", the
agent may attempt a manual review of SQL files / ORM config and amend
the file. Do not invent entities.

### Phase 8 — Dependencies, Integrations, and APIs

**Already done by analyzer.** Read `.openclaw/app-dev-discovery/08-dependencies-integrations-evidence.md`
(major libraries + integrations) and `09-api-evidence.md` (API surface).
The agent may add an "Auth Providers / APIs" section to 08- if it
discovers auth patterns in source code.

### Phase 9 — Testing Analysis

**Already done by analyzer.** Read `.openclaw/app-dev-discovery/10-testing-evidence.md`.
The file contains the test/source ratio and detected frameworks/commands.
The agent may add "Test Gaps / Observations" notes.

### Phase 10 — Error Handling, Logging, and Observability

**Already done by analyzer.** Read `.openclaw/app-dev-discovery/11-error-logging-evidence.md`.
The agent may add pattern-level analysis (global exception handlers,
retry, alerting) by reading source code.

### Phase 11 — Security Analysis

**Already done by analyzer (partial).** Read `.openclaw/app-dev-discovery/12-security-evidence.md`.
The agent must extend this with auth/authorization analysis, secrets
handling, CSRF/CORS/CSP behavior. **Do not perform destructive security
testing.**

### Phase 12 — Build, Deployment, and Operations

**Already done by analyzer.** Read `.openclaw/app-dev-discovery/13-build-deploy-evidence.md`.
The agent must add: build flow narrative, deployment flow narrative,
env var table, and local development notes.

### Phase 13 — Repository Hygiene and Architecture Risk

**PARTIAL — analyzer lists findings; agent interprets.**

Read `.openclaw/app-dev-discovery/14-risk-hygiene-evidence.md`. The
analyzer has already produced a table of findings. The agent must:

1. Run grep for TODO, FIXME, HACK, XXX, TECHDEBT, DEPRECATED, @deprecated.
2. Count occurrences, list top recurring themes, likely impact.
3. Classify each finding as: Confirmed Risk, Probable Risk, Observation.
4. Categories: Security, Testing, Performance, Reliability, Scalability,
   Maintainability, Operational Readiness, Documentation.

### Phase 14 — Contradiction Detection

**PARTIAL — analyzer lists candidates; agent interprets.**

Read `.openclaw/app-dev-discovery/15-contradiction-detection.md`. The
analyzer has listed contradiction candidates. The agent must:

1. For each candidate, add: likely interpretation, recommended follow-up.
2. Cross-check manually between: documentation, source code, config,
   CI/CD, Docker, infrastructure, tests.
3. Look for: README vs code, Dockerfile vs CI, docs vs implemented
   routes, declared vs exposed ports.

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

**Source from the 16 evidence files** — they already have the relevant
tables and lists with commit-pinned URLs. The agent's job is to compose
the prose that connects them.

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
3. All GitHub links are commit-pinned. **Validation gate: at least one
   `https://github.com/<owner>/<repo>/blob/<sha>/...` URL must appear in
   the final document. The 2026-06-10 BroadleafCommerce run failed here
   (0 URLs in the agent-authored final doc, 7 in the prior 2026-06-06
   doc). See `openclaw-kb/known-errors/agent-dropped-commit-pinned-urls.md`.**
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
14. **All 16 analyzer evidence files are on disk** (the runner's
    `validate.sh` will check for these too).

Write results to `.openclaw/app-dev-discovery/16-final-validation.md`. If
validation fails, fix and rerun. Do not commit until it passes.

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

## Performance & Quality Notes

This is the analyzer-accelerated variant. Compared to the previous
all-LLM version, the tradeoffs are:

| Aspect | Old (LLM) | New (Analyzer + LLM) |
| --- | --- | --- |
| Evidence accuracy | LLM-dependent | Deterministic (commit-pinned URLs verified) |
| Speed | ~10-20 min/run | ~2-3 min/run |
| Cost | High (every fact extracted by LLM) | Low (analyzer pre-computes 80%) |
| Reproducibility | Variable (LLM drift) | High (deterministic backbone) |
| Flexibility | LLM can interpret intent | LLM focuses on judgment calls only |
| Coverage of rare stack patterns | Better (LLM can read anything) | Limited to analyzer's known patterns |

**When to fall back to the old approach:** If the analyzer produces
sparse or zero evidence for a non-standard stack (e.g. a custom DSL,
rare language, hand-rolled build system), the agent can fall back to
manual source review for the affected sections. Document this in the
"Unknowns" section of the final doc.
