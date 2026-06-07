# Stage 5 — Repeat-Run Drift Analysis (template)

The agent writes a markdown report to `artifacts/api_change_log.md`. This
template is the raw evidence the agent should consult.

## Was this a baseline run?

(yes | no — previous baseline was YYYY-MM-DD)

## Inputs found

- `artifacts/history/previous_api_inventory.json`: present | absent
- `artifacts/history/previous_openapi.normalized.yaml`: present | absent
- `artifacts/history/previous_api_test_results.json`: present | absent

## Detected drift (one row per change)

| Type | Endpoint / Area | Before | After | Impact | Action taken |
| --- | --- | --- | --- | --- | --- |

## Drift types reference

```text
new_endpoint
removed_endpoint
method_changed
schema_changed
auth_changed
status_code_changed
error_shape_changed
behavior_changed
performance_changed
security_changed
unknown
```

## Baseline promotion

At the end of the run, copy current inventory / contract / results into
`artifacts/history/` as the new baseline (only if safe — do not overwrite a
known-good baseline with a known-bad one).
