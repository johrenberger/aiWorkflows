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


---

## PI-016 — Cycle closeout memos must quote validator output with explicit branch context (NEW, cycle 9)

- **Improvement ID:** PI-016
- **Evidence reference:** EV-018, cycle-7 closeout memo (`memory/2026-07-01-cycle-7-final.md`) and cycle-8 closeout memo (`memory/2026-07-01-cycle-8-final.md`), both of which quoted `make dreaming-validate` output without distinguishing branch-local from `main` post-merge counts
- **Observed problem:** Two consecutive closeout memos (cycles 7 and 8) mislabeled `make dreaming-validate` output:

  - **Cycle 7's closeout memo** said: "make dreaming-validate on main post-cycle-7-merge: **123 passed, 0 failed, 0 skipped**." The actual count on `main` (post-cycle-7-merge, `b42cdca`) was 121 passed + 1 skipped + 1 expected-fail-on-main (`test_current_branch_uses_dreaming_prefix`, fails on `main` by design).
  - **Cycle 8's closeout memo** said: "make dreaming-validate = **124 passed, 0 failed, 0 skipped**." That count was correct **on the cycle-8 branch**, but the memo did not distinguish branch-local from `main` post-merge counts. The merge closeout (`memory/2026-07-01-cycle-8-closeout.md`) corrected the post-merge count to 122 passed + 1 skipped + 1 expected-fail-on-main.

  Both memos quoted the validator's headline number without explicit branch context. The pattern is two-cycle-stale and recurring — it's a procedural-error pattern, not a one-off typo.

- **Affected package:** the cycle-closeout-memo convention itself (the prose discipline that produces `memory/YYYY-MM-DD-cycle-N-final.md`). No code change; no test change; no workflow-doc stage change.
- **Recommended change:** Adopt a convention: every cycle closeout memo quotes `make dreaming-validate` output **twice when applicable**, with explicit branch context:

  1. **Branch-local count** — the validator output on the cycle branch (e.g., "124 passed on `dreaming/...cycle-8`"). This is the right number for a cycle closeout memo because it describes the cycle's own validation discipline.
  2. **`main` post-merge count** — the validator output on `main` after the merge lands (e.g., "122 passed + 1 skipped + 1 expected-fail-on-main on `main` post-cycle-8-merge"). This is the right number for a merge closeout, and must be quoted if the closeout memo also claims the post-merge state.

  When a closeout memo is a cycle closeout (PR open, awaiting merge), only the branch-local count is required. When a closeout memo is a merge closeout (PR merged), both counts are required if the memo discusses the post-merge state.

- **Expected benefit:** Eliminates the recurring bookkeeping-error pattern. Future closeout memos don't need correction entries. The validation discipline is preserved and accurately reported.
- **Risk level:** low (procedural change to memo-writing discipline; no code change; no schema change)
- **Safety classification:** auto_safe (procedural convention; no production-runtime change; no skill change; no validation-gate change)
- **Validation required:** None at the test level. Validation is human-discipline: future cycle closeout memos quote both counts (when applicable) with explicit branch context.
- **Status:** proposed (NEW) — convention adopted for cycle 9 onward. Cycle 9's closeout memo (this cycle) is the first one written under the new convention.
- **Adjacent observation (not part of this PI):** The cycle-8 closeout memo I wrote earlier (`memory/2026-07-01-cycle-8-final.md`) is the source of the cycle-8-side error. The merge closeout (`memory/2026-07-01-cycle-8-closeout.md`) corrected it. PI-016 prevents the next cycle from repeating the same error, but it does not retroactively fix cycle 7's or cycle 8's closeout memos. Those corrections stand as historical record.

---

## Summary of cycle-9 PI status

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
| PI-016 | auto_safe | proposed (cycle 9, NEW) |

No blocked-class changes proposed in cycle 9. Cycle 9 ships PI-016 only — a procedural convention for cycle closeout memos. No code changes. No parser changes. No spec changes. No test-suite changes. No workflow-doc stage changes.


---

## PI-017 — Add Stage -3 Post-amend verify to workflow-nightly-dreaming.md (NEW, cycle 10; applied-this-cycle)

- **Improvement ID:** PI-017
- **Evidence reference:** EV-019, cycle-8 merge closeout memo and cycle-9 merge closeout memo, both of which disclosed a post-amend working-tree-rescue pattern
- **Observed problem:** Cycles 8 and 9 closeouts both hit the same working-tree state-rescue pattern. After a `git commit --amend`, the local working tree has a stale line (the pre-amend hash or content) that doesn't match HEAD. The next `git checkout main` (or any branch switch) fails silently with "Please commit your changes or stash them before you switch branches." The cycle author has to manually `git checkout -- <file>` to discard the stale working-tree state, then retry the checkout.
  - **Cycle 8's closeout memo** (`memory/2026-07-01-cycle-8-closeout.md`) disclosed this as "a real workflow-disclosure, not a process failure" and proposed a Stage -3 ("post-amend verify") as a candidate.
  - **Cycle 9's closeout memo** (`memory/2026-07-01-cycle-9-closeout.md`) flagged the pattern as "two-cycle-stale, not a one-off" and recommended cycle 10 consider Stage -3.
- **Affected package:** `.openclaw/dreaming/workflow-nightly-dreaming.md` (procedure doc, Stage -3 added before Stage -2); `tests/dreaming/test_pr_readiness.py` (new test enforcing the discipline).
- **Recommended change:** Add Stage -3 to the workflow doc, requiring the cycle author to verify the working tree is clean (no modified tracked files in `.openclaw/dreaming/`) before the next checkout, especially after `git commit --amend`. Add a corresponding test that reads `git status --short -- .openclaw/dreaming/` and asserts no drift lines (excluding untracked files).
- **Expected benefit:** Future cycles don't reproduce the working-tree-rescue pattern. The Stage -3 check is fast (`git status` is sub-second) and runs as part of the existing `make dreaming-validate` flow.
- **Risk level:** low (procedural change; no code change; no schema migration; no production-runtime change)
- **Safety classification:** auto_safe (workflow-doc change; test addition; no production-runtime change; no skill change; no validation-gate change beyond the new test)
- **Validation required:** `make dreaming-validate` returns 0 failures on the cycle-10 branch (the new test passes because the cycle-10 commit is in sync with the working tree at commit time). RS-019 captures the regression scenario. Cycle 10 dogfoods the new stage.
- **Status:** APPLIED (cycle 10, NEW) — single-cycle PI; the change ships in this cycle's PR.

---

## PI-018 — Strengthen PI-016 forecast-discipline with post-merge verification (NEW, cycle 11)

- **Improvement ID:** PI-018
- **Evidence reference:** EV-020, RS-020, cycle-10 merge closeout memo (`memory/2026-07-01-cycle-10-closeout.md`).
- **Observed problem:** PI-016 (cycle 9) established the convention of forecasting "main post-merge" validator counts in cycle closeout memos. Cycle 10's merge closeout initially reported that PI-016's forecast-discipline had never actually worked for any of cycles 6-10. **Cycle 11's PI-018 retroactive correction re-measured each prior cycle's actual count properly (by `git checkout <sha>` to clean working tree before running `make dreaming-validate`) and found the situation is more nuanced:** PI-016's forecast-discipline had partial failures. Specifically:
  - cycle 6 (`c21b712`) closeout claimed `123 passed + 0 failed + 0 skipped`; actual is **121 passed + 1 skipped + 1 expected-fail-on-main** (off by 2 in passed-count direction; also missed the 1 skipped + 1 expected-fail).
  - cycle 7 (`b42cdca`) closeout claimed `121 passed + 1 failed + 1 skipped`; actual is **121 passed + 1 skipped + 1 expected-fail-on-main** (matched).
  - cycle 8 (`ec087fe`) closeout claimed `122 passed + 1 skipped + 1 expected-fail-on-main`; actual is **122 passed + 1 skipped + 1 expected-fail-on-main** (matched).
  - cycle 9 (`d1cbc08`) closeout claimed `122 passed + 1 skipped + 1 expected-fail-on-main` and stated "matched"; actual is **122 passed + 1 skipped + 1 expected-fail-on-main** (matched; cycle 10's closeout wrongly claimed cycle 9 was off by 3; cycle 11 corrected the misreport).
  - cycle 10 (`a91abff`) closeout forecast `125 + 1 + 1`; actual is **126 passed + 1 skipped + 1 expected-fail-on-main** (off by 1 in passed-count direction).
- **Affected package:** `.openclaw/dreaming/workflow-nightly-dreaming.md` (PI-016 amendment, adding a verification step to the forecast procedure); cycles 6-10 closeout memos in `memory/` (retroactive correction of the actual measured counts).
- **Recommended change:** PI-016 needs a discipline-strengthening amendment. Specifically: the forecast step is currently "compute the new test count and write it down." It should become "compute the new test count, write it down, and **after the merge lands, run `make dreaming-validate` on the actual post-merge `main` and verify the forecast matched.**" If the forecast did not match, the closeout memo must be corrected with the actual measured count and a forecast-accuracy section explaining the delta. Optionally, add a test that asserts closeout memos quote the post-merge count correctly (a meta-test on `memory/` files). Cycle 11 should also retroactively correct cycles 6-10's closeout memos with the actual measured counts (see cross-cycle table in this PI).
- **Expected benefit:** PI-016 becomes a real verification method, not just a documentation discipline. The forecast-accuracy delta is recorded honestly. Future cycles can quote PI-016 numbers with confidence.
- **Risk level:** low (doc amendment + retroactive memo correction; no code change; no schema migration; no production-runtime change)
- **Safety classification:** auto_safe (workflow-doc amendment; retroactive memo edits; no production-runtime change)
- **Validation required:** cycle 11's PI-018 application must (a) amend PI-016's section in the workflow doc with the verification step, (b) retroactively correct cycles 6-10's closeout memos with the actual measured counts, (c) add a test enforcing the forecast-presence discipline in `pr-change-log.md` (the test `test_pr_change_log_forecasts_main_post_merge_count` is the cycle-11 NEW test that fires during cycle authoring if the cycle's row in `pr-change-log.md` doesn't yet contain the forecast; it does NOT verify the forecast was correct, which remains a manual discipline per Stage 11), (d) PI-018 itself is verifiable by running `make dreaming-validate` on cycle 11's post-merge `main` and confirming the forecast matched.
- **Status:** APPLIED (cycle 11, NEW)
- **Cycle:** 11

---

## PI-019 — Adopt code-reviewer sub-agent as a workflow stage (NEW, cycle 11)

- **Improvement ID:** PI-019
- **Evidence reference:** EV-021, RS-021, Telegram msgs #11647 (workflow adopted), #11644 (per-round-summary directive), #11770 (5-round budget chosen arbitrarily), #11772 (rounds 4 and 5 locked as fixed purposes). Cycle-10 reviewer log: `.openclaw/dreaming/cycle-10-review-log.md`. Cycle-11 reviewer log: `.openclaw/dreaming/cycle-11-review-log.md`.
- **Observed problem:** Cycles 1-9 did not use a code-reviewer sub-agent; the cycle author reviewed their own work. Cycles 10 and 11 each spawned a code-reviewer sub-agent for 5 rounds (per msg #11647, adopted after cycle 10's reviewer run). Cycle 10's reviewer caught 4 latent issues across 5 rounds (the most important: Stage -3 schema alignment — a Stage schema was introduced that fired on the wrong git status line shape). Cycle 11's reviewer caught 6 latent issues across 5 rounds + a second-pass catch (the most important: forecast-line test regex matched text but not numeric count — would pass on `TBD` / `to be determined` placeholder inputs, exactly the discipline failure PI-018 was supposed to prevent). The catch rate demonstrates that a clean-context second pair of eyes catches real issues; the cycle author reviewing their own work cannot reproduce this distance.
- **Affected package:** `.openclaw/dreaming/workflow-nightly-dreaming.md` (Stage 12 added).
- **Recommended change:** Add Stage 12 to the workflow doc, documenting the code-reviewer sub-agent convention with explicit round purposes: rounds 1-3 are flex (target the specific risk surface of the cycle's scope); rounds 4-5 are fixed (round 4 = retroactive-correction accuracy / cross-cycle bookkeeping verification; round 5 = real-world fitness / false-positive simulation). Lock in the per-round-summary directive (msg #11644) as a hard constraint. Lock in the second-pass discipline (verify claimed code changes by reading actual code, not just commit messages) as a default reviewer behavior.
- **Expected benefit:** Every substantive cycle gets a deterministic spine of review rounds (numerical-correctness check + empirical-failure-mode check) regardless of scope. The reviewer becomes a documented workflow stage, discoverable for future cycles.
- **Risk level:** low (workflow-doc addition + reviewer-log convention; no production-runtime change; no test suite change beyond the reviewer logs)
- **Safety classification:** auto_safe (workflow-doc amendment + reviewer-log convention; no code change to validator, parser, or production runtime)
- **Validation required:** cycle 11's PI-019 application must (a) add Stage 12 to the workflow doc with the round purposes documented, (b) the cycle-11 reviewer log must enumerate 5 rounds with a per-round-summary directive, (c) cycle 12 (and beyond) must spawn a code-reviewer sub-agent per Stage 12, (d) PI-019 itself is verifiable by reading the cycle-11 reviewer log + the Stage 12 section in the workflow doc.
- **Status:** APPLIED (cycle 11, NEW)
- **Cycle:** 11

---

## PI-020 — Forecast methodology refinement: capture collect-only baseline at forecast-time (NEW, cycle 12)

- **Improvement ID:** PI-020
- **Evidence reference:** EV-022, RS-022, cycle-11 closeout memo (`memory/2026-07-01-cycle-11-closeout.md`).
- **Observed problem:** PI-018 (cycle 11 NEW, APPLIED) established the post-merge verification step: after the cycle's PR merges, run `make dreaming-validate` on actual `main` and compare to the cycle author's forecast. Cycle 11's forecast missed by +3 because the forecast reasoned from `def test_` count but did not account for `@pytest.mark.parametrize` driven by `_all_dreaming_files()` in `tests/dreaming/test_no_hidden_reasoning_capture.py`. Cycle 11 added 1 NEW file to `.openclaw/dreaming/` (`cycle-11-review-log.md`, committed by reviewer) and modified 2 existing files (`workflow-nightly-dreaming.md` adding Stage 11 + Stage 12, `proposed-improvements.md` adding PI-018 + PI-019). Only the 1 NEW file was newly enumerated by `_all_dreaming_files()` and contributed +3 parametrized test invocations (3 parametrized tests × 1 newly-enumerated file); the 2 modified files were already present pre-cycle-11 and did not add new parametrized test invocations. The post-merge verification step (PI-018) caught the +3 correctly, but the forecast itself was a reasoned estimate rather than a captured number. Future cycles face the same risk: parametrized-test expansions (and other dynamic test-count sources) make the reasoned estimate unreliable.
- **Affected package:** `.openclaw/dreaming/workflow-nightly-dreaming.md` (Stage 0a added as a new section under Stage 0; not an amendment to Stage 0 itself), `tests/dreaming/test_pr_readiness.py` (new test enforcing the collect-only baseline in pr-change-log.md), `.openclaw/dreaming/regression-scenarios.md` (RS-022), `.openclaw/dreaming/evidence-index.md` (EV-022).
- **Recommended change:** PI-020 strengthens the forecast-discipline (PI-016) by adding a **pre-merge baseline-capture step**: when the cycle author writes the cycle row in `pr-change-log.md`, they must also run `python3 -m pytest tests/dreaming/ --collect-only -q | grep "tests collected"` and quote the captured baseline as a `Collected-test baseline (forecast): <N> tests collected` line in the cycle row. This gives a precise baseline (rather than a reasoned estimate), making the post-merge verification step (PI-018) more deterministic. PI-020 is the symmetry partner of PI-018: pre-merge baseline-capture + post-merge verification. The cycle author can also include the parametrized-test-expansion delta explicitly (e.g., "cycle 12 adds 1 new file to `.openclaw/dreaming/` which adds 3 parametrized tests, so the collect-only baseline of 132 should match the post-merge count of 135"). PI-020 adds a forward-looking test `test_pr_change_log_includes_collect_only_forecast_baseline` that asserts the cycle row contains the captured baseline line.
- **Expected benefit:** The forecast-baseline becomes a captured number, not a reasoned estimate. Future cycles' forecasts will reflect parametrized-test expansions and other dynamic test-count sources. PI-018's verification step now compares the actual collected count to the captured baseline, surfacing drift caused by out-of-band test additions (e.g., reviewer-driven parametrization changes). The cycle-12 forecast-discipline test enforces the discipline going forward.
- **Risk level:** low (workflow-doc amendment + new test + ledger entries; no production-runtime change; no schema migration)
- **Safety classification:** auto_safe (workflow-doc amendment + test addition + RS/EV/PI ledger entries; no code change to validator, parser, or production runtime)
- **Validation required:** cycle 12's PI-020 application must (a) add Stage 0a to the workflow doc with the collect-only forecast step, (b) add `test_pr_change_log_includes_collect_only_forecast_baseline` to `tests/dreaming/test_pr_readiness.py`, (c) add RS-022 and EV-022 to their respective ledgers, (d) PI-020 itself is verifiable by running `make dreaming-validate` on cycle 12's branch and confirming the new test passes on the cycle-12 row's collected-test baseline.
- **Status:** APPLIED (cycle 12, NEW)
- **Cycle:** 12

---

## Summary of cycle-10 PI status

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
| PI-010 | informational | proposed (cycle 2)
| PI-011 | auto_safe | APPLIED (cycle 4) |
| PI-012 | auto_safe | APPLIED (cycle 4) |
| PI-013 | review_required | APPLIED (cycle 5) |
| PI-014 | auto_safe | proposed (cycle 7, NEW) |
| PI-015 | auto_safe | APPLIED (cycle 8, NEW) |
| PI-016 | auto_safe | proposed (cycle 9, NEW) |
| PI-017 | auto_safe | APPLIED (cycle 10, NEW) |
| PI-018 | auto_safe | APPLIED (cycle 11, NEW) |
| PI-019 | auto_safe | APPLIED (cycle 11, NEW) |
| PI-020 | auto_safe | APPLIED (cycle 12, NEW) |
| PI-021 | auto_safe | APPLIED (cycle 13, NEW) |
| PI-022 | auto_safe | proposed (cycle 13, NEW; cycle-12 carry-forward candidate) |

---

## PI-021 — Forecast-format clarification: enforce explicit `collected → passed` arithmetic in cycle row forecast (NEW, cycle 13)

- **Improvement ID:** PI-021
- **Observed problem:** PI-016 (cycle 9) established the convention that every cycle row in `pr-change-log.md` must include a `Main post-merge (forecast)` line. PI-018 (cycle 11) added a post-merge verification step. PI-020 (cycle 12) added a pre-merge collect-only baseline-capture step (Stage 0a) that captures the precise baseline at forecast-time. However, the cycle-12 row's `Main post-merge (forecast)` line was written as `136 passed + 1 skipped + 1 expected-fail-on-main` — where `136` was actually the **collected** count (133 branch-local baseline + 3 parametrized-test expansion delta), not the **passed** count. The arithmetic `136 collected → 134 passed + 1 skipped + 1 expected-fail-on-main` matches the actual post-PR-#72 `main` count (`134 passed + 1 skipped + 1 expected-fail-on-main` at merge SHA `5fbc1f9`) perfectly; the cycle-12 row's −2 delta was purely a **forecast-format labeling bug** (the number was labeled as "passed" when it was actually "collected"). PI-018 / Stage 11 caught the partial-failure forecast (−2 at PR #72, −4 at PR #71), but the failure mode is a forecast-format labeling issue, not a methodology or merge-state issue. Future cycles face the same risk: a forecaster may label a `collected` number as `passed` (or vice versa) and produce an arithmetic-incorrect forecast that fails post-merge verification.
- **Recommended change:** PI-021 strengthens the forecast-discipline (PI-016 / PI-018 / PI-020) by requiring cycle rows to use one of two explicit forecast formats:
  - **Format A (preferred):** `Main post-merge (forecast): N collected → (N-2) passed + 1 skipped + 1 expected-fail-on-main`, where the explicit `collected → passed` arithmetic is shown inline. Example: `Main post-merge (forecast): 136 collected → 134 passed + 1 skipped + 1 expected-fail-on-main`.
  - **Format B (legacy-compatible):** `Main post-merge (forecast): N passed + 1 skipped + 1 expected-fail-on-main` where the row also includes a separate `Collected-test baseline (forecast): N tests collected` line (per Stage 0a) AND the cycle's actual-on-main verification uses `pytest --collect-only -q` to confirm `N collected → (N-2) passed` arithmetic. Format B is the cycle-12 PR #71 format; it works but couples the "passed" label to the row's separate baseline line, which is easy to misread.
  - **Format C (collected-only):** `Main post-merge (forecast): N collected` (no `passed` count in the forecast at all). This is acceptable when the cycle author chooses not to predict the passed/skipped/expected-fail-on-main breakdown, but Stage 11's verification step still computes the actual `passed` count from the actual collect-only baseline.

  The key invariant: a forecast's **number** must be unambiguously either **collected** or **passed**, and the **arithmetic** between the two (`collected - 1 skipped - 1 expected-fail-on-main = passed`) must be explicit or trivially derivable from a separate baseline line in the same cycle row.
- **Expected benefit:** Future cycles' forecasts will be unambiguous between `collected` and `passed`. The post-merge verification step (PI-018) compares the actual `main` collect-only count to the forecast; if the forecast's number was labeled incorrectly (e.g., "passed" when it was actually "collected"), the verification will catch the arithmetic mismatch deterministically. The cycle-13 forecast-discipline test (`test_pr_change_log_forecast_uses_explicit_collected_or_passed_label`, NEW, PI-021) enforces the label-format discipline going forward and rejects forecasts that mix `collected` and `passed` labels without explicit arithmetic.
- **Validation required:** cycle 13's PI-021 application must (a) add the forecast-format-label convention to `workflow-nightly-dreaming.md` Stage 0a (clarify that the post-merge forecast must use Format A or Format B with explicit arithmetic), (b) add `test_pr_change_log_forecast_uses_explicit_collected_or_passed_label` to `tests/dreaming/test_pr_readiness.py` enforcing the label convention, (c) add RS-023 to `regression-scenarios.md` and EV-023 to `evidence-index.md`, (d) cycle-13 row uses Format A (preferred), (e) PI-021 is verifiable by running `make dreaming-validate` on cycle-13's branch and confirming the new test passes on the cycle-13 row's explicit-format forecast.
- **Linked PIs:** PI-016 (cycle 9, APPLIED), PI-018 (cycle 11, APPLIED), PI-020 (cycle 12, APPLIED)
- **Linked regression scenarios:** RS-023 (NEW, cycle 13)
- **Cycle:** 13
- **Safety classification:** `auto_safe` (workflow-doc amendment + test addition + RS + EV + PI ledger entries + cycle-row format update).

---

## PI-022 — Forecast-merge-state-clarification: explicitly state assumed merge state in forecast (NEW, cycle 13; cycle-12 carry-forward)

- **Improvement ID:** PI-022
- **Observed problem:** PI-016 (cycle 9) and PI-018 (cycle 11) require cycle rows to forecast `main` post-merge counts. PI-020 (cycle 12) added the pre-merge baseline-capture step. However, the cycle-12 row's `Main post-merge (forecast)` line implicitly assumed **all reviewer-driven additions would be in the merge** (the +3 parametrized-test expansion was based on the cycle-12 reviewer log being added by the reviewer sub-agent). The actual PR #71 merge was at Round 3 fix-up state (`a1920b3`), and the reviewer log was committed locally on the cycle-12 branch (commits `ebbb3b9` and `088bfd7`) but not pushed to origin before the merge. The actual `main` post-PR #71 count was `132 + 1 + 1` (−4 from forecast), exactly because the reviewer log was not in the merge. The cycle-12 PR #72 follow-up merged the reviewer log + drift check + regex widening, and the actual count became `134 + 1 + 1` (the reviewer log's +3 expansion fired, but the cycle-12 row's `136 passed` label was a Format-B labeling bug — PI-021 territory). The cycle-12 row's forecast was a **conditional prediction** tied to a reviewer-driven file addition that did not land in the PR #71 merge; the forecast was off by −4 because the forecast's merge-state assumption (reviewer-driven additions in merge) was wrong. PI-018 / Stage 11 caught the −4 delta correctly via the cycle-12 closeout memo, but the failure mode was a **merge-state-assumption** issue, not a methodology or label-format issue. Future cycles face the same risk: a forecaster may implicitly assume reviewer-driven additions are merged when the PR is actually merged at the substantive-commit state (or vice versa), producing an off-by-N forecast.
- **Recommended change:** PI-022 strengthens the forecast-discipline (PI-016 / PI-018 / PI-020 / PI-021) by requiring cycle rows to **explicitly state the assumed merge state** in the `Main post-merge (forecast)` line. Acceptable assumed-merge-state values:
  - `substantive-commit-only`: PR is merged at the cycle's substantive commit (no reviewer-driven additions in merge). Forecast arithmetic: `branch-local collect-only baseline - 1 (skipped) - 1 (expected-fail-on-main) = passed`.
  - `with-reviewer-driven-additions`: PR is merged with all reviewer-driven additions (5 rounds per Stage 12). Forecast arithmetic: `branch-local collect-only baseline + (3 × reviewer-added-files) - 1 (skipped) - 1 (expected-fail-on-main) = passed`.
  - `mixed`: PR is merged at a specific round (e.g., "merged at Round 3 fix-up state, no Rounds 4-5 additions"). Forecast arithmetic: explicit count of which reviewer rounds are in-merge, parametrized-expansion delta computed accordingly.

  The key invariant: a forecast must explicitly state which reviewer-driven additions are in the merge, so the post-merge verification (PI-018) can compare the actual count against the correct baseline.
- **Expected benefit:** Future cycles' forecasts will be unambiguous about which reviewer-driven additions are assumed in the merge. The post-merge verification step (PI-018) compares the actual `main` count to the forecast; if the forecast's merge-state assumption is wrong (e.g., reviewer-driven additions were not in the merge), the verification will catch the off-by-N delta and the closeout memo will document the merge-state discrepancy rather than a methodology failure. PI-022 is informational and may not need a dedicated test; the cycle-13 carry-forward is the documentation update to Stage 0a and the cycle-row-format convention.
- **Validation required:** cycle 13 (and beyond) must state the assumed merge state in the cycle row's `Main post-merge (forecast)` line. The Stage 0a amendment (PI-021 application) includes the merge-state-clarification convention as a sibling to the label-format convention. PI-022 does NOT add a new test; it is enforced by the cycle author's diligence per Stage 0a + Stage 11.
- **Linked PIs:** PI-016 (cycle 9, APPLIED), PI-018 (cycle 11, APPLIED), PI-020 (cycle 12, APPLIED), PI-021 (cycle 13, APPLIED)
- **Linked regression scenarios:** RS-022 (cycle 12; carries forward the collect-only-baseline convention)
- **Cycle:** 13
- **Safety classification:** `auto_safe` (workflow-doc amendment to Stage 0a; no new test or RS/EV ledger entries beyond the PI-021 sibling amendment). Carries forward as a cycle-13 documentation-only PI; can be promoted to a tested PI in a future cycle if the merge-state assumption becomes a recurring source of forecast failures.

---

No blocked-class changes proposed in cycle 12 or planned for cycle 13. The cycle-13 PR amends Stage 0a with the forecast-format-label convention (PI-021) and the merge-state-clarification convention (PI-022 sibling amendment), adds one new test enforcing the label-format convention (PI-021), adds RS-023 and EV-023 to their respective ledgers, backfills the cycle-12 row's forecast line to Format A (explicit `collected → passed` arithmetic), and pre-pends a cycle-13 body to `nightly-summary.md` using the Stage -2 schema. The cycle-13 row uses Format A (preferred). No code changes to the parser, spec, or test suite beyond the new test.
