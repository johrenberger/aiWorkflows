# Stage 14 — Failure Triage Evidence (template)

The agent writes the full defect report to `artifacts/api_defect_report.md`.
Use this template to classify each failure.

## Failure classes

```text
application_defect
test_defect
contract_drift
missing_test_data
environment_issue
auth_configuration_issue
dependency_issue
flaky_behavior
unsafe_to_execute
unknown
```

## Per-failure record (one block per confirmed defect)

```text
ID:
Endpoint:
Method/path:
Request payload (sanitized):
Response status:
Response body (sanitized):
Expected result:
Actual result:
Source evidence:
Severity:
Confidence:
Recommended fix:
Affected files (if known):
Failure class:
```

## Flaky behavior log

| Test | Run 1 | Run 2 | Run 3 | Verdict |
| --- | --- | --- | --- | --- |

## Open questions

_Anything the next run should revisit._
