# TODO Component Analysis

## Context

- [ ] **CTA-CTX-1 [Repository]**
  - Repository URL:
  - Branch:
  - Commit:
  - Timestamp:
  - Profile: `lite` | `standard` | `full`
  - Output Directory:

## Checkpoints

- [ ] CTA-CKPT-1 INPUT_VALIDATED
- [ ] CTA-CKPT-2 REPO_ACQUIRED
- [ ] CTA-CKPT-3 STACK_DETECTED
- [ ] CTA-CKPT-4 COMPONENTS_DETECTED
- [ ] CTA-CKPT-5 RISK_BEHAVIOR_GAP_DONE   (LITE+)
- [ ] CTA-CKPT-6 CONTRACTS_FIDELITY_DONE  (STANDARD+)
- [ ] CTA-CKPT-7 RANKING_GATES_ROLLOUT    (STANDARD+)
- [ ] CTA-CKPT-8 SECURITY_ARCH_PLAYBOOKS  (FULL)
- [ ] CTA-CKPT-9 OUTPUTS_ASSEMBLED

## Section 1 — Repository Analysis

### Repository Overview

```
Name:
Description (from README or repo metadata):
Primary language(s):
Test framework(s) detected:
Build system:
Package manager:
CI/CD pipeline(s):
Source layout:
Test layout:
```

### Technology Inventory

| Category | Tool / Library | Version | Purpose |
|---|---|---|---|
| Language | | | |
| Framework | | | |
| Build | | | |
| Package manager | | | |
| Test framework | | | |
| Coverage tool | | | |
| CI/CD | | | |
| Database | | | |
| Messaging | | | |
| Cache | | | |

### Dependency Inventory

(List top-level dependencies from manifest files: `pom.xml`, `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, etc.)

| Dependency | Type | Version | Source | Purpose |
|---|---|---|---|---|
| | Internal/Database/HTTP/... | | pom.xml / package.json / ... | |

### Architecture Summary

(2-3 paragraphs: layered? hexagonal? microservices? monolith? event-driven?)

### Assumptions

(State any assumption that could not be verified from the source tree.)

## Section 2 — Component Inventory

| Component | Responsibility | Public Interface | Dependencies | Dep Type | Risk Tier | Test Boundary |
|---|---|---|---|---|---|---|
| | | | | | T1-T4 | unit/component/contract/integration/E2E |

### Component Detail (per component, in STANDARD+ profile)

#### Component: <Name>

**Responsibility:** ...

**Public Interface:**
```
<signatures, not implementations>
```

**Dependencies (in):** ...

**Dependencies (out):** ...

**Risk Tier:** T1 | T2 | T3 | T4

**Test Boundary:** unit | component | contract | integration | E2E

**State:** CLEAR | UNCLEAR (with rationale)

## Section 3 — Dependency Risk Matrix  (LITE: internal only / STANDARD+: full)

| Dependency | Component Owner | Failure Impact (1-5) | Likelihood (1-5) | Risk Score | Test Strategy |
|---|---|:---:|:---:|:---:|---|
| | | | | 1-25 | Real / Fake / Stub / Mock / WireMock / Testcontainers |

## Section 4 — Component Testing Definition

(For THIS repo specifically.)

**Compared against:**
- Unit Testing: ...
- Component Testing: ...
- Contract Testing: ...
- Integration Testing: ...
- System Testing: ...
- End-to-End Testing: ...

**Goals:** ...
**Ownership:** ...
**Success Criteria:** ...
**Expected Outcomes:** ...

## Section 5 — Dataset Integrity Analysis

### Datasets Detected

| Path | Type | Size | Risk |
|---|---|---|---|
| | seed/CSV/SQL/fixture/loader/init | | T1-T4 |

### Integrity Issues

| Issue | Type | Affected Dataset | Severity |
|---|---|---|---|
| | orphan/duplicate/missing-ref/... | | blocker/major/minor |

## Section 6 — State Transition Matrix

### Component: <Name>

```
START
 ↓
Valid Request
 ↓
Entity Found
 ↓
Return Response
```

OR

```
START
 ↓
Valid Request
 ↓
Entity Missing
 ↓
Exception
 ↓
Error Response
```

| State | Trigger | Next State | Coverage Requirement |
|---|---|---|---|

## Section 7 — Behavioral Coverage Matrix

| Component | Behavior | Happy | Negative | Validation | Error | Boundary | Dep Failure | State | Security | Score |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| | | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | 0-8 |

**Behavioral Coverage Score:** (covered behaviors / total behaviors × 100%)

## Section 8 — Current Test Analysis

| Test File | Component Tested | Test Type | Tests | Last Modified | Coverage % |
|---|---|---|---|---|---|

## Section 9 — Test Gap Analysis (Prioritized Backlog)

| ID | Component | Behavior | Severity | Risk | Complexity | Effort | Owner | Priority | Trigger | Expected Result | Test Type | Framework | Source File | Target Test File | Acceptance Criteria |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CTA-GAP-001 | | | blocker/major/minor/nit | T1-T4 | trivial/simple/moderate/complex | < 1h / 1-4h / 0.5-2d / 1w / 2w+ | | P0-P3 | | | | | | | |

(Top 10 by risk in the body; full list in `gap-backlog.json`.)

## Section 10 — Security Coverage Matrix  (FULL)

| Component | Input Validation | Injection | Auth Logic | Authz | Resource Ownership | Error Handling | Info Disclosure | OWASP ASVS |
|---|---|---|---|---|---|---|---|---|
| | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | V#.#.# |

## Section 11 — Contract Inventory  (STANDARD+)

| API | Method | Path | Request Schema | Response Schema | Error Schema | Backward Compat | Schema Validation |
|---|---|---|---|---|---|---|---|

## Section 12 — Architecture Validation Backlog  (FULL)

| Violation | Type | Affected Files | ArchUnit / DC Rule |
|---|---|---|---|

## Section 13 — Coverage Strategy

| Coverage Type | Definition | Risk-Based Expectation | Threshold |
|---|---|---|---|
| Functional | | | |
| Behavioral | | | |
| State | | | |
| Dependency | | | |
| Security | | | |
| Configuration | | | |
| Data | | | |
| Contract | | | |
| Accessibility (if UI) | | | |

## Section 14 — Test Fidelity Matrix  (STANDARD+)

| Component | Dependency | Recommended | Why |
|---|---|---|---|
| | | Real/Fake/Stub/Mock/WireMock/Testcontainers | |

## Section 15 — Test Selection Decision Tree  (STANDARD+)

```
Uses DB?
 → DataJpaTest (Spring) / pytest-django (Python) / *_test.go with testcontainers (Go)

Uses REST controller?
 → MockMvc (Spring) / TestClient (FastAPI) / supertest (Node)

Uses external HTTP?
 → WireMock / msw (Node) / httptest (Go)

Needs production DB semantics?
 → Testcontainers

Needs real message queue?
 → Testcontainers (Kafka, RabbitMQ)

Needs real cache?
 → Testcontainers (Redis)

Needs deterministic time?
 → Clock abstraction / TimeMachine (Java) / freezegun (Python)
```

## Section 16 — Java Implementation Playbook  (FULL)

(Folder structure, naming, tags, profiles, data management, CI integration for JUnit 5, Mockito, AssertJ, Spring Boot Test, MockMvc, REST Assured, Testcontainers, WireMock, Pact, JaCoCo, PIT, Maven, Gradle.)

## Section 17 — JavaScript Implementation Playbook  (FULL)

(Folder structure, naming, data management, CI integration for Jest, Vitest, Testing Library, Playwright Component Testing, MSW, Pact, Istanbul.)

## Section 18 — Mutation Testing Strategy  (FULL)

| PIT Configuration | Value |
|---|---|
| Mutation targets | |
| Exclusions | |
| Mutation score threshold | |
| Quality gate | |

## Section 19 — Flaky Test Prevention Checklist  (STANDARD+)

- [ ] No `Thread.sleep`
- [ ] No execution-order dependency
- [ ] No shared mutable state
- [ ] No external network access (in unit/component tests)
- [ ] Deterministic clocks (use `Clock` abstraction, not `new Date()`)
- [ ] Deterministic randomness (use seeded `Random`)
- [ ] No filesystem writes to absolute paths
- [ ] No timing-based assertions (`assertTrue(start - end < 100ms)`)

## Section 20 — Test Data Governance  (STANDARD+)

| Data Class | Source | Lifecycle | Governance |
|---|---|---|---|
| Static | | | |
| Generated | | | |
| Reference | | | |
| Edge Case | | | |
| Security | | | |

## Section 21 — Risk Priority Ranking  (STANDARD+)

| Component | Business Crit | Change Freq | Dep Count | Complexity | Public Exposure | Existing Coverage | Risk Score | Priority |
|---|---|---|---|---|---|---|:---:|---|
| | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 (inverted) | 6-30 | P0-P3 |

## Section 22 — Production Feedback Loop

```
Incident
 ↓
Root Cause
 ↓
Missing Scenario
 ↓
Backlog (CTA-GAP-NNN)
 ↓
Test Creation
```

## Section 23 — Machine-Readable Outputs

(List the JSONs actually emitted. By default, sections with no source data are skipped — see `EMIT_EMPTY_JSONS` input.)

| File | Schema Version | Bytes | Section |
|---|---|---|---|
| | | | |

## Section 24 — Test Creation Workflow Input Schema  (FULL)

(Emitted as `test-creation-input-schema.json`. The schema describes the input contract for downstream AI test-generation systems.)

## Section 25 — Test Gap Backlog Format  (FULL)

(Schema is in `gap-backlog.json`. See field requirements in `prompt-implementation.md` Gap Classification section.)

## Section 26 — Implementation Rollout Plan

| Phase | Focus | Components / Datasets | Success Criteria |
|---|---|---|---|
| 1 | Data Integrity | | |
| 2 | Highest Risk Component (T1) | | |
| 3 | Remaining Domain Components (T2) | | |
| 4 | Architecture Validation | | |
| 5 | Mutation Testing | | |
| 6 | Continuous Improvement | | |

## Section 27 — Quality Gates  (STANDARD+)

| Gate | Threshold | Owner | Action on Failure |
|---|---|---|---|
| Pull Request | behavioral coverage ≥ X%, contracts pass | | block merge |
| Branch Build | + flaky test rate < Y% | | block merge |
| Nightly Build | + mutation score ≥ Z% | | warn |
| Release Candidate | + architecture validation pass | | block tag |
| Regression Suite | + all E2E pass | | block release |

## Section 28 — Test Pyramid Alignment  (STANDARD+)

| Layer | Recommended Distribution | Rationale |
|---|---|---|
| Unit | 60% | Fast feedback, low cost |
| Component | 20% | Boundary validation |
| Contract | 10% | API stability |
| Integration | 7% | Cross-module behavior |
| E2E | 3% | Critical user paths only |

## Handoff Manifest

(Emitted as `handoff-manifest.json`.)

```json
{
  "produced_at": "<ISO-8601>",
  "profile": "standard",
  "repo": "<url>",
  "branch": "<branch>",
  "commit": "<sha>",
  "artifacts": [
    {
      "file": "component-inventory.json",
      "description": "...",
      "consumer": "application-test-coverage",
      "consumer_input_mapping": "..."
    },
    {
      "file": "gap-backlog.json",
      "description": "...",
      "consumer": "application-test-coverage",
      "consumer_input_mapping": "MODULE_LIST or focused picks"
    }
  ]
}
```

---

# JSON Schema Docs

## `component-inventory.json`

```json
{
  "version": "1.0",
  "repo": "<url>",
  "commit": "<sha>",
  "profile": "lite|standard|full",
  "components": [
    {
      "id": "CTA-COMP-001",
      "name": "<ComponentName>",
      "responsibility": "<text>",
      "public_interface": ["<signature>", ...],
      "dependencies_in": [{"name": "<dep>", "type": "Internal|Database|..."}],
      "dependencies_out": [{"name": "<dep>", "type": "Internal|Database|..."}],
      "risk_tier": "T1|T2|T3|T4",
      "test_boundary": "unit|component|contract|integration|E2E",
      "state": "CLEAR|UNCLEAR",
      "rationale_if_unclear": "<text>"
    }
  ]
}
```

## `behavior-coverage.json`

```json
{
  "version": "1.0",
  "components": [
    {
      "component_id": "CTA-COMP-001",
      "behaviors": [
        {
          "id": "CTA-BEH-001",
          "name": "<behavior>",
          "paths_covered": ["happy", "negative", "validation", "error", "boundary", "dependency_failure", "state_transition", "security"],
          "score": 0-8
        }
      ],
      "total_score": 0,
      "max_score": 0,
      "coverage_percent": 0
    }
  ],
  "aggregate_coverage_percent": 0
}
```

## `gap-backlog.json`

```json
{
  "version": "1.0",
  "gaps": [
    {
      "id": "CTA-GAP-001",
      "component_id": "CTA-COMP-001",
      "behavior_id": "CTA-BEH-001|null",
      "description": "<text>",
      "severity": "blocker|major|minor|nit",
      "risk": "T1|T2|T3|T4",
      "complexity": "trivial|simple|moderate|complex",
      "effort": "<1h|1-4h|0.5-2d|1w|2w+",
      "owner": "<team>",
      "priority": "P0|P1|P2|P3",
      "trigger": "<input that exposes the gap>",
      "expected_result": "<correct behavior>",
      "test_type": "unit|component|contract|integration|E2E",
      "framework": "<junit5|pytest|jest|...>",
      "source_file": "<path>",
      "target_test_file": "<path>",
      "acceptance_criteria": "<text>"
    }
  ]
}
```

## `dependency-risk-matrix.json`

```json
{
  "version": "1.0",
  "dependencies": [
    {
      "id": "CTA-DEP-001",
      "name": "<dep>",
      "component_owner": "CTA-COMP-001",
      "type": "Internal|Database|HTTP|Messaging|FileSystem|Cache|Configuration|Startup|ThirdParty",
      "failure_impact": 1-5,
      "likelihood": 1-5,
      "risk_score": 1-25,
      "risk_tier": "T1|T2|T3|T4",
      "test_strategy": "Real|Fake|Stub|Mock|WireMock|Testcontainers",
      "rationale": "<text>"
    }
  ]
}
```

## `state-transition-matrix.json`

```json
{
  "version": "1.0",
  "components": [
    {
      "component_id": "CTA-COMP-001",
      "states": ["START", "Valid Request", "Entity Found", "Return Response", "Error"],
      "transitions": [
        {"from": "START", "to": "Valid Request", "trigger": "<text>"},
        {"from": "Valid Request", "to": "Entity Found", "trigger": "<text>"},
        {"from": "Valid Request", "to": "Entity Missing", "trigger": "<text>"},
        {"from": "Entity Missing", "to": "Exception", "trigger": "<text>"},
        {"from": "Exception", "to": "Error Response", "trigger": "<text>"}
      ],
      "coverage_requirements": {
        "<state>": "<what must be tested>"
      }
    }
  ]
}
```

## `contract-inventory.json`

```json
{
  "version": "1.0",
  "contracts": [
    {
      "id": "CTA-CTC-001",
      "component_id": "CTA-COMP-001",
      "method": "GET|POST|PUT|DELETE|...",
      "path": "/api/...",
      "request_schema": {"<field>": "<type>"},
      "response_schema": {"<field>": "<type>"},
      "error_schema": {"<field>": "<type>"},
      "backward_compat_rules": ["<rule>"],
      "schema_validation": "openapi|jsonschema|protobuf|..."
    }
  ]
}
```

## `risk-priority-ranking.json`

```json
{
  "version": "1.0",
  "rankings": [
    {
      "component_id": "CTA-COMP-001",
      "business_criticality": 1-5,
      "change_frequency": 1-5,
      "dependency_count": 1-5,
      "complexity": 1-5,
      "public_exposure": 1-5,
      "existing_coverage_inverted": 1-5,
      "risk_score": 6-30,
      "priority": "P0|P1|P2|P3"
    }
  ]
}
```

## `mutation-roadmap.json`

```json
{
  "version": "1.0",
  "tools": {
    "primary": "PIT",
    "version": "<ver>",
    "config_path": "<path>"
  },
  "targets": ["<component_id>", ...],
  "exclusions": [
    {"path": "<glob>", "reason": "<text>"}
  ],
  "thresholds": {
    "mutation_score": 0-100,
    "test_strength": 0-100,
    "quality_gate": "block|warn"
  },
  "rollout_phases": [
    {"phase": 1, "components": ["<id>", ...], "target_score": 0-100}
  ]
}
```

## `test-creation-input-schema.json`

(JSON Schema describing the input contract for downstream AI test-generation systems. Emitted in FULL profile only. Schema is per original prompt section 24, with these top-level fields: `github_url`, `branch`, `component`, `source_paths`, `test_paths`, `behaviors`, `dependencies`, `risk_tier`, `missing_scenarios`, `assertions`, `fixtures`, `execution_commands`, `acceptance_criteria`.)

## `handoff-manifest.json`

```json
{
  "produced_at": "<ISO-8601>",
  "profile": "lite|standard|full",
  "repo": "<url>",
  "branch": "<branch>",
  "commit": "<sha>",
  "artifacts": [
    {
      "file": "<name>.json",
      "description": "<text>",
      "consumer": "application-test-coverage|application-mutation-testing|external-ai-test-gen|none",
      "consumer_input_mapping": "<how to consume>"
    }
  ]
}
```
