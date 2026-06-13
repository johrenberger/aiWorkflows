# Technical Report — Skill Governance Pipeline

Started: 2026-06-13T23:44:13Z
Finished: 2026-06-13T23:44:13Z
CI: FAIL

## Inventory

| Name | Type | Tokens | Version | Owner |
| --- | --- | --- | --- | --- |
| README | unknown | 3687 | - | - |
| README | unknown | 12 | - | - |
| SKILL | skill | 3736 | - | - |
| SKILL | skill | 3127 | - | - |
| SKILL | skill | 3815 | - | - |
| SKILL | skill | 1363 | - | - |
| SKILL | skill | 1417 | - | - |
| SKILL | skill | 1471 | - | - |
| SKILL | skill | 2694 | - | - |
| SKILL | skill | 3365 | - | - |
| SKILL | skill | 1502 | - | - |
| SKILL | skill | 2524 | - | - |
| SKILL | skill | 3147 | - | - |
| SKILL | skill | 4370 | - | - |
| SKILL | skill | 2752 | - | - |
| SKILL | skill | 3227 | - | - |
| SKILL | skill | 1741 | - | - |
| SKILL | skill | 3135 | - | - |
| SKILL | skill | 1417 | - | - |
| SKILL | skill | 2443 | - | - |
| SKILL | skill | 2286 | - | - |
| SKILL | skill | 1641 | - | - |
| SKILL | skill | 2707 | - | - |
| action-item | unknown | 508 | - | - |
| adr | unknown | 1239 | - | - |
| angular | unknown | 1202 | - | - |
| api-doc-update-checklist | unknown | 960 | - | - |
| architecture-options-analysis | unknown | 1378 | - | - |
| architecture-review-report | unknown | 1520 | - | - |
| architecture-risk-checklist | unknown | 1119 | - | - |
| async-messaging | unknown | 1774 | - | - |
| authz-review-checklist | unknown | 864 | - | - |
| backend-implementation-report | unknown | 636 | - | - |
| blocker | unknown | 105 | - | - |
| code-review-report | unknown | 542 | - | - |
| contract-testing | unknown | 1551 | - | - |
| decision-log | unknown | 133 | - | - |
| decision-quality-checklist | unknown | 1096 | - | - |
| dependency-change-report | unknown | 595 | - | - |
| dependency-risk-checklist | unknown | 1153 | - | - |
| distributed-systems-checklist | unknown | 1031 | - | - |
| doc-source-of-truth | unknown | 1219 | - | - |
| documentation-impact-report | unknown | 1157 | - | - |
| dotnet | unknown | 550 | - | - |
| dotnet-testing | unknown | 671 | - | - |
| file-batch | unknown | 1780 | - | - |
| frontend-implementation-report | unknown | 1111 | - | - |
| go | unknown | 458 | - | - |
| go-no-go-checklist | unknown | 1268 | - | - |
| go-testing | unknown | 702 | - | - |
| handoff-and-forbidden | unknown | 559 | - | - |
| handoff-packet | unknown | 474 | - | - |
| implementation-routing-report | unknown | 1273 | - | - |
| incident-severity-guide | unknown | 1187 | - | - |
| incident-triage-report | unknown | 1650 | - | - |
| integration-implementation-report | unknown | 1569 | - | - |
| java-spring | unknown | 822 | - | - |
| jest-vitest | unknown | 687 | - | - |
| junit-spring | unknown | 964 | - | - |
| latency-spike | unknown | 119 | - | - |
| logging-metrics-tracing-checklist | unknown | 1403 | - | - |
| migration-risk-checklist | unknown | 1353 | - | - |
| migration-safety-report | unknown | 801 | - | - |
| mixed-monolith | unknown | 845 | - | - |
| modular-monolith-checklist | unknown | 814 | - | - |
| nextjs | unknown | 1691 | - | - |
| node-typescript | unknown | 574 | - | - |
| observability-review-report | unknown | 1256 | - | - |
| owasp-checklist | unknown | 1200 | - | - |
| pytest-unittest | unknown | 679 | - | - |
| python | unknown | 583 | - | - |
| react | unknown | 1212 | - | - |
| readme-update-checklist | unknown | 1004 | - | - |
| release-gate-checklist | unknown | 1246 | - | - |
| release-readiness-report | unknown | 1747 | - | - |
| release-risk-register | unknown | 1108 | - | - |
| repo-discovery-report | unknown | 564 | - | - |
| rest-api | unknown | 1707 | - | - |
| review-severity | unknown | 1085 | - | - |
| risk-weighting | unknown | 876 | - | - |
| runbook | unknown | 1409 | - | - |
| runbook-authoring-report | unknown | 1110 | - | - |
| runbook-quality-checklist | unknown | 1174 | - | - |
| secrets-review-checklist | unknown | 892 | - | - |
| security-review-report | unknown | 592 | - | - |
| self | unknown | 1 | - | - |
| slo-review | unknown | 845 | - | - |
| state | unknown | 98 | - | - |
| static-ui | unknown | 1079 | - | - |
| stop-and-validation | unknown | 371 | - | - |
| task | unknown | 134 | - | - |
| test-gap-report | unknown | 543 | - | - |
| test-generation-report | unknown | 468 | - | - |
| timeline | unknown | 787 | - | - |
| troubleshooting-guide | unknown | 929 | - | - |
| validation-report | unknown | 389 | - | - |
| vue | unknown | 1102 | - | - |
| webhook | unknown | 1606 | - | - |
| workflow | unknown | 1243 | - | - |

## Findings

| Severity | Artifact | Category | Message |
| --- | --- | --- | --- |
| warning | README | discovery | Artifact 'README' is not a skill or agent (path: README.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | decision-quality-checklist | discovery | Artifact 'decision-quality-checklist' is not a skill or agent (path: architecture-decision/references/decision-quality-checklist.md). Skipping contract validation. |
| warning | adr | discovery | Artifact 'adr' is not a skill or agent (path: architecture-decision/templates/adr.md). Skipping contract validation. |
| warning | architecture-options-analysis | discovery | Artifact 'architecture-options-analysis' is not a skill or agent (path: architecture-decision/templates/architecture-options-analysis.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | architecture-risk-checklist | discovery | Artifact 'architecture-risk-checklist' is not a skill or agent (path: architecture-review/references/architecture-risk-checklist.md). Skipping contract validation. |
| warning | distributed-systems-checklist | discovery | Artifact 'distributed-systems-checklist' is not a skill or agent (path: architecture-review/references/distributed-systems-checklist.md). Skipping contract validation. |
| warning | modular-monolith-checklist | discovery | Artifact 'modular-monolith-checklist' is not a skill or agent (path: architecture-review/references/modular-monolith-checklist.md). Skipping contract validation. |
| warning | architecture-review-report | discovery | Artifact 'architecture-review-report' is not a skill or agent (path: architecture-review/templates/architecture-review-report.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | dotnet | discovery | Artifact 'dotnet' is not a skill or agent (path: backend-implementation/references/profiles/dotnet.md). Skipping contract validation. |
| warning | go | discovery | Artifact 'go' is not a skill or agent (path: backend-implementation/references/profiles/go.md). Skipping contract validation. |
| warning | java-spring | discovery | Artifact 'java-spring' is not a skill or agent (path: backend-implementation/references/profiles/java-spring.md). Skipping contract validation. |
| warning | mixed-monolith | discovery | Artifact 'mixed-monolith' is not a skill or agent (path: backend-implementation/references/profiles/mixed-monolith.md). Skipping contract validation. |
| warning | node-typescript | discovery | Artifact 'node-typescript' is not a skill or agent (path: backend-implementation/references/profiles/node-typescript.md). Skipping contract validation. |
| warning | python | discovery | Artifact 'python' is not a skill or agent (path: backend-implementation/references/profiles/python.md). Skipping contract validation. |
| warning | backend-implementation-report | discovery | Artifact 'backend-implementation-report' is not a skill or agent (path: backend-implementation/templates/backend-implementation-report.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | review-severity | discovery | Artifact 'review-severity' is not a skill or agent (path: code-change-review/references/review-severity.md). Skipping contract validation. |
| warning | code-review-report | discovery | Artifact 'code-review-report' is not a skill or agent (path: code-change-review/templates/code-review-report.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | migration-risk-checklist | discovery | Artifact 'migration-risk-checklist' is not a skill or agent (path: database-migration-safety/references/migration-risk-checklist.md). Skipping contract validation. |
| warning | migration-safety-report | discovery | Artifact 'migration-safety-report' is not a skill or agent (path: database-migration-safety/templates/migration-safety-report.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | dependency-risk-checklist | discovery | Artifact 'dependency-risk-checklist' is not a skill or agent (path: dependency-change-review/references/dependency-risk-checklist.md). Skipping contract validation. |
| warning | dependency-change-report | discovery | Artifact 'dependency-change-report' is not a skill or agent (path: dependency-change-review/templates/dependency-change-report.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | doc-source-of-truth | discovery | Artifact 'doc-source-of-truth' is not a skill or agent (path: documentation-update/references/doc-source-of-truth.md). Skipping contract validation. |
| warning | README | discovery | Artifact 'README' is not a skill or agent (path: documentation-update/scripts/test_fixtures/README.md). Skipping contract validation. |
| warning | self | discovery | Artifact 'self' is not a skill or agent (path: documentation-update/scripts/test_fixtures/self.md). Skipping contract validation. |
| warning | api-doc-update-checklist | discovery | Artifact 'api-doc-update-checklist' is not a skill or agent (path: documentation-update/templates/api-doc-update-checklist.md). Skipping contract validation. |
| warning | documentation-impact-report | discovery | Artifact 'documentation-impact-report' is not a skill or agent (path: documentation-update/templates/documentation-impact-report.md). Skipping contract validation. |
| warning | readme-update-checklist | discovery | Artifact 'readme-update-checklist' is not a skill or agent (path: documentation-update/templates/readme-update-checklist.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | angular | discovery | Artifact 'angular' is not a skill or agent (path: frontend-implementation/references/profiles/angular.md). Skipping contract validation. |
| warning | nextjs | discovery | Artifact 'nextjs' is not a skill or agent (path: frontend-implementation/references/profiles/nextjs.md). Skipping contract validation. |
| warning | react | discovery | Artifact 'react' is not a skill or agent (path: frontend-implementation/references/profiles/react.md). Skipping contract validation. |
| warning | static-ui | discovery | Artifact 'static-ui' is not a skill or agent (path: frontend-implementation/references/profiles/static-ui.md). Skipping contract validation. |
| warning | vue | discovery | Artifact 'vue' is not a skill or agent (path: frontend-implementation/references/profiles/vue.md). Skipping contract validation. |
| warning | frontend-implementation-report | discovery | Artifact 'frontend-implementation-report' is not a skill or agent (path: frontend-implementation/templates/frontend-implementation-report.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | handoff-packet | discovery | Artifact 'handoff-packet' is not a skill or agent (path: handoff-packet/templates/handoff-packet.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | handoff-and-forbidden | discovery | Artifact 'handoff-and-forbidden' is not a skill or agent (path: implementation-orchestrator/references/handoff-and-forbidden.md). Skipping contract validation. |
| warning | stop-and-validation | discovery | Artifact 'stop-and-validation' is not a skill or agent (path: implementation-orchestrator/references/stop-and-validation.md). Skipping contract validation. |
| warning | workflow | discovery | Artifact 'workflow' is not a skill or agent (path: implementation-orchestrator/references/workflow.md). Skipping contract validation. |
| warning | implementation-routing-report | discovery | Artifact 'implementation-routing-report' is not a skill or agent (path: implementation-orchestrator/templates/implementation-routing-report.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | incident-severity-guide | discovery | Artifact 'incident-severity-guide' is not a skill or agent (path: incident-triage/references/incident-severity-guide.md). Skipping contract validation. |
| warning | action-item | discovery | Artifact 'action-item' is not a skill or agent (path: incident-triage/templates/action-item.md). Skipping contract validation. |
| warning | incident-triage-report | discovery | Artifact 'incident-triage-report' is not a skill or agent (path: incident-triage/templates/incident-triage-report.md). Skipping contract validation. |
| warning | timeline | discovery | Artifact 'timeline' is not a skill or agent (path: incident-triage/templates/timeline.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | async-messaging | discovery | Artifact 'async-messaging' is not a skill or agent (path: integration-implementation/references/profiles/async-messaging.md). Skipping contract validation. |
| warning | contract-testing | discovery | Artifact 'contract-testing' is not a skill or agent (path: integration-implementation/references/profiles/contract-testing.md). Skipping contract validation. |
| warning | file-batch | discovery | Artifact 'file-batch' is not a skill or agent (path: integration-implementation/references/profiles/file-batch.md). Skipping contract validation. |
| warning | rest-api | discovery | Artifact 'rest-api' is not a skill or agent (path: integration-implementation/references/profiles/rest-api.md). Skipping contract validation. |
| warning | webhook | discovery | Artifact 'webhook' is not a skill or agent (path: integration-implementation/references/profiles/webhook.md). Skipping contract validation. |
| warning | integration-implementation-report | discovery | Artifact 'integration-implementation-report' is not a skill or agent (path: integration-implementation/templates/integration-implementation-report.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | logging-metrics-tracing-checklist | discovery | Artifact 'logging-metrics-tracing-checklist' is not a skill or agent (path: observability-review/references/logging-metrics-tracing-checklist.md). Skipping contract validation. |
| warning | observability-review-report | discovery | Artifact 'observability-review-report' is not a skill or agent (path: observability-review/templates/observability-review-report.md). Skipping contract validation. |
| warning | slo-review | discovery | Artifact 'slo-review' is not a skill or agent (path: observability-review/templates/slo-review.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | release-gate-checklist | discovery | Artifact 'release-gate-checklist' is not a skill or agent (path: release-readiness/references/release-gate-checklist.md). Skipping contract validation. |
| warning | go-no-go-checklist | discovery | Artifact 'go-no-go-checklist' is not a skill or agent (path: release-readiness/templates/go-no-go-checklist.md). Skipping contract validation. |
| warning | release-readiness-report | discovery | Artifact 'release-readiness-report' is not a skill or agent (path: release-readiness/templates/release-readiness-report.md). Skipping contract validation. |
| warning | release-risk-register | discovery | Artifact 'release-risk-register' is not a skill or agent (path: release-readiness/templates/release-risk-register.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | repo-discovery-report | discovery | Artifact 'repo-discovery-report' is not a skill or agent (path: repo-discovery/templates/repo-discovery-report.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | runbook-quality-checklist | discovery | Artifact 'runbook-quality-checklist' is not a skill or agent (path: runbook-authoring/references/runbook-quality-checklist.md). Skipping contract validation. |
| warning | latency-spike | discovery | Artifact 'latency-spike' is not a skill or agent (path: runbook-authoring/scripts/test_fixtures/latency-spike.md). Skipping contract validation. |
| warning | runbook-authoring-report | discovery | Artifact 'runbook-authoring-report' is not a skill or agent (path: runbook-authoring/templates/runbook-authoring-report.md). Skipping contract validation. |
| warning | runbook | discovery | Artifact 'runbook' is not a skill or agent (path: runbook-authoring/templates/runbook.md). Skipping contract validation. |
| warning | troubleshooting-guide | discovery | Artifact 'troubleshooting-guide' is not a skill or agent (path: runbook-authoring/templates/troubleshooting-guide.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | authz-review-checklist | discovery | Artifact 'authz-review-checklist' is not a skill or agent (path: security-review/references/authz-review-checklist.md). Skipping contract validation. |
| warning | owasp-checklist | discovery | Artifact 'owasp-checklist' is not a skill or agent (path: security-review/references/owasp-checklist.md). Skipping contract validation. |
| warning | secrets-review-checklist | discovery | Artifact 'secrets-review-checklist' is not a skill or agent (path: security-review/references/secrets-review-checklist.md). Skipping contract validation. |
| warning | security-review-report | discovery | Artifact 'security-review-report' is not a skill or agent (path: security-review/templates/security-review-report.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | blocker | discovery | Artifact 'blocker' is not a skill or agent (path: task-state-management/templates/blocker.md). Skipping contract validation. |
| warning | decision-log | discovery | Artifact 'decision-log' is not a skill or agent (path: task-state-management/templates/decision-log.md). Skipping contract validation. |
| warning | state | discovery | Artifact 'state' is not a skill or agent (path: task-state-management/templates/state.json). Skipping contract validation. |
| warning | task | discovery | Artifact 'task' is not a skill or agent (path: task-state-management/templates/task.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | risk-weighting | discovery | Artifact 'risk-weighting' is not a skill or agent (path: test-gap-analysis/references/risk-weighting.md). Skipping contract validation. |
| warning | test-gap-report | discovery | Artifact 'test-gap-report' is not a skill or agent (path: test-gap-analysis/templates/test-gap-report.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | dotnet-testing | discovery | Artifact 'dotnet-testing' is not a skill or agent (path: test-generation/references/dotnet-testing.md). Skipping contract validation. |
| warning | go-testing | discovery | Artifact 'go-testing' is not a skill or agent (path: test-generation/references/go-testing.md). Skipping contract validation. |
| warning | jest-vitest | discovery | Artifact 'jest-vitest' is not a skill or agent (path: test-generation/references/jest-vitest.md). Skipping contract validation. |
| warning | junit-spring | discovery | Artifact 'junit-spring' is not a skill or agent (path: test-generation/references/junit-spring.md). Skipping contract validation. |
| warning | pytest-unittest | discovery | Artifact 'pytest-unittest' is not a skill or agent (path: test-generation/references/pytest-unittest.md). Skipping contract validation. |
| warning | test-generation-report | discovery | Artifact 'test-generation-report' is not a skill or agent (path: test-generation/templates/test-generation-report.md). Skipping contract validation. |
| blocking | SKILL | metadata | Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed |
| warning | SKILL | metadata | Purpose is missing or too short / vague. |
| blocking | SKILL | contract | Inputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is missing or unstructured. |
| blocking | SKILL | contract | Outputs contract is vague (e.g. 'a report', 'analysis', 'summary'). |
| warning | SKILL | contract | Outputs do not declare a structured format hint (json/markdown/yaml/...). |
| warning | validation-report | discovery | Artifact 'validation-report' is not a skill or agent (path: validation-runner/templates/validation-report.md). Skipping contract validation. |
| blocking | adr | dependency | Circular dependency: adr -> architecture-options-analysis -> adr |
| blocking | release-gate-checklist | dependency | Circular dependency: release-gate-checklist -> go-no-go-checklist -> release-gate-checklist |
| blocking | blocker | dependency | Circular dependency: blocker -> task -> blocker |
| blocking | task | dependency | Circular dependency: task -> validation-report -> task |

## Dependency graph
- Nodes: 78
- Missing: 0
- Circular: 4
- Unused: 0

## Responsibility

| Flag | Count |
| --- | --- |
| over-broad | 17 |
| unclear | 82 |

### Over-broad skills (first 5)
- `SKILL` (score=50): Detected 5 distinct actions: audit, create, design, review, route. Skill may be over-broad; consider tightening scope.
- `SKILL` (score=50): Detected 4 distinct actions: audit, recommend, report, review. Skill may be over-broad; consider tightening scope.
- `SKILL` (score=25): Detected 6 distinct actions: design, merge, rank, report, review, sign. Skill is over-broad; consider splitting.
- `code-review-report` (score=50): Detected 4 distinct actions: list, report, review, test. Skill may be over-broad; consider tightening scope.
- `SKILL` (score=50): Detected 5 distinct actions: build, find, rank, report, review. Skill may be over-broad; consider tightening scope.

## Overlap (top 10 pairs)

| Artifact A | Artifact B | Score | Recommendation |
| --- | --- | --- | --- |
| SKILL | SKILL | 60 | keep_separate |
| architecture-review-report | observability-review-report | 45 | keep_separate |
| frontend-implementation-report | integration-implementation-report | 44 | keep_separate |
| react | vue | 43 | keep_separate |
| angular | react | 42 | keep_separate |
| SKILL | SKILL | 41 | keep_separate |
| observability-review-report | slo-review | 39 | keep_separate |
| angular | vue | 38 | keep_separate |
| SKILL | SKILL | 33 | keep_separate |
| SKILL | SKILL | 33 | keep_separate |

## Scorecard
| Name | ROI | Decision | Rationale |
| --- | --- | --- | --- |
| README | 41 | rewrite | Score 41; rewrite triggered by 0 blocking + 2 warnings. |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| decision-quality-checklist | 49 | merge | Score 49; merge candidate (high overlap detected). |
| adr | 39 | rewrite | Score 39; rewrite triggered by 1 blocking + 1 warnings. |
| architecture-options-analysis | 48 | merge | Score 48; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| architecture-risk-checklist | 49 | merge | Score 49; merge candidate (high overlap detected). |
| distributed-systems-checklist | 49 | merge | Score 49; merge candidate (high overlap detected). |
| modular-monolith-checklist | 49 | merge | Score 49; merge candidate (high overlap detected). |
| architecture-review-report | 48 | merge | Score 48; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| dotnet | 49 | merge | Score 49; merge candidate (high overlap detected). |
| go | 50 | rewrite | Score 50; rewrite triggered by 0 blocking + 1 warnings. |
| java-spring | 49 | merge | Score 49; merge candidate (high overlap detected). |
| mixed-monolith | 49 | merge | Score 49; merge candidate (high overlap detected). |
| node-typescript | 49 | merge | Score 49; merge candidate (high overlap detected). |
| python | 50 | rewrite | Score 50; rewrite triggered by 0 blocking + 1 warnings. |
| backend-implementation-report | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| review-severity | 49 | merge | Score 49; merge candidate (high overlap detected). |
| code-review-report | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| migration-risk-checklist | 48 | merge | Score 48; merge candidate (high overlap detected). |
| migration-safety-report | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| dependency-risk-checklist | 49 | merge | Score 49; merge candidate (high overlap detected). |
| dependency-change-report | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| doc-source-of-truth | 48 | merge | Score 48; merge candidate (high overlap detected). |
| README | 41 | rewrite | Score 41; rewrite triggered by 0 blocking + 2 warnings. |
| self | 50 | rewrite | Score 50; rewrite triggered by 0 blocking + 1 warnings. |
| api-doc-update-checklist | 49 | merge | Score 49; merge candidate (high overlap detected). |
| documentation-impact-report | 49 | merge | Score 49; merge candidate (high overlap detected). |
| readme-update-checklist | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| angular | 48 | merge | Score 48; merge candidate (high overlap detected). |
| nextjs | 48 | merge | Score 48; merge candidate (high overlap detected). |
| react | 48 | merge | Score 48; merge candidate (high overlap detected). |
| static-ui | 49 | merge | Score 49; merge candidate (high overlap detected). |
| vue | 49 | merge | Score 49; merge candidate (high overlap detected). |
| frontend-implementation-report | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| handoff-packet | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| handoff-and-forbidden | 49 | merge | Score 49; merge candidate (high overlap detected). |
| stop-and-validation | 50 | rewrite | Score 50; rewrite triggered by 0 blocking + 1 warnings. |
| workflow | 49 | merge | Score 49; merge candidate (high overlap detected). |
| implementation-routing-report | 48 | merge | Score 48; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| incident-severity-guide | 49 | merge | Score 49; merge candidate (high overlap detected). |
| action-item | 49 | merge | Score 49; merge candidate (high overlap detected). |
| incident-triage-report | 48 | merge | Score 48; merge candidate (high overlap detected). |
| timeline | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| async-messaging | 48 | merge | Score 48; merge candidate (high overlap detected). |
| contract-testing | 48 | merge | Score 48; merge candidate (high overlap detected). |
| file-batch | 48 | merge | Score 48; merge candidate (high overlap detected). |
| rest-api | 48 | merge | Score 48; merge candidate (high overlap detected). |
| webhook | 48 | merge | Score 48; merge candidate (high overlap detected). |
| integration-implementation-report | 48 | merge | Score 48; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| logging-metrics-tracing-checklist | 48 | merge | Score 48; merge candidate (high overlap detected). |
| observability-review-report | 48 | merge | Score 48; merge candidate (high overlap detected). |
| slo-review | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| release-gate-checklist | 39 | rewrite | Score 39; rewrite triggered by 1 blocking + 1 warnings. |
| go-no-go-checklist | 49 | merge | Score 49; merge candidate (high overlap detected). |
| release-readiness-report | 48 | merge | Score 48; merge candidate (high overlap detected). |
| release-risk-register | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| repo-discovery-report | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| runbook-quality-checklist | 49 | merge | Score 49; merge candidate (high overlap detected). |
| latency-spike | 50 | rewrite | Score 50; rewrite triggered by 0 blocking + 1 warnings. |
| runbook-authoring-report | 49 | merge | Score 49; merge candidate (high overlap detected). |
| runbook | 49 | merge | Score 49; merge candidate (high overlap detected). |
| troubleshooting-guide | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| authz-review-checklist | 49 | merge | Score 49; merge candidate (high overlap detected). |
| owasp-checklist | 49 | merge | Score 49; merge candidate (high overlap detected). |
| secrets-review-checklist | 49 | merge | Score 49; merge candidate (high overlap detected). |
| security-review-report | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| blocker | 40 | rewrite | Score 40; rewrite triggered by 1 blocking + 1 warnings. |
| decision-log | 50 | rewrite | Score 50; rewrite triggered by 0 blocking + 1 warnings. |
| state | 50 | rewrite | Score 50; rewrite triggered by 0 blocking + 1 warnings. |
| task | 45 | rewrite | Score 45; rewrite triggered by 1 blocking + 1 warnings. |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| risk-weighting | 49 | merge | Score 49; merge candidate (high overlap detected). |
| test-gap-report | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| dotnet-testing | 49 | merge | Score 49; merge candidate (high overlap detected). |
| go-testing | 49 | merge | Score 49; merge candidate (high overlap detected). |
| jest-vitest | 49 | merge | Score 49; merge candidate (high overlap detected). |
| junit-spring | 49 | merge | Score 49; merge candidate (high overlap detected). |
| pytest-unittest | 49 | merge | Score 49; merge candidate (high overlap detected). |
| test-generation-report | 49 | merge | Score 49; merge candidate (high overlap detected). |
| SKILL | 34 | rewrite | Score 34; rewrite triggered by 84 blocking + 42 warnings. |
| validation-report | 50 | rewrite | Score 50; rewrite triggered by 0 blocking + 1 warnings. |
