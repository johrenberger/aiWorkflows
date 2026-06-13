# Technical Report — Skill Governance Pipeline

Started: 2026-06-13T22:26:05Z
Finished: 2026-06-13T22:26:06Z
CI: FAIL

## Inventory

| Name | Type | Tokens | Version | Owner |
| --- | --- | --- | --- | --- |
| README | unknown | 2302 | - | - |
| adr-index | unknown | 864 | - | - |
| agents/ARCHITECT_AGENT | agent | 1158 | - | - |
| agents/CLOUD_SECURITY_AGENT | agent | 2671 | - | - |
| agents/CODE_REVIEW_AGENT | agent | 898 | - | - |
| agents/COMMUNICATIONS_MANAGER_AGENT | agent | 927 | - | - |
| agents/CREATIVE_DIRECTOR_AGENT | agent | 991 | - | - |
| agents/DATA_ANALYST_AGENT | agent | 976 | - | - |
| agents/DEVOPS_AGENT | agent | 876 | - | - |
| agents/DOCUMENTATION_AGENT | agent | 905 | - | - |
| agents/EXECUTIVE_ASSISTANT_AGENT | agent | 959 | - | - |
| agents/FINANCIAL_ANALYST_AGENT | agent | 881 | - | - |
| agents/KNOWLEDGE_MANAGER_AGENT | agent | 1116 | - | - |
| agents/LEGAL_COMPLIANCE_AGENT | agent | 888 | - | - |
| agents/MONITORING_AGENT | agent | 1105 | - | - |
| agents/PEN_TESTING_AGENT | agent | 1819 | - | - |
| agents/PRODUCT_MANAGER_AGENT | agent | 1061 | - | - |
| agents/PROJECT_COORDINATOR_AGENT | agent | 1092 | - | - |
| agents/README | agent | 2288 | - | - |
| agents/RESEARCH_ANALYST_AGENT | agent | 643 | - | - |
| agents/SECURITY_ANALYST_AGENT | agent | 1188 | - | - |
| agents/SOFTWARE_ENGINEER_AGENT | agent | 649 | - | - |
| agents/TEST_AUTOMATION_AGENT | agent | 930 | - | - |
| approval-gate | unknown | 790 | - | - |
| findings-severity | unknown | 816 | - | - |
| go-no-go-summary | unknown | 798 | - | - |
| incident-summary | unknown | 992 | - | - |
| operational-risk-register | unknown | 1101 | - | - |
| risk-register | unknown | 944 | - | - |
| skills/README | skill | 3684 | - | - |
| skills/architecture-decision | skill | 3581 | - | - |
| skills/architecture-review | skill | 3127 | - | - |
| skills/backend-implementation | skill | 3815 | - | - |
| skills/code-change-review | skill | 1363 | - | - |
| skills/database-migration-safety | skill | 1417 | - | - |
| skills/dependency-change-review | skill | 1471 | - | - |
| skills/documentation-update | skill | 2694 | - | - |
| skills/frontend-implementation | skill | 3365 | - | - |
| skills/handoff-packet | skill | 1502 | - | - |
| skills/implementation-orchestrator | skill | 3536 | - | - |
| skills/incident-triage | skill | 3147 | - | - |
| skills/integration-implementation | skill | 4370 | - | - |
| skills/observability-review | skill | 2752 | - | - |
| skills/profiles | skill | 550 | - | - |
| skills/profiles | skill | 458 | - | - |
| skills/profiles | skill | 822 | - | - |
| skills/profiles | skill | 845 | - | - |
| skills/profiles | skill | 574 | - | - |
| skills/profiles | skill | 583 | - | - |
| skills/profiles | skill | 1202 | - | - |
| skills/profiles | skill | 1691 | - | - |
| skills/profiles | skill | 1212 | - | - |
| skills/profiles | skill | 1079 | - | - |
| skills/profiles | skill | 1102 | - | - |
| skills/profiles | skill | 1774 | - | - |
| skills/profiles | skill | 1551 | - | - |
| skills/profiles | skill | 1780 | - | - |
| skills/profiles | skill | 1707 | - | - |
| skills/profiles | skill | 1606 | - | - |
| skills/references | skill | 1096 | - | - |
| skills/references | skill | 1119 | - | - |
| skills/references | skill | 1031 | - | - |
| skills/references | skill | 814 | - | - |
| skills/references | skill | 1085 | - | - |
| skills/references | skill | 1353 | - | - |
| skills/references | skill | 1153 | - | - |
| skills/references | skill | 1219 | - | - |
| skills/references | skill | 1187 | - | - |
| skills/references | skill | 1403 | - | - |
| skills/references | skill | 1246 | - | - |
| skills/references | skill | 1174 | - | - |
| skills/references | skill | 864 | - | - |
| skills/references | skill | 1200 | - | - |
| skills/references | skill | 892 | - | - |
| skills/references | skill | 876 | - | - |
| skills/references | skill | 671 | - | - |
| skills/references | skill | 702 | - | - |
| skills/references | skill | 687 | - | - |
| skills/references | skill | 964 | - | - |
| skills/references | skill | 679 | - | - |
| skills/release-readiness | skill | 3227 | - | - |
| skills/repo-discovery | skill | 1741 | - | - |
| skills/runbook-authoring | skill | 3135 | - | - |
| skills/security-review | skill | 1417 | - | - |
| skills/task-state-management | skill | 2443 | - | - |
| skills/templates | skill | 1239 | - | - |
| skills/templates | skill | 1378 | - | - |
| skills/templates | skill | 1520 | - | - |
| skills/templates | skill | 636 | - | - |
| skills/templates | skill | 542 | - | - |
| skills/templates | skill | 801 | - | - |
| skills/templates | skill | 595 | - | - |
| skills/templates | skill | 960 | - | - |
| skills/templates | skill | 1157 | - | - |
| skills/templates | skill | 1004 | - | - |
| skills/templates | skill | 1111 | - | - |
| skills/templates | skill | 474 | - | - |
| skills/templates | skill | 1273 | - | - |
| skills/templates | skill | 508 | - | - |
| skills/templates | skill | 1650 | - | - |
| skills/templates | skill | 787 | - | - |
| skills/templates | skill | 1569 | - | - |
| skills/templates | skill | 1256 | - | - |
| skills/templates | skill | 845 | - | - |
| skills/templates | skill | 1268 | - | - |
| skills/templates | skill | 1747 | - | - |
| skills/templates | skill | 1108 | - | - |
| skills/templates | skill | 564 | - | - |
| skills/templates | skill | 1110 | - | - |
| skills/templates | skill | 1409 | - | - |
| skills/templates | skill | 929 | - | - |
| skills/templates | skill | 592 | - | - |
| skills/templates | skill | 105 | - | - |
| skills/templates | skill | 133 | - | - |
| skills/templates | skill | 98 | - | - |
| skills/templates | skill | 134 | - | - |
| skills/templates | skill | 543 | - | - |
| skills/templates | skill | 468 | - | - |
| skills/templates | skill | 389 | - | - |
| skills/test-gap-analysis | skill | 2286 | - | - |
| skills/test-generation | skill | 1641 | - | - |
| skills/test_fixtures | skill | 12 | - | - |
| skills/test_fixtures | skill | 1 | - | - |
| skills/test_fixtures | skill | 119 | - | - |
| skills/validation-runner | skill | 2707 | - | - |
| task-spec-packet | unknown | 1294 | - | - |

## Findings

| Severity | Artifact | Category | Message |
| --- | --- | --- | --- |
| blocking | README | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | README | metadata | Purpose is missing or too short / vague. |
| blocking | README | contract | Inputs contract is missing or unstructured. |
| blocking | README | contract | Outputs contract is missing or unstructured. |
| blocking | README | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | README | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| blocking | agents/ARCHITECT_AGENT | discovery | Path does not exist: agents/ARCHITECT_AGENT.md |
| blocking | agents/CLOUD_SECURITY_AGENT | discovery | Path does not exist: agents/CLOUD_SECURITY_AGENT.md |
| blocking | agents/CODE_REVIEW_AGENT | discovery | Path does not exist: agents/CODE_REVIEW_AGENT.md |
| blocking | agents/COMMUNICATIONS_MANAGER_AGENT | discovery | Path does not exist: agents/COMMUNICATIONS_MANAGER_AGENT.md |
| blocking | agents/CREATIVE_DIRECTOR_AGENT | discovery | Path does not exist: agents/CREATIVE_DIRECTOR_AGENT.md |
| blocking | agents/DATA_ANALYST_AGENT | discovery | Path does not exist: agents/DATA_ANALYST_AGENT.md |
| blocking | agents/DEVOPS_AGENT | discovery | Path does not exist: agents/DEVOPS_AGENT.md |
| blocking | agents/DOCUMENTATION_AGENT | discovery | Path does not exist: agents/DOCUMENTATION_AGENT.md |
| blocking | agents/EXECUTIVE_ASSISTANT_AGENT | discovery | Path does not exist: agents/EXECUTIVE_ASSISTANT_AGENT.md |
| blocking | agents/FINANCIAL_ANALYST_AGENT | discovery | Path does not exist: agents/FINANCIAL_ANALYST_AGENT.md |
| blocking | agents/KNOWLEDGE_MANAGER_AGENT | discovery | Path does not exist: agents/KNOWLEDGE_MANAGER_AGENT.md |
| blocking | agents/LEGAL_COMPLIANCE_AGENT | discovery | Path does not exist: agents/LEGAL_COMPLIANCE_AGENT.md |
| blocking | agents/MONITORING_AGENT | discovery | Path does not exist: agents/MONITORING_AGENT.md |
| blocking | agents/PEN_TESTING_AGENT | discovery | Path does not exist: agents/PEN_TESTING_AGENT.md |
| blocking | agents/PRODUCT_MANAGER_AGENT | discovery | Path does not exist: agents/PRODUCT_MANAGER_AGENT.md |
| blocking | agents/PROJECT_COORDINATOR_AGENT | discovery | Path does not exist: agents/PROJECT_COORDINATOR_AGENT.md |
| blocking | agents/README | discovery | Path does not exist: agents/README.md |
| blocking | agents/RESEARCH_ANALYST_AGENT | discovery | Path does not exist: agents/RESEARCH_ANALYST_AGENT.md |
| blocking | agents/SECURITY_ANALYST_AGENT | discovery | Path does not exist: agents/SECURITY_ANALYST_AGENT.md |
| blocking | agents/SOFTWARE_ENGINEER_AGENT | discovery | Path does not exist: agents/SOFTWARE_ENGINEER_AGENT.md |
| blocking | agents/TEST_AUTOMATION_AGENT | discovery | Path does not exist: agents/TEST_AUTOMATION_AGENT.md |
| blocking | skills/README | discovery | Path does not exist: skills/README.md |
| blocking | skills/architecture-decision | discovery | Path does not exist: skills/architecture-decision/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/architecture-decision/references/decision-quality-checklist.md |
| blocking | skills/templates | discovery | Path does not exist: skills/architecture-decision/templates/adr.md |
| blocking | skills/templates | discovery | Path does not exist: skills/architecture-decision/templates/architecture-options-analysis.md |
| blocking | skills/architecture-review | discovery | Path does not exist: skills/architecture-review/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/architecture-review/references/architecture-risk-checklist.md |
| blocking | skills/references | discovery | Path does not exist: skills/architecture-review/references/distributed-systems-checklist.md |
| blocking | skills/references | discovery | Path does not exist: skills/architecture-review/references/modular-monolith-checklist.md |
| blocking | skills/templates | discovery | Path does not exist: skills/architecture-review/templates/architecture-review-report.md |
| blocking | skills/backend-implementation | discovery | Path does not exist: skills/backend-implementation/SKILL.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/backend-implementation/references/profiles/dotnet.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/backend-implementation/references/profiles/go.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/backend-implementation/references/profiles/java-spring.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/backend-implementation/references/profiles/mixed-monolith.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/backend-implementation/references/profiles/node-typescript.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/backend-implementation/references/profiles/python.md |
| blocking | skills/templates | discovery | Path does not exist: skills/backend-implementation/templates/backend-implementation-report.md |
| blocking | skills/code-change-review | discovery | Path does not exist: skills/code-change-review/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/code-change-review/references/review-severity.md |
| blocking | skills/templates | discovery | Path does not exist: skills/code-change-review/templates/code-review-report.md |
| blocking | skills/database-migration-safety | discovery | Path does not exist: skills/database-migration-safety/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/database-migration-safety/references/migration-risk-checklist.md |
| blocking | skills/templates | discovery | Path does not exist: skills/database-migration-safety/templates/migration-safety-report.md |
| blocking | skills/dependency-change-review | discovery | Path does not exist: skills/dependency-change-review/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/dependency-change-review/references/dependency-risk-checklist.md |
| blocking | skills/templates | discovery | Path does not exist: skills/dependency-change-review/templates/dependency-change-report.md |
| blocking | skills/documentation-update | discovery | Path does not exist: skills/documentation-update/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/documentation-update/references/doc-source-of-truth.md |
| blocking | skills/test_fixtures | discovery | Path does not exist: skills/documentation-update/scripts/documentation-update-scripts/test_fixtures/README.md |
| blocking | skills/test_fixtures | discovery | Path does not exist: skills/documentation-update/scripts/documentation-update-scripts/test_fixtures/self.md |
| blocking | skills/templates | discovery | Path does not exist: skills/documentation-update/templates/api-doc-update-checklist.md |
| blocking | skills/templates | discovery | Path does not exist: skills/documentation-update/templates/documentation-impact-report.md |
| blocking | skills/templates | discovery | Path does not exist: skills/documentation-update/templates/readme-update-checklist.md |
| blocking | skills/frontend-implementation | discovery | Path does not exist: skills/frontend-implementation/SKILL.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/frontend-implementation/references/profiles/angular.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/frontend-implementation/references/profiles/nextjs.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/frontend-implementation/references/profiles/react.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/frontend-implementation/references/profiles/static-ui.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/frontend-implementation/references/profiles/vue.md |
| blocking | skills/templates | discovery | Path does not exist: skills/frontend-implementation/templates/frontend-implementation-report.md |
| blocking | skills/handoff-packet | discovery | Path does not exist: skills/handoff-packet/SKILL.md |
| blocking | skills/templates | discovery | Path does not exist: skills/handoff-packet/templates/handoff-packet.md |
| blocking | skills/implementation-orchestrator | discovery | Path does not exist: skills/implementation-orchestrator/SKILL.md |
| blocking | skills/templates | discovery | Path does not exist: skills/implementation-orchestrator/templates/implementation-routing-report.md |
| blocking | skills/incident-triage | discovery | Path does not exist: skills/incident-triage/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/incident-triage/references/incident-severity-guide.md |
| blocking | skills/templates | discovery | Path does not exist: skills/incident-triage/templates/action-item.md |
| blocking | skills/templates | discovery | Path does not exist: skills/incident-triage/templates/incident-triage-report.md |
| blocking | skills/templates | discovery | Path does not exist: skills/incident-triage/templates/timeline.md |
| blocking | skills/integration-implementation | discovery | Path does not exist: skills/integration-implementation/SKILL.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/integration-implementation/references/profiles/async-messaging.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/integration-implementation/references/profiles/contract-testing.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/integration-implementation/references/profiles/file-batch.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/integration-implementation/references/profiles/rest-api.md |
| blocking | skills/profiles | discovery | Path does not exist: skills/integration-implementation/references/profiles/webhook.md |
| blocking | skills/templates | discovery | Path does not exist: skills/integration-implementation/templates/integration-implementation-report.md |
| blocking | skills/observability-review | discovery | Path does not exist: skills/observability-review/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/observability-review/references/logging-metrics-tracing-checklist.md |
| blocking | skills/templates | discovery | Path does not exist: skills/observability-review/templates/observability-review-report.md |
| blocking | skills/templates | discovery | Path does not exist: skills/observability-review/templates/slo-review.md |
| blocking | skills/release-readiness | discovery | Path does not exist: skills/release-readiness/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/release-readiness/references/release-gate-checklist.md |
| blocking | skills/templates | discovery | Path does not exist: skills/release-readiness/templates/go-no-go-checklist.md |
| blocking | skills/templates | discovery | Path does not exist: skills/release-readiness/templates/release-readiness-report.md |
| blocking | skills/templates | discovery | Path does not exist: skills/release-readiness/templates/release-risk-register.md |
| blocking | skills/repo-discovery | discovery | Path does not exist: skills/repo-discovery/SKILL.md |
| blocking | skills/templates | discovery | Path does not exist: skills/repo-discovery/templates/repo-discovery-report.md |
| blocking | skills/runbook-authoring | discovery | Path does not exist: skills/runbook-authoring/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/runbook-authoring/references/runbook-quality-checklist.md |
| blocking | skills/test_fixtures | discovery | Path does not exist: skills/runbook-authoring/scripts/runbook-authoring-scripts/test_fixtures/latency-spike.md |
| blocking | skills/templates | discovery | Path does not exist: skills/runbook-authoring/templates/runbook-authoring-report.md |
| blocking | skills/templates | discovery | Path does not exist: skills/runbook-authoring/templates/runbook.md |
| blocking | skills/templates | discovery | Path does not exist: skills/runbook-authoring/templates/troubleshooting-guide.md |
| blocking | skills/security-review | discovery | Path does not exist: skills/security-review/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/security-review/references/authz-review-checklist.md |
| blocking | skills/references | discovery | Path does not exist: skills/security-review/references/owasp-checklist.md |
| blocking | skills/references | discovery | Path does not exist: skills/security-review/references/secrets-review-checklist.md |
| blocking | skills/templates | discovery | Path does not exist: skills/security-review/templates/security-review-report.md |
| blocking | skills/task-state-management | discovery | Path does not exist: skills/task-state-management/SKILL.md |
| blocking | skills/templates | discovery | Path does not exist: skills/task-state-management/templates/blocker.md |
| blocking | skills/templates | discovery | Path does not exist: skills/task-state-management/templates/decision-log.md |
| blocking | skills/templates | discovery | Path does not exist: skills/task-state-management/templates/state.json |
| blocking | skills/templates | discovery | Path does not exist: skills/task-state-management/templates/task.md |
| blocking | skills/test-gap-analysis | discovery | Path does not exist: skills/test-gap-analysis/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/test-gap-analysis/references/risk-weighting.md |
| blocking | skills/templates | discovery | Path does not exist: skills/test-gap-analysis/templates/test-gap-report.md |
| blocking | skills/test-generation | discovery | Path does not exist: skills/test-generation/SKILL.md |
| blocking | skills/references | discovery | Path does not exist: skills/test-generation/references/dotnet-testing.md |
| blocking | skills/references | discovery | Path does not exist: skills/test-generation/references/go-testing.md |
| blocking | skills/references | discovery | Path does not exist: skills/test-generation/references/jest-vitest.md |
| blocking | skills/references | discovery | Path does not exist: skills/test-generation/references/junit-spring.md |
| blocking | skills/references | discovery | Path does not exist: skills/test-generation/references/pytest-unittest.md |
| blocking | skills/templates | discovery | Path does not exist: skills/test-generation/templates/test-generation-report.md |
| blocking | skills/validation-runner | discovery | Path does not exist: skills/validation-runner/SKILL.md |
| blocking | skills/templates | discovery | Path does not exist: skills/validation-runner/templates/validation-report.md |
| blocking | adr-index | discovery | Path does not exist: templates/adr-index.md |
| blocking | approval-gate | discovery | Path does not exist: templates/approval-gate.md |
| blocking | findings-severity | discovery | Path does not exist: templates/findings-severity.md |
| blocking | go-no-go-summary | discovery | Path does not exist: templates/go-no-go-summary.md |
| blocking | incident-summary | discovery | Path does not exist: templates/incident-summary.md |
| blocking | operational-risk-register | discovery | Path does not exist: templates/operational-risk-register.md |
| blocking | risk-register | discovery | Path does not exist: templates/risk-register.md |
| blocking | task-spec-packet | discovery | Path does not exist: templates/task-spec-packet.md |
| blocking | skills/architecture-decision | dependency | Circular dependency: skills/architecture-decision -> skills/architecture-review -> skills/architecture-decision |
| blocking | skills/backend-implementation | dependency | Circular dependency: skills/backend-implementation -> skills/implementation-orchestrator -> skills/backend-implementation |
| blocking | skills/frontend-implementation | dependency | Circular dependency: skills/frontend-implementation -> skills/implementation-orchestrator -> skills/frontend-implementation |
| blocking | skills/test-gap-analysis | dependency | Circular dependency: skills/test-gap-analysis -> skills/test-generation -> skills/test-gap-analysis |

## Dependency graph
- Nodes: 56
- Missing: 0
- Circular: 4
- Unused: 0

## Responsibility

| Flag | Count |
| --- | --- |
| over-broad | 22 |
| unclear | 104 |

### Over-broad skills (first 5)
- `agents/CODE_REVIEW_AGENT` (score=50): Detected 4 distinct actions: design, detect, review, test. Skill may be over-broad; consider tightening scope.
- `agents/DATA_ANALYST_AGENT` (score=50): Detected 4 distinct actions: analyze, build, create, report. Skill may be over-broad; consider tightening scope.
- `agents/MONITORING_AGENT` (score=50): Detected 4 distinct actions: alert, build, detect, monitor. Skill may be over-broad; consider tightening scope.
- `agents/PEN_TESTING_AGENT` (score=50): Detected 4 distinct actions: deploy, execute, report, test. Skill may be over-broad; consider tightening scope.
- `agents/SOFTWARE_ENGINEER_AGENT` (score=50): Detected 4 distinct actions: design, refactor, review, test. Skill may be over-broad; consider tightening scope.

## Overlap (top 10 pairs)

| Artifact A | Artifact B | Score | Recommendation |
| --- | --- | --- | --- |
| skills/templates | skills/templates | 55 | keep_separate |
| skills/backend-implementation | skills/frontend-implementation | 54 | keep_separate |
| skills/templates | skills/templates | 54 | keep_separate |
| skills/profiles | skills/profiles | 53 | keep_separate |
| skills/profiles | skills/profiles | 52 | keep_separate |
| skills/templates | skills/templates | 49 | keep_separate |
| skills/profiles | skills/profiles | 48 | keep_separate |
| skills/templates | skills/templates | 43 | keep_separate |
| skills/templates | skills/templates | 42 | keep_separate |
| skills/templates | skills/templates | 42 | keep_separate |

## Scorecard
| Name | ROI | Decision | Rationale |
| --- | --- | --- | --- |
| README | 32 | rewrite | Score 32; rewrite triggered by 4 blocking + 2 warnings. |
| agents/ARCHITECT_AGENT | 43 | rewrite | Score 43; rewrite triggered by 1 blocking + 0 warnings. |
| agents/CLOUD_SECURITY_AGENT | 42 | rewrite | Score 42; rewrite triggered by 1 blocking + 0 warnings. |
| agents/CODE_REVIEW_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/COMMUNICATIONS_MANAGER_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/CREATIVE_DIRECTOR_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/DATA_ANALYST_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/DEVOPS_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/DOCUMENTATION_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/EXECUTIVE_ASSISTANT_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/FINANCIAL_ANALYST_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/KNOWLEDGE_MANAGER_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/LEGAL_COMPLIANCE_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/MONITORING_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/PEN_TESTING_AGENT | 43 | rewrite | Score 43; rewrite triggered by 1 blocking + 0 warnings. |
| agents/PRODUCT_MANAGER_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/PROJECT_COORDINATOR_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/README | 42 | rewrite | Score 42; rewrite triggered by 1 blocking + 0 warnings. |
| agents/RESEARCH_ANALYST_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/SECURITY_ANALYST_AGENT | 43 | rewrite | Score 43; rewrite triggered by 1 blocking + 0 warnings. |
| agents/SOFTWARE_ENGINEER_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| agents/TEST_AUTOMATION_AGENT | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| skills/README | 40 | rewrite | Score 40; rewrite triggered by 1 blocking + 0 warnings. |
| skills/architecture-decision | 31 | rewrite | Score 31; rewrite triggered by 2 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/architecture-review | 41 | rewrite | Score 41; rewrite triggered by 1 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/backend-implementation | 30 | rewrite | Score 30; rewrite triggered by 2 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/code-change-review | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/database-migration-safety | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/dependency-change-review | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/documentation-update | 42 | rewrite | Score 42; rewrite triggered by 1 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/test_fixtures | 35 | rewrite | Score 35; rewrite triggered by 3 blocking + 0 warnings. |
| skills/test_fixtures | 35 | rewrite | Score 35; rewrite triggered by 3 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/frontend-implementation | 31 | rewrite | Score 31; rewrite triggered by 2 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/handoff-packet | 43 | rewrite | Score 43; rewrite triggered by 1 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/implementation-orchestrator | 41 | rewrite | Score 41; rewrite triggered by 1 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/incident-triage | 41 | rewrite | Score 41; rewrite triggered by 1 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/integration-implementation | 40 | rewrite | Score 40; rewrite triggered by 1 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/profiles | 33 | rewrite | Score 33; rewrite triggered by 16 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/observability-review | 42 | rewrite | Score 42; rewrite triggered by 1 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/release-readiness | 41 | rewrite | Score 41; rewrite triggered by 1 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/repo-discovery | 43 | rewrite | Score 43; rewrite triggered by 1 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/runbook-authoring | 41 | rewrite | Score 41; rewrite triggered by 1 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/test_fixtures | 35 | rewrite | Score 35; rewrite triggered by 3 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/security-review | 43 | rewrite | Score 43; rewrite triggered by 1 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/task-state-management | 42 | rewrite | Score 42; rewrite triggered by 1 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/test-gap-analysis | 32 | rewrite | Score 32; rewrite triggered by 2 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/test-generation | 43 | rewrite | Score 43; rewrite triggered by 1 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/references | 33 | rewrite | Score 33; rewrite triggered by 21 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| skills/validation-runner | 42 | rewrite | Score 42; rewrite triggered by 1 blocking + 0 warnings. |
| skills/templates | 31 | rewrite | Score 31; rewrite triggered by 34 blocking + 0 warnings. |
| adr-index | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| approval-gate | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| findings-severity | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| go-no-go-summary | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| incident-summary | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| operational-risk-register | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| risk-register | 44 | rewrite | Score 44; rewrite triggered by 1 blocking + 0 warnings. |
| task-spec-packet | 43 | rewrite | Score 43; rewrite triggered by 1 blocking + 0 warnings. |
