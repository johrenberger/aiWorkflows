# Lessons Learned

Cycle: 2026-06-29 cycle-4

Compact, evidence-backed. No vague lessons. Each lesson has a single evidence reference.

L-001 through L-008 are carried from cycle 1; L-009 through L-013 are new in cycle 2.

---

## L-001 — Lock permissive state in tests before flipping to strict (carried + reframed)

- **Evidence:** EV-001, EV-007 (cycle-2 reframing)
- **Observed behavior:** The SGP ship (EV-001, single timestamp in cycle 1) is actually a 16-PR arc (EV-007). PR #43 ships v1.0.0 in permissive mode. PRs #44–46 push coverage and BDD density. PRs #47, #50 add CI gates. PR #57 adds a test that locks in the permissive state. PR #58 flips mypy to strict with full annotations. Strict mode and the permissive-state test coexist.
- **Interpretation:** Cycle 1's L-001 was based on a single PR pair (`efd083d` → `a965c13`). Cycle 2's trace shows that the same pattern was applied **three times in series** (permissive → test-locks-permissive → strict-flip): once for mypy strict (PRs #57, #58), and the pattern is the canonical way the team tightened any validation gate in the SGP work.
- **Future execution guidance:** Any time a "permissive → strict" transition is contemplated, capture the permissive state as a test, then a progression script, then flip. The pattern is well-evidenced now and should be a routing rule.
- **Affected workflow / skill:** SGP, generic validation discipline
- **Regression scenario link:** RS-001

---

## L-002 — Mutation testing surfaces real coverage gaps (carried + widened)

- **Evidence:** EV-001, EV-007
- **Observed behavior:** Cycle 1 captured one mypy-line ("261 survived, 99.6%") as L-002 evidence. EV-007 shows the broader context: mutation testing was a continuous concern in SGP, with `efd083d` (test locks permissive state) and `a965c13` (strict-flip) being just one axis of the quality arc.
- **Interpretation:** L-002 was correct but underspecified. Cycle 2 widens it: mutation testing is one of multiple complementary gates (mypy strict, branch coverage, hypothesis property tests, ruff lint). No single gate is sufficient; the gate-stack is the value.
- **Future execution guidance:** Apply a gate-stack, not a gate. For decision code (routing, scoring, classification): unit + branch coverage + mutation + mypy strict + ruff + at least one property-based test for invariants.
- **Affected workflow / skill:** SGP, generic validation discipline
- **Regression scenario link:** RS-002

---

## L-003 — Document the full state machine before any validator lands (carried)

- **Evidence:** EV-002
- **Future execution guidance:** SKILL.md must include a complete transition table or explicit "no path" assertions.
- **Affected workflow / skill:** `task-state-management`
- **Regression scenario link:** RS-003

---

## L-004 — DOTALL regexes match across section boundaries (carried)

- **Evidence:** EV-002
- **Future execution guidance:** Prefer line-by-line scanners over `re.DOTALL` for structured-document validators.
- **Affected workflow / skill:** `task-state-management`, generic validator discipline
- **Regression scenario link:** RS-004

---

## L-005 — Sub-agent reviewers catch concurrency bugs BDD does not (carried)

- **Evidence:** EV-003
- **Future execution guidance:** Run sub-agent code review on finalize/finalizeFailure paths before declaring a slice done.
- **Affected workflow / skill:** `code-review-slice-N` (emergent)
- **Regression scenario link:** RS-005, RS-007

---

## L-006 — Multi-tenant `/health` and `/ready` endpoints must not leak tenant-derived data (carried)

- **Evidence:** EV-003
- **Future execution guidance:** Strict `/health` and `/ready` contracts: no tenant-derived fields, no row counts.
- **Affected workflow / skill:** `BusinessOperationsDashboard`, generic API-design discipline
- **Regression scenario link:** RS-006

---

## L-007 — Dreaming requires structured run logs to do its full job (carried; **unchanged in cycle 2**)

- **Evidence:** EV-004
- **Cycle-2 status:** unchanged. `find` across `/data/.openclaw/workspace` still returns no structured run logs. PI-006 still proposed, still not applied. This is the single largest unfilled gap from cycle 1.
- **Future execution guidance:** Add a JSONL run log. Until then, dreaming's per-tool-call retry/timeout/blocked-state findings are unavailable.
- **Affected workflow / skill:** dreaming workflow itself
- **Regression scenario link:** RS-008

---

## L-008 — Tracked-but-untested limitations become untested assumptions (carried)

- **Evidence:** EV-005
- **Cycle-2 status:** unchanged. PI-007 still proposed, not applied.
- **Regression scenario link:** RS-009

---

## L-009 — CI-environment mismatch caused 5 of cycle-1's 9 commits

- **Evidence:** EV-006
- **Observed behavior:** Cycle 1 generated 9 commits and 5 were fix-ups. All 5 fix-ups were the same root cause: the code worked locally but not in CI. Specifically: detached HEAD with no `main` ref, marker-scan greps matching rule-documenting files, and "ensure X is not configured" greps matching docs that say "do not configure X".
- **Interpretation:** Local "passes" ≠ CI "passes." The gap costs 5 fix-up commits and 5 re-push cycles. PI-008 (local validation via Makefile) was retroactively identified as the fix.
- **Future execution guidance:** Every workflow that has CI validation should expose the same validation as a pre-push target (`make <workflow>-validate`). Running that target locally catches CI-environment mismatches before they consume push cycles.
- **Affected workflow / skill:** dreaming workflow; extensible to SGP (PI-009)
- **Regression scenario link:** RS-010

---

## L-010 — Spec-vs-implementation gap on `DREAMING.md`: cycle-1 branch regex was over-strict

- **Evidence:** EV-008 (PI-008 first use)
- **Observed behavior:** Cycle 1's `test_current_branch_uses_dreaming_prefix` test asserted the branch name matched `^dreaming/nightly-execution-quality-(\d{4}-\d{2}-\d{2})$`. Cycle 2's branch (`dreaming/nightly-execution-quality-2026-06-29-cycle-2`) has a `-cycle-2` suffix and broke the regex. The spec text says "Do not split the nightly dreaming output into multiple PRs in this version" — ambiguous on whether future cycles get their own branches.
- **Interpretation:** Spec ambiguity always shows up at the test. Cycle 2's branch name is the right move (cycle 1's branch was deleted on merge), so the spec needs to allow cycle suffixes and the test must accept them.
- **Future execution guidance:** When tests assert against spec language, double-check the spec leaves room for the natural extension. Branch naming with cycle suffixes is a reasonable extension; document it explicitly in `DREAMING.md`.
- **Affected workflow / skill:** dreaming workflow
- **Regression scenario link:** RS-011

---

## L-011 — Quality-tightening arcs are themselves the canonical evidence (NEW)

- **Evidence:** EV-007
- **Observed behavior:** The SGP work from cycle 1 (single timestamp `01d1c34`) is in fact a 16-PR arc over 4 days (#43 → #58). Each PR added one quality dimension (coverage, BDD, CI gate, mypy, ruff, hypothesis, HITL). The whole is the lesson; any single PR is a moment in it.
- **Interpretation:** Single-event evidence collapses arc-scale patterns into snapshots. PR-review activity as an evidence source (added in cycle 2) is what un-collapses them.
- **Future execution guidance:** When reviewing prior activity, prefer arc-scale evidence (PR traces, commit chains) over single-event snapshots. A "ship date" is the start of a tightening arc, not a discrete accomplishment.
- **Affected workflow / skill:** dreaming workflow, generic retrospective discipline
- **Regression scenario link:** RS-002 (reframed)

---

## L-012 — Local CI has compounding returns on its first use (NEW)

- **Evidence:** EV-008
- **Observed behavior:** PI-008's first use (cycle 2, `make dreaming-validate`) caught 2 real issues before push: branch regex too strict (L-010), commit-prefix test failing on empty range (L-013). The same classes of issue caused 5 fix-up commits in cycle 1; PI-008's first run prevented the same pattern from recurring in cycle 2.
- **Interpretation:** "Bake in" pre-push validation that mirrors CI exactly. The first use pays the cost of writing the target; subsequent uses pay only the seconds-to-run.
- **Future execution guidance:** When adopting a CI workflow that runs nontrivial tests, write the local-equivalent Makefile target in the same PR. Otherwise the second cycle will pay the cycle-1 fix-up tax.
- **Affected workflow / skill:** dreaming workflow; extensible (PI-009)
- **Regression scenario link:** RS-012

---

## L-013 — Spec rules must be honest about expected usage (NEW)

- **Evidence:** EV-008 (commit-prefix test failure on empty range)
- **Observed behavior:** `test_commits_use_chore_dreaming_prefix` originally failed when there were no commits on the branch. The Makefile target is designed to run *before* the first commit too. A test that fails on a clean branch is a test that prevents its own consumers from running it.
- **Interpretation:** Test design must anticipate "this test runs in environments where the precondition may not yet hold." For a Makefile-driven pre-push target, an empty commit log is the *expected* state on the first run.
- **Future execution guidance:** Write tests such that the precondition-empty case skips gracefully. Otherwise the test prevents the very workflow it is supposed to support.
- **Affected workflow / skill:** dreaming workflow
- **Regression scenario link:** RS-012

---

## L-014 — Workflow triggers must distinguish PR from base branch (NEW)

- **Evidence:** EV-010
- **Observed behavior:** `nightly-dreaming-validation.yml`'s `on: push:` block listed both `dreaming/nightly-execution-quality-*` and `main`. After PR #60 merged to main, GitHub fired a `push` CI run on main. The PR-readiness tests (`test_current_branch_uses_dreaming_prefix`, `test_commits_use_chore_dreaming_prefix`) are nonsensical on main because:
  - there is no PR head ref to assert against
  - the commit range `[merge-base..HEAD]` is empty when merge-base == HEAD, immediately after a merge
- **Interpretation:** A CI workflow's trigger list is part of its tested surface. Bundling `main` into a workflow that contains PR-readiness assertions causes those assertions to fire in environments where the precondition does not hold.
- **Future execution guidance:** When writing a CI workflow that contains PR-readiness assertions (branch naming, commit-prefix, scan-vs-PR-base), restrict the `push:` trigger to the branches that own the PRs; leave `pull_request:` to cover main-becoming-PR-base. Independently, the tests themselves should skip gracefully when the precondition does not hold, so that ad-hoc triggers do not become firefights.
- **Affected workflow / skill:** dreaming workflow; extensible (PI-009 — generalization to other workflows)
- **Regression scenario link:** RS-013, RS-014

---

## L-015 — Workspace-state assertions should surface at human time (NEW, cycle 4)

- **Evidence:** EV-012, EV-013
- **Observed behavior:** Cycle 3's `test_only_one_dreaming_branch_exists` issue (a lingering cycle-2 branch on disk) was caught only when `make dreaming-validate` ran. The same fact was true at cycle 3's start: the cycle-2 branch was already on disk. The fact that it existed was *not* part of cycle 3's evidence; only its consequence (a failing test) entered the evidence stream.
- **Interpretation:** Validation-time assertions and human-time assertions differ in cost. A test that fires only at validation time exposes a state problem at the wrong moment; a precheck surfaces the same fact earlier, when it can be addressed preventively.
- **Future execution guidance:** When a state condition is "the kind of thing you wish you'd checked before pushing," make it visible at session-start (or PR-start), not at validation-time. PI-012 is the first instance of this pattern in dreaming.
- **Affected workflow / skill:** dreaming workflow, generic PR-readiness discipline
- **Regression scenario link:** RS-015
