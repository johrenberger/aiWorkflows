# Stage 9 — Security Baseline Findings (template)

The agent writes findings to `artifacts/api_security_findings.md`. Use this
template to record raw observations before the per-finding format is
finalized.

## Checks performed

- [ ] missing authentication on protected endpoints
- [ ] broken object-level authorization risk
- [ ] broken function-level authorization risk
- [ ] excessive data exposure
- [ ] sensitive data in responses
- [ ] stack trace leakage
- [ ] verbose error messages
- [ ] unsafe HTTP methods
- [ ] insecure CORS behavior
- [ ] missing or weak rate limiting (observable)
- [ ] injection-prone query/body parameters
- [ ] mass assignment risk
- [ ] file upload validation risk
- [ ] token leakage in logs / code / tests
- [ ] hardcoded secrets
- [ ] weak auth/session handling
- [ ] debug endpoints exposed

## Safety rules observed

- [ ] no destructive attacks
- [ ] no aggressive fuzzing against production
- [ ] no credential stuffing / brute force
- [ ] no exploit chaining / data exfiltration

## Findings (one row per finding — full record in the artifact)

| ID | Title | Endpoint | Severity | Confidence |
| --- | --- | --- | --- | --- |

## Affected files (if repo available)

_List of paths, grouped by finding._
