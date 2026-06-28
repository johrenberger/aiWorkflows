# Inefficiency Patterns

Each pattern has a single evidence reference.

---

## P-IP-001 — Dreaming Stage 1 ran without structured run logs

- **Pattern ID:** P-IP-001
- **Evidence reference:** EV-004
- **Affected workflow / skill:** dreaming workflow itself
- **Observed inefficiency:** First cycle produced useful but coarse-grained findings because it could only use Git history and `memory/*.md` notes. Per-tool-call retries, timeouts, blocked states, and selected skills at the run level were not directly observable.
- **Was the output still successful:** Yes — the artifacts are useful and evidence-backed; patterns surfaced are real.
- **Cause:** No structured OpenClaw run log existed in the workspace. The dreaming spec assumes raw OpenClaw logs as Stage-1 input.
- **Recommended improvement:** Add a structured OpenClaw run log that records (at minimum) start, completion, selected skills, tool errors, retries, and outcome for each turn. Subsequent dreaming cycles should consume this log.
- **Deterministic tooling opportunity:** yes — the log format should be JSONL with a fixed schema; dreaming Stage 1 should parse it deterministically rather than grepping `memory/`.
- **Regression scenario link:** RS-008

---

## P-IP-002 — Slice N ships before slice N review, requiring slice N.1

- **Pattern ID:** P-IP-002
- **Evidence reference:** EV-003 (slice 3 → slice 3.1 → slice 4.1)
- **Affected workflow / skill:** `code-review-slice-N` sub-agent workflow (emergent)
- **Observed inefficiency:** Slice 3 shipped and was reviewed post-hoc, requiring a `slice 3.1` follow-up commit. Slice 4 followed the same pattern (`slice 4.1`). The cost is small (one extra commit, one extra review cycle) but real.
- **Was the output still successful:** Yes — slice 3.1 caught 2 CRITICAL + 4 HIGH + 5 MEDIUM + 3 LOW findings.
- **Cause:** The review-before-ship step is not yet enforced as part of the slice workflow; it happens when the main session decides to spawn a reviewer.
- **Recommended improvement:** Standardize the spawn-reviewer step as part of the slice workflow itself (see PI-005). Make "slice N ships only after sub-agent review" a routing rule.
- **Deterministic tooling opportunity:** not directly; the workflow is sub-agent-based. The improvement is workflow-level, not tool-level.
- **Regression scenario link:** RS-005 (the slice 3 CRITICAL itself), RS-007 (the slice 4 idempotency scenario)
