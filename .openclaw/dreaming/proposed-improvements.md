# Proposed Improvements

Cycle: 2026-06-29 cycle-5

PI-001 through PI-007 are carried from cycle 1 (some with updates); PI-008 is now **APPLIED**; PI-009 and PI-010 are NEW.

Safety classifications: `auto_safe | review_required | blocked`

Status values: `proposed | applied | deferred | rejected`

---

## PI-001 — Add "permissive-state" pre-check to SGP CI (carried, scope reframed)

- **Improvement ID:** PI-001
- **Evidence reference:** EV-001, EV-007, L-001 (reframed)
- **Cycle-2 update:** EV-007 shows L-001's pattern applied **multiple times** across the SGP arc. The PI's scope is now "assert that any permissive-state-test is preceded by, or co-committed with, a strict-flip commit" — a sharper invariant.
- **Safety classification:** auto_safe
- **Status:** proposed (unchanged)

---

## PI-002 — Add state-machine transition-table requirement to validator (carried)

- **Evidence reference:** EV-002, L-003
- **Status:** proposed (unchanged)
- **Safety classification:** review_required (unchanged)

---

## PI-003 — Add `re.DOTALL` denylist to skill validator CI (carried)

- **Evidence reference:** EV-002, L-004
- **Status:** proposed (unchanged)
- **Safety classification:** auto_safe (unchanged)

---

## PI-004 — Require sub-agent code review before slice ship (carried)

- **Evidence reference:** EV-003, L-005
- **Status:** proposed (unchanged)
- **Safety classification:** review_required (unchanged)

---

## PI-005 — Promote `code-review-slice-N` sub-agent pattern to a registered skill (carried)

- **Evidence reference:** EV-003, P-S-001
- **Status:** proposed (unchanged)
- **Safety classification:** review_required (unchanged)

---

## PI-006 — Add structured OpenClaw run log (carried; **still unfilled in cycle 2**)

- **Improvement ID:** PI-006
- **Evidence reference:** EV-004, L-007, P-IP-001
- **Cycle-2 status:** unchanged. No JSONL run log was added between cycles. `find` still returns nothing. This remains the single largest unfilled deterministic opportunity.
- **Status:** proposed (carried; explicitly not applied)
- **Safety classification:** review_required (unchanged)
- **Validation required:** feed fixture log to parser; assert parsed evidence matches expectations.

---

## PI-007 — Add regression test for cron tick path (carried)

- **Evidence reference:** EV-005, L-008, RS-009
- **Status:** proposed (unchanged)
- **Safety classification:** auto_safe (unchanged)

---

## PI-008 — Run local validation via Makefile target before push (APPLIED in cycle 2)

- **Improvement ID:** PI-008
- **Evidence reference:** EV-006 (cycle-1 fix-up root cause), EV-008 (first-use validation)
- **Applied in cycle 2:** Yes — `Makefile` added at repo root with `dreaming-validate`, `dreaming-pr-ready`, `dreaming-clean`, `dreaming-help`, and `dreaming-resolve-base` targets. First use caught 2 real issues (L-010, L-013) before push.
- **Status:** **APPLIED** (was proposed in cycle 1)
- **Safety classification:** auto_safe (applied; classification was correct)
- **Validation performed:** `make dreaming-validate` returns 104 passed, 1 skipped on the cycle-2 branch ahead of any commits.
- **Rollback notes:** `git revert` the Makefile commit if developer ergonomics prove worse than the saved fix-up cycles.

---

## PI-009 — Generalize PI-008 to other workflow artifact sets (NEW)

- **Improvement ID:** PI-009
- **Evidence reference:** EV-008, L-009
- **Observed problem:** PI-008 solved dreaming's local-validation gap. SGP, BusinessOperationsDashboard, and any other workflow with a CI workflow file are likely to have the same gap, but no equivalent local target exists for them.
- **Affected workflow / skill / artifact:** all workflows with `.github/workflows/*.yml` files
- **Recommended change:** For each existing CI workflow, create a sibling `make <name>-validate` target. Existing precedent: `make dreaming-validate` (PI-008).
- **Expected benefit:** Prevent the cycle-1 fix-up pattern (5 fix-up commits after push) from recurring in other workflows.
- **Risk level:** low
- **Safety classification:** review_required (touches developer workflow conventions)
- **Validation required:** Apply to SGP first; verify `make sgp-validate` catches a known CI-only failure locally before promoting the convention.
- **Status:** proposed

---

## PI-010 — Treat each EV entry as a candidate for arc expansion (NEW, informational)

- **Improvement ID:** PI-010
- **Evidence reference:** EV-007 (the SGP arc-expansion), nightly-summary.md's "Cycle-2 self-meta observation"
- **Observed problem:** Cycle 1's EV-001 was a single timestamp that understated the SGP work by ~15x (16 PRs collapsed into one moment). This is a class of error: **single-event evidence naturally hides arc-scale patterns**.
- **Recommended change:** When writing a new EV-### entry, ask: "Is this a single event or the visible tip of an arc?" If the latter, expand to the arc before publishing.
- **Safety classification:** informational (process guidance, not code)
- **Validation required:** Spot-audit existing EV entries; expand those that prove to be arc-tips on first review.
- **Status:** proposed (informational)

---

## Summary of cycle-2 PI status

| PI | Class | Status |
| --- | --- | --- |
| PI-001 | auto_safe | proposed (reframed) |
| PI-002 | review_required | proposed |
| PI-003 | auto_safe | proposed |
| PI-004 | review_required | proposed |
| PI-005 | review_required | proposed |
| PI-006 | review_required | **partial** (cycle 5; downstream applied, runtime split into PI-006a) |
| PI-006a | review_required | proposed (cycle 6, NEW; out-of-repo) |
| PI-007 | auto_safe | proposed |
| **PI-008** | **auto_safe** | **APPLIED** ✅ |
| PI-009 | review_required | proposed (NEW) |
| PI-010 | informational | proposed (NEW) |
| PI-013 | review_required | APPLIED (cycle 5, NEW) |

No blocked-class changes proposed in cycle 2.

---

## PI-011 — Add `on: pull_request:` filter to surface PR-only failures cleanly (NEW, cycle 3)

- **Improvement ID:** PI-011
- **Evidence reference:** EV-010, L-014
- **Observed problem:** Even after removing `main` from the `push:` trigger, a developer can `git push origin main` directly. The dreaming test suite would still fail. The current `tests/` skip-when-precondition-not-held logic is necessary but not sufficient — the workflow trigger itself must reflect the test's domain.
- **Recommended change:** Document (in `workflow-nightly-dreaming.md`) the CI trigger model: "this suite is a PR-readiness suite; PR events are the primary trigger; `push:` is allowed only for early-warning on the feature branch before the PR opens."
- **Expected benefit:** Future cycle maintainers don't repeat the cycle-3 trigger-bundling bug.
- **Safety classification:** auto_safe (documentation-only)
- **Validation required:** N/A (doc-only); apply in cycle 4 or later.
- **Status:** proposed

---

## Summary of cycle-3 PI status

| PI | Class | Status |
| --- | --- | --- |
| PI-001 | auto_safe | proposed (reframed) |
| PI-002 | review_required | proposed |
| PI-003 | auto_safe | proposed |
| PI-004 | review_required | proposed |
| PI-005 | review_required | proposed |
| PI-006 | review_required | **partial** (cycle 5; downstream applied, runtime split into PI-006a) |
| PI-006a | review_required | proposed (cycle 6, NEW; out-of-repo) |
| PI-007 | auto_safe | proposed |
| PI-008 | auto_safe | APPLIED (cycle 2) |
| PI-009 | review_required | proposed (cycle 2) |
| PI-010 | informational | proposed (cycle 2) |
| PI-011 | auto_safe | APPLIED (cycle 4) |
| PI-012 | auto_safe | APPLIED (cycle 4, NEW) |
| PI-013 | review_required | APPLIED (cycle 5, NEW) |

No blocked-class changes proposed in cycle 3, cycle 4, or cycle 5.

---

## PI-006a — OpenClaw runtime emits JSONL run logs (NEW, cycle 6; split out of PI-006 per L-016)

- **Improvement ID:** PI-006a
- **Evidence reference:** EV-014, EV-015, L-016, RS-016, P-IP-004, `.openclaw/dreaming/openclaw-run-log-spec.md`, `.openclaw/dreaming/openclaw-run-log-emitter-handoff.md`
- **Observed problem:** PI-006 was carried from cycle 1 as a single sentence. Cycle 5 surfaced that PI-006 actually bundles two units across two repos: (a) the OpenClaw runtime emits JSONL logs, (b) downstream tooling parses them. (b) was applied in cycle 5 (PR #63, status `partial`). (a) was declared out-of-scope for `aiWorkflows` and is the work this PI describes.
- **Affected package:** `openclaw/openclaw` runtime (NOT `aiWorkflows`).
- **Recommended change:** Implement the JSONL run-log emitter in the OpenClaw runtime, against the spec shipped in cycle 5. A complete, self-contained handoff is at `.openclaw/dreaming/openclaw-run-log-emitter-handoff.md` (cycle 6) — the implementer does not need to read this repo beyond that document and the spec.
- **Expected benefit:** Closes PI-006's open half. RS-008 (the OpenClaw run log evidence minimum, currently `warning`) flips to `passing` the moment a runtime-emitted file lands in the dreaming fixture path. The dream-workflow's per-tool-call retry/timeout/blocker findings become available for the first time.
- **Risk level:** medium (touches a different repo; the contract is locked in this repo, the implementer just has to honor it)
- **Safety classification:** review_required (touches a runtime path; the anti-CoT invariant on `args_summary` is a hard rule, not a guideline)
- **Validation required:** Per the handoff's "Validation" section — 7 steps; step 7 is the dream-workflow's `make dreaming-validate` on a runtime-emitted fixture.
- **Status:** proposed (NEW; out-of-repo; cannot be applied from `aiWorkflows`)

---

## Summary of cycle-6 PI status

| PI | Class | Status |
| --- | --- | --- |
| PI-001 | auto_safe | proposed (reframed) |
| PI-002 | review_required | proposed |
| PI-003 | auto_safe | proposed |
| PI-004 | review_required | proposed |
| PI-005 | review_required | proposed |
| PI-006 | review_required | **partial** (cycle 5; downstream applied, runtime split into PI-006a) |
| PI-006a | review_required | proposed (cycle 6, NEW; out-of-repo) |
| PI-007 | auto_safe | proposed |
| PI-008 | auto_safe | APPLIED (cycle 2) |
| PI-009 | review_required | proposed (cycle 2; held per "A then B") |
| PI-010 | informational | proposed (cycle 2) |
| PI-011 | auto_safe | APPLIED (cycle 4) |
| PI-012 | auto_safe | APPLIED (cycle 4) |
| PI-013 | review_required | APPLIED (cycle 5) |
| PI-014 | auto_safe | proposed (cycle 7, NEW) |

No blocked-class changes proposed in cycle 6 or cycle 7. The cycle-6 PR was a hygiene pass plus a spec-grounded handoff for PI-006a; cycle 7 files PI-014 (cyber-signal feed pipeline), adds RS-017, and back-fills EV-016. No code changes to the parser, spec, or test suite.



---

## PI-014 — Restore the cyber-signal-daily feed pipeline (NEW, cycle 7)

- **Improvement ID:** PI-014
- **Evidence reference:** EV-016, RS-017, cron `cyber-signal-daily` runs history
- **Observed problem:** The `cyber-signal-daily` cron has been pointing at `/data/.openclaw/workspace/scripts/cyber-signal-fetch-feeds.sh` for at least 19 days. That path does not exist — `scripts/` is not even a directory on this gateway (`stat` returns ENOENT). The pre-fetched JSON at `/tmp/cyber-signal-feeds.json` was last touched 2026-06-11 13:33 GMT+2 and has been getting more stale every day. The cron still fires and the brief still gets delivered to Telegram, but it's a retrospective snapshot of stale items, not a daily brief. The agent runs are repeatedly noting "feeds are N days stale" in their summaries (see EV-016). A second, distinct issue is interleaved: every cron run fails its first attempt with `FailoverError: The AI service is temporarily overloaded`, then succeeds on retry (auto-retry-on-overload is doing its job; this is the lesser of the two issues).
- **Affected package:** the gateway's `/data/.openclaw/workspace/scripts/` directory (does not exist) and the `cyber-signal-daily` cron job. NOT a `aiWorkflows`-side concern.
- **Recommended change:** Create `/data/.openclaw/workspace/scripts/cyber-signal-fetch-feeds.sh` (or a Python equivalent) that pulls from a curated list of OSINT threat feeds (The Hacker News, BleepingComputer, IndustrialCyber, CISA, etc.), deduplicates, and writes fresh JSON to `/tmp/cyber-signal-feeds.json` before each cron fires. Either run it as a separate cron entry scheduled for `25 6 * * *` (5 minutes before the analyst cron at `30 6 * * *`) or have the analyst cron call it as step 1. The shape of the fetch script is implementation-defined; the contract (fresh JSON in `/tmp/cyber-signal-feeds.json` with `.items[]` and `.fetch_errors`) is already encoded in the cron prompt.
- **Expected benefit:** Daily briefs become actual daily briefs. RS-017 (the cron deliverable freshness gate, NEW) flips from `failing` to `passing` the moment a fetch script lands and one cron cycle completes with fresh data. The AI-overload retries can be addressed separately (see "Adjacent observation" below).
- **Risk level:** low (script creation; no runtime path touches production data; the cron already handles "no fresh data" gracefully)
- **Safety classification:** auto_safe (script + cron config; no production-side changes; no schema changes; no skill/workflow changes)
- **Validation required:** Manual: (a) `scripts/cyber-signal-fetch-feeds.sh` exists and is executable; (b) it can be run standalone and produces `/tmp/cyber-signal-feeds.json` with at least one fresh item from each configured source; (c) the next cron cycle produces a brief that contains at least one item with `pubDate` within 48 hours of the cron fire time. RS-017 encodes (c) as a regression check.
- **Status:** proposed (NEW)
- **Adjacent observation (not part of this PI):** the AI-overload retry pattern (first attempt fails, retry succeeds) is the existing behavior. It's not a bug per se — the auto-retry is doing its job. But it means each cron run doubles the model-call cost and adds ~100s of latency. Worth tracking as a follow-up PI if the pattern persists past 2026-07-15.

---

## Summary of cycle-7 PI status

| PI | Class | Status |
| --- | --- | --- |
| PI-001 | auto_safe | proposed (reframed) |
| PI-002 | review_required | proposed |
| PI-003 | auto_safe | proposed |
| PI-004 | review_required | proposed |
| PI-005 | review_required | proposed |
| PI-006 | review_required | **partial** (cycle 5; downstream applied, runtime split into PI-006a) |
| PI-006a | review_required | proposed (cycle 6, NEW; out-of-repo) |
| PI-007 | auto_safe | proposed |
| PI-008 | auto_safe | APPLIED (cycle 2) |
| PI-009 | review_required | proposed (cycle 2; held per "A then B") |
| PI-010 | informational | proposed (cycle 2) |
| PI-011 | auto_safe | APPLIED (cycle 4) |
| PI-012 | auto_safe | APPLIED (cycle 4) |
| PI-013 | review_required | APPLIED (cycle 5) |
| PI-014 | auto_safe | proposed (cycle 7, NEW) |

No blocked-class changes proposed in cycle 7. The cycle-7 PR files PI-014 (cyber-signal feed pipeline is broken), adds RS-017 (a regression scenario pinning the freshness expectation), and back-fills EV-016 (the evidence entry documenting the broken pipeline). No code changes to the parser, spec, or test suite; no behavior changes; no production-runtime changes.


---

## PI-015 — Add Stage -2 Surface-Scope Pre-Declaration to workflow-nightly-dreaming.md (NEW, cycle 8; applied-this-cycle)

- **Improvement ID:** PI-015
- **Evidence reference:** EV-017, RS-018, cycles 5/6/7 self-meta observations
- **Observed problem:** Cycles 5, 6, and 7 each shipped a self-meta observation justifying scope decisions that were not surfaced until close-out. Cycle 5's "biggest since cycle 1"; cycle 6's "substantive-by-handoff"; cycle 7's "first cycle with out-of-scope work." None of these was required by the workflow doc; all were post-hoc. The honest constraint "I cannot do that from this repo" (cycle 6) and "fix is on the same gateway but outside the workflow's surface area" (cycle 7) should be structural artifacts, not self-meta justifications.
- **Affected package:** `.openclaw/dreaming/workflow-nightly-dreaming.md` (procedure doc); `.openclaw/dreaming/nightly-summary.md` (Trigger section schema); `tests/dreaming/test_pr_readiness.py` (new test).
- **Recommended change:** Add Stage -2 to the workflow doc, requiring the cycle author's Trigger section to pre-declare four fields: Workflow target, Surface area, Dreaming-ledger scope, Cycle-size budget. Add a corresponding test that asserts the most recent cycle's Trigger section contains all four field labels. Past cycles' Trigger sections are preserved as historical record (the test is forward-looking).
- **Expected benefit:** Scope decisions are surfaced at human time (when the cycle is being planned) rather than at audit time (when the cycle is being closed). Cycles that turn out to be cross-repo or non-dreaming-ledger are pre-registered, so the cross-repo-handoff-index and the non-dreaming rationale are not afterthoughts.
- **Risk level:** low (procedural change; no code; no schema migration; past cycles unaffected)
- **Safety classification:** auto_safe (workflow-doc change; test addition; no production-runtime change; no skill change; no validation-gate change)
- **Validation required:** `make dreaming-validate` returns 0 failures on the cycle-8 branch (the new test passes because cycle 8's Trigger is written in the new format). RS-018 captures the regression scenario. Cycle 8 dogfoods the new format.
- **Status:** APPLIED (cycle 8, NEW) — single-cycle PI; the change ships in this cycle's PR.

---

## Summary of cycle-8 PI status

| PI | Class | Status |
| --- | --- | --- |
| PI-001 | auto_safe | proposed (reframed) |
| PI-002 | review_required | proposed |
| PI-003 | auto_safe | proposed |
| PI-004 | review_required | proposed |
| PI-005 | review_required | proposed |
| PI-006 | review_required | **partial** (cycle 5; downstream applied, runtime split into PI-006a) |
| PI-006a | review_required | proposed (cycle 6, NEW; out-of-repo) |
| PI-007 | auto_safe | proposed |
| PI-008 | auto_safe | APPLIED (cycle 2) |
| PI-009 | review_required | proposed (cycle 2; held per "A then B") |
| PI-010 | informational | proposed (cycle 2) |
| PI-011 | auto_safe | APPLIED (cycle 4) |
| PI-012 | auto_safe | APPLIED (cycle 4) |
| PI-013 | review_required | APPLIED (cycle 5) |
| PI-014 | auto_safe | proposed (cycle 7, NEW) |
| PI-015 | auto_safe | APPLIED (cycle 8, NEW) |

No blocked-class changes proposed in cycle 8. The cycle-8 PR adds Stage -2 to the workflow doc, a new test enforcing it, RS-018, and EV-017. The single substantive change is the Stage -2 schema; everything else is artifact tracking. No code changes to the parser, spec, or test suite beyond the new test.
