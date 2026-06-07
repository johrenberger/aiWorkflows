# Component Test Analysis Workflow

## Objective

Produce a structured, risk-based, machine-readable analysis of a GitHub repository's component-level testing strategy. The workflow is **read-only**: it does not write tests, modify the target repo, or run the target repo's build. Its output is consumed by downstream test-generation workflows.

The analysis answers ten questions:

1. What does this repo do and what is it built with?
2. What are its components, and what are their boundaries?
3. What dependencies exist and what is their failure risk?
4. What does "component-level testing" mean *for this repo specifically*?
5. What dataset integrity issues exist?
6. What state transitions must be tested?
7. What behaviors are uncovered?
8. What tests exist today, and what gaps remain?
9. What is the prioritized gap backlog?
10. What is the rollout plan to close the gaps?

The workflow runs the **applicable subset** of 28 analysis sections per the `ANALYSIS_PROFILE` input. See `README.md` for the LITE/STANDARD/FULL tier summary, and `_docs/profile-tiers.md` for the per-section mapping.

## Inputs

```text
INPUT_GITHUB_REPO=<github-url>
INPUT_BRANCH=<optional branch, default: repo default>
ANALYSIS_PROFILE=lite|standard|full   # default: standard
ALLOW_PRODUCTION_FIXES=false           # this workflow NEVER touches source, but flag is honored
ALLOW_COMMIT=false                     # this workflow NEVER commits to the target repo
ALLOW_DEPENDENCY_INSTALL=false         # this workflow may need analysis tools (jq, python3, etc.)
ALLOW_CI_CHANGES=true                  # not applicable for this workflow
ALLOW_TEST_CONFIG_CHANGES=true         # not applicable for this workflow
MAX_REPAIR_ATTEMPTS_PER_FAILURE_CLASS=2
EMIT_EMPTY_JSONS=false                 # default: false. Set to true only for testing.
OUTPUT_DIR=<optional, default: ./artifacts/component-analysis-<date>/
```

### Defaults

- `ANALYSIS_PROFILE=standard` is the default. Pick `lite` for triage, `full` for a complete audit.
- `EMIT_EMPTY_JSONS=false` means the workflow does not produce JSON files for sections where the source data was not found. Downstream consumers must check `ls $OUTPUT_DIR/*.json` rather than assume a fixed set.
- `ALLOW_PRODUCTION_FIXES=false` and `ALLOW_COMMIT=false` are honored even though this workflow is read-only by design. The flags exist so this workflow can be safely composed into a larger pipeline that might toggle them for downstream phases.

## Phases

The workflow has 9 phases. Phases 1-4 are profile-agnostic. Phases 5-8 are gated by `ANALYSIS_PROFILE`. Phase 9 is always run.

```
Phase 0.5  Environment pre-flight (always)
Phase 1    Input validation (always)
Phase 2    Repository acquisition (always, read-only)
Phase 3    Stack and architecture detection (always)
Phase 4    Component boundary detection (always)
Phase 5    [LITE+] Dependency risk + dataset integrity + state transitions + behavioral coverage
Phase 6    [STANDARD+] Contract coverage + test fidelity + decision tree
Phase 7    [STANDARD+] Risk priority ranking + quality gates
Phase 8    [FULL] Security + architecture validation + Java/JS playbooks + mutation roadmap
Phase 9    Output assembly + handoff manifest (always)
```

### Phase 0.5 — Environment pre-flight

Verifies:
- `git` on PATH.
- `python3` on PATH (for JSON emission and pattern analysis).
- `gh` NOT required (this workflow does not call GitHub; it works on a local clone).
- `jq` on PATH (for JSON validation).
- Disk free for `OUTPUT_DIR` (≥ 1 GB recommended; most artifacts are < 100 MB but JaCoCo/Pytest raw reports can be large).
- GitHub auth NOT required.

The pre-flight fails fast with `CTA-BLK-PreFlight` if any required tool is missing. The `application-test-coverage` pre-flight (TC-VAL-17/18/19/20) is **not** required here — that workflow's gates validate test-execution tooling, which this workflow doesn't use.

### Phase 1 — Input validation

- Validate `INPUT_GITHUB_REPO` is a well-formed GitHub URL.
- Resolve `INPUT_BRANCH` to a concrete branch (or use repo default).
- Validate `ANALYSIS_PROFILE ∈ {lite, standard, full}`.
- Reject combinations of `ALLOW_PRODUCTION_FIXES=true` with `ANALYSIS_PROFILE=full` if the user really wants source modifications, since `full` includes architecture-validation recommendations that suggest source refactors — log a warning, not a block.

### Phase 2 — Repository acquisition

- Clone (or update) the repository to `$OUTPUT_DIR/_repo/`.
- Use `--depth 1` for shallow clones; this is sufficient for analysis.
- Record the commit SHA, branch, and timestamp in the ledger.

This is the only phase that touches the network for code. No further network calls.

### Phase 3 — Stack and architecture detection

- Detect language(s), framework(s), build system(s), package manager(s), CI/CD pipeline(s).
- Detect source layout, test layout, infrastructure code, database technologies, messaging technologies, external integrations, public/internal APIs, shared libraries, configuration systems.
- Produce `Repository Overview` and `Technology Inventory` sections of the ledger.

**Section coverage:** Original prompt section 1.

### Phase 4 — Component boundary detection

- Walk the source tree and identify logical components (preferring domain/module boundaries over individual classes).
- For each component, capture: name, responsibility, public interface, dependencies, dependency type, risk tier, test boundary.
- Produce `Component Inventory Table`.

**Section coverage:** Original prompt section 2.

### Phase 5 — Risk + behavior + gap (LITE+)

| Sub-phase | Source sections | Description |
|---|---|---|
| 5a | 3 (partial — internal deps only) | Dependency classification. Skip external HTTP/messaging deps in LITE; full inventory in STANDARD+. |
| 5b | 5 | Dataset integrity analysis. Detect seed data, CSV/SQL scripts, fixtures, data loaders, referential integrity, orphan/duplicate/missing-reference detection. |
| 5c | 6 (per component) | State transition analysis. Build state models for each component. |
| 5d | 7 | Behavioral coverage model. For each behavior: happy path, negative path, validation, error path, boundaries, dependency failures, state transitions, security scenarios. Produce `Behavior Coverage Matrix`. |
| 5e | 8 | Current test analysis. Map existing tests to components. Produce `Current Coverage Matrix`. |
| 5f | 9 | Test gap analysis. For each component, identify missing behaviors, interfaces, error paths, data conditions, state transitions, security checks, dependency failures, configuration scenarios. Classify each gap. Produce `Prioritized Gap Backlog`. |
| 5g | 13 | Coverage strategy. Functional / behavioral / state / dependency / security / configuration / data / contract / accessibility coverage, with risk-based expectations. |

**JSONs emitted in LITE:** `component-inventory.json`, `behavior-coverage.json`, `gap-backlog.json`.

### Phase 6 — Contracts + fidelity + decision tree (STANDARD+)

| Sub-phase | Source sections | Description |
|---|---|---|
| 6a | 3 (full) | Complete dependency risk matrix. |
| 6b | 11 | Contract coverage analysis. For each public API: request/response/error contract, contract tests, backward-compat rules, schema validation. Produce `Contract Inventory`. |
| 6c | 14 | Test fidelity strategy. Real > Fake > Stub > Mock. For each dependency, recommend concrete approach (Real/Fake/Stub/Mock/WireMock/Testcontainers) with rationale. |
| 6d | 15 | Test architecture decision tree. Deterministic selection rules: "Uses DB? → DataJpaTest", "Uses REST? → MockMvc", etc. |
| 6e | 19, 20 | Flaky test prevention + test data governance. |
| 6f | 23, 24 | Machine-readable output schemas. (Emission in Phase 9.) |

**JSONs emitted in STANDARD:** `dependency-risk-matrix.json`, `state-transition-matrix.json`, `contract-inventory.json`, `risk-priority-ranking.json` (after Phase 7).

### Phase 7 — Risk ranking + gates + rollout (STANDARD+)

| Sub-phase | Source sections | Description |
|---|---|---|
| 7a | 21 | Change-risk prioritization. Compute risk from business criticality + change frequency + dependency count + complexity + public exposure + existing coverage. Produce `Risk Priority Ranking`. |
| 7b | 27 | Quality gates. For PR / branch / nightly / RC / regression: behavioral coverage, contract verification, mutation results, flaky test thresholds, architecture validation. |
| 7c | 26 | Implementation rollout plan. 6 phases: data integrity → highest risk component → remaining domain → architecture validation → mutation → continuous improvement. |
| 7d | 28 | Test pyramid alignment. Unit / component / contract / integration / E2E distribution with rationale. |
| 7e | 22 | Production feedback loop. Incident → root cause → missing scenario → backlog → test creation. |

**JSONs emitted in STANDARD:** `risk-priority-ranking.json`. (Other Phase 6 JSONs also emitted here.)

### Phase 8 — Security + architecture + playbooks (FULL only)

| Sub-phase | Source sections | Description |
|---|---|---|
| 8a | 10 | Security-relevant component testing. Input validation, injection protection, business logic abuse, authorization, resource ownership, error handling, info disclosure. OWASP ASVS mapping. Produce `Security Coverage Matrix`. |
| 8b | 12 | Architecture validation. Layer violations, dependency violations, cyclic dependencies, package violations, unauthorized access paths. ArchUnit (Java) / Dependency Cruiser (JS) rule recommendations. |
| 8c | 4 | Component testing definition (specifically for this repo). Goals, ownership, success criteria, expected outcomes. |
| 8d | 16 | Java implementation playbook. JUnit 5, Mockito, AssertJ, Spring Boot Test, MockMvc, REST Assured, Testcontainers, WireMock, Pact, JaCoCo, PIT, Maven, Gradle. Folder structure, naming, tags, profiles, data management, CI integration. |
| 8e | 17 | JavaScript implementation playbook. Jest, Vitest, Testing Library, Playwright Component Testing, MSW, Pact, Istanbul. Folder structure, naming, data management, CI integration. |
| 8f | 18 | Mutation testing strategy. PIT usage, mutation targets, exclusions, mutation quality gates. Produce `Mutation Testing Roadmap`. |
| 8g | 25 | Test gap backlog format. ID, component, risk, priority, behavior, trigger, expected result, test type, framework, source file, target test file, acceptance criteria, owner. |

**JSONs emitted in FULL:** `mutation-roadmap.json`, plus `test-creation-input-schema.json` (the section 24 schema for downstream AI test-gen).

### Phase 9 — Output assembly + handoff manifest

- Assemble `TODO_component-analysis.md` from all populated sections.
- Emit the JSON files for sections that produced data.
- Produce a `handoff-manifest.json` listing all artifacts produced, with one-line descriptions and pointers to the matching consumer workflow.
- If `EMIT_EMPTY_JSONS=true` (testing only), emit stubs for the missing sections with `{"_skipped": "..."}` payload.

## Multi-module repositories

This workflow inherits the multi-module handling from `application-test-coverage`. Specifically:

- For Maven `<modules>`, Gradle `include(...)`, npm/pnpm/yarn workspaces, Cargo workspace: treat each module as a separate component.
- For Spring Boot / Django / Express: treat each top-level package/route group as a component.
- Components are detected per-module, then rolled up. The rollup is the top-level `Component Inventory`; per-module detail is appendix.

## Profile gating summary

| Phase | LITE | STANDARD | FULL |
|---|:---:|:---:|:---:|
| 0.5 pre-flight | ✅ | ✅ | ✅ |
| 1 input validation | ✅ | ✅ | ✅ |
| 2 repo acquisition | ✅ | ✅ | ✅ |
| 3 stack detection | ✅ | ✅ | ✅ |
| 4 component detection | ✅ | ✅ | ✅ |
| 5 risk + behavior + gap | ✅ (5b, 5c, 5d, 5e, 5f, 5g) | ✅ | ✅ |
| 6 contracts + fidelity | — | ✅ | ✅ |
| 7 risk ranking + gates | — | ✅ | ✅ |
| 8 security + arch + playbooks | — | — | ✅ |
| 9 output assembly | ✅ | ✅ | ✅ |

## Strict rules

- **Read-only on the target repo.** No file modifications, no test execution, no commits.
- **Network is only used in Phase 2** (clone). No subsequent API calls.
- **No invented data.** Every claim in the ledger must reference a file, command, or observed artifact.
- **No invented components.** If a component's boundary is unclear, mark it `UNCLEAR` in the inventory and explain the ambiguity.
- **No re-running expensive commands.** The `RECOVERY` model resumes from the ledger; do not re-clone or re-scan unless required for correctness.
- **Every gap must be classifiable.** Severity, risk, complexity, effort, owner, priority are required fields. If a field cannot be determined, use `TBD` with rationale.

## Handoff contracts

See `_docs/handoffs.md` for the explicit handoff paths to:

- `application-test-coverage` — consumes `gap-backlog.json` + `component-inventory.json`
- `application-mutation-testing` — consumes `mutation-roadmap.json` (FULL only)
- AI test-generation systems — consumes `test-creation-input-schema.json` (FULL only) + `gap-backlog.json`

## Recovery

See `recovery.md`. Standard ledger-based resume pattern.

## Validation

See `validation.md`. Profile-aware TC-VAL-* gate list.

## Outputs

See `output-template.md`. The Markdown ledger template + 8 JSON schema docs.
