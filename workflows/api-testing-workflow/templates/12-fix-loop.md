# Stage 15 — Fix Loop Evidence (template)

The agent records fix-loop decisions here. The runner handles commits
unless `commit_changes: true` was set explicitly.

## Was patching enabled?

(yes | no)

## Patches applied

| File | Reason | Test added/updated | Re-run result |
| --- | --- | --- | --- |

## Recommended patches (unified diffs) — when patching disabled

_Group by file, attach the diff inline or as a sibling `*.patch` file._

## Commit policy

- `commit_changes: false` (default) — the runner commits on its own
  after the validation gate passes.
- `commit_changes: true` — the agent should follow these prefixes:
  - `test(api): add API contract and validation tests`
  - `fix(api): correct <specific endpoint behavior>`
  - `docs(api): add API testing workflow artifacts`

## Notes

_Anything affecting re-runs._
