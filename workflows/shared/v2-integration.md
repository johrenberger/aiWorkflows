# v2 × Coverage Workflow Integration

**Cross-workflow protocol for using `application-test-automation-v2` (the deterministic tool) as the analysis backend for `application-test-coverage` (the LLM-driven workflow).**

## Why this exists

`application-test-coverage` and `application-test-automation-v2` were originally two parallel attempts to solve the same problem: figure out which test files to write to close coverage gaps in a target repo. They overlap massively:

- **Both** detect language stack, test framework, coverage tooling.
- **Both** build a per-file coverage table.
- **Both** classify eligible vs. excluded files.
- **Both** produce an ordered work queue of files to test.

`coverage` does all of this with the LLM re-deriving values by reading the repo. It's slow and inconsistent — two runs against the same repo can produce different stack detections if the LLM notices different signals. `v2` does it deterministically with static analysis. It's fast and consistent, but it doesn't write tests — that's still the LLM's job.

The integration keeps the LLM where it adds value (test design, mock fidelity, test writing) and pushes the deterministic work into v2 where the LLM is just a slower, less reliable substitute.

## The contract

The coverage workflow's `prompt-implementation.md` gains a new **Phase 2.5** between Phase 0.5 (env pre-flight) and Phase 3 (stack detection). Phase 2.5:

1. Calls `workflows/shared/integrate-v2.sh <repo> <artifacts> [limit] [--generate-coverage]`.
2. Reads `v2_summary.md` from the artifacts.
3. **Cites v2 JSON files as evidence** for TC-FRAMEWORK-1, TC-VAL-3, TC-VAL-5, TC-CKPT-6, TC-CKPT-7, TC-CKPT-8.
4. **Skips Phases 3-9** in the original prompt — the v2 outputs already cover them.
5. Goes straight to Phase 10 (work batch selection), taking the top N from v2's `test_gap_queue.json`.
6. For each work-batch file, hands the matching `ai_work_items/wi-<hash>.md` to the LLM as the per-file spec (TC-ITEM-N.N).

The LLM is still the executor for Phases 10-18 (work batch, test design, implementation, focused validation, coverage recheck, repair, full validation, ledger, commit). The LLM is also the owner of the canonical ledger (`TODO_test-coverage.md`).

## Phases 3-9 → v2 output mapping

| Coverage workflow phase | v2 artifact | What it provides |
|---|---|---|
| **3. Stack/framework detection** | `language_stack.json` + `adapter_detections.json` | Detected languages, primary adapter, framework (pytest, junit, jest, etc.) |
| **4a. Multi-module scope** | `module_graph.json` | Module boundaries, language per module |
| **5. Baseline tests** | `commands_discovered.json` | Canonical test command per language |
| **6. Baseline coverage** | `coverage_baseline.json` (+ optionally `coverage_runs/generate.json`) | Per-file line + branch coverage |
| **7. Testability classification** | `risk_scores.json` | Per-file risk factors: complexity, churn, public_api_exposure, dependency_fan_in, defect_history, data_or_security_sensitivity, coverage_gap |
| **8. Eligibility** | `exclusions.json` + filter on `risk_scores.json` | Files excluded with rationale; eligible files have `coverage_gap > 0` |
| **9. Coverage gap map** | `test_gap_queue.json` | Sorted queue: `risk_score × coverage_gap` descending |
| **10. Work batch** | `test_gap_queue.json[:N]` | Top N files (where N = `MAX_FILES_PER_BATCH`) |
| **11. Test design (per file)** | `ai_work_items/wi-<hash>.md` | Per-file work-item spec: target lines, conventions, existing tests, recommended test type |

## What the LLM still owns (unchanged)

- **Phase 11 (test design)** for the work batch — the v2 work-item spec is a starting point, not a complete design. The LLM adds:
  - Which behavior to assert (mock fidelity, return types, branch coverage strategy)
  - Fixtures and builders
  - AAA structure
  - Edge cases beyond what v2 enumerated
- **Phase 12 (test implementation)** — actual file writes. v2 doesn't write code.
- **Phase 13 (focused tests)** — running the new tests, debugging failures.
- **Phase 14 (coverage recheck)** — re-running v2 (`test-factory run --generate-coverage`) and diffing `coverage_baseline.json`.
- **Phase 15 (repair)** — re-running tests after fixes.
- **Phase 16 (full validation)** — running the full test suite.
- **Phase 17 (ledger finalization)** — `TODO_test-coverage.md` finalization.
- **Phase 18 (commit)** — git commit and (optionally) PR.
- **Sub-agent orchestration** — the 3-role protocol (discoverer / test-writer / coverage-manager) from `application-test-coverage/_docs/multi-module-orchestration.md` still applies. The discoverer's job shrinks to "filter v2's queue by MODULE_LIST" instead of re-deriving the module map.

## Hard rules for the LLM

These are non-negotiable. They are what makes the integration worth doing instead of just giving the LLM two tools to confuse.

1. **The LLM MUST NOT re-derive stack, framework, or coverage values** from manual grep / file reading. The v2 outputs are the source of truth. If the LLM believes v2 is wrong, it MUST:
   - Document the disagreement in `TC-OBS-1 [Commands Executed]`.
   - Cite the v2 artifact it disagrees with.
   - Either: (a) fall back to the v2 value, or (b) skip the file and record it as `TC-BLK-V2Disagreement`.

2. **The LLM MUST NOT skip the v2 step** if `test-factory` is on PATH. Even if the LLM "knows" the stack, the v2 outputs are needed for: the work queue, the per-file risk factors, and the per-file work-item specs.

3. **The LLM MUST NOT re-implement Phases 3-9** even partially. The v2 outputs replace the entirety of those phases.

4. **The LLM MUST cite the v2 artifact path in the ledger's evidence fields** for every section that came from v2. Example:
   ```
   ## Framework Detection

   - [ ] **TC-FRAMEWORK-1 [Detected Stack]**
     - Language: python
     - Package Manager: pip
     - Test Framework: pytest 8.4.2
     - Coverage Tool: pytest-cov 6.3.0 + coverage 7.14.1
     - CI Config: (none detected)
     - Evidence: workflows/shared/integrate-v2.sh output -> v2/language_stack.json
   ```

5. **The LLM MUST NOT modify files in the v2 output directory** (`<artifacts>/v2/`). v2 writes are deterministic; the LLM must re-run v2 if it wants a fresh analysis. This is a read-only directory from the LLM's perspective.

6. **The LLM MUST re-run v2 after each test batch** to get a coverage delta. The diff between the new `coverage_baseline.json` and the pre-batch one is `TC-VAL-RESULT-2 [Coverage Recheck]`'s evidence.

## When v2 is unavailable

If `test-factory` is not on PATH, `integrate-v2.sh` exits with code 1. The coverage workflow MUST then:

1. Record `TC-BLK-V2NotInstalled` in the ledger.
2. **Fall back to the legacy Phase 3-9 manual detection** (the original prompt-implementation.md sections).
3. Note in the final summary that the run was non-deterministic and may be harder to reproduce.

This is the **graceful-degradation** path. Users who want the deterministic core MUST install v2:

```bash
pip install --break-system-packages -e "$WORKSPACE/workflows/application-test-automation-v2[dev]"
```

The `[dev]` extra pulls in the pinned `pytest>=8,<9`, `pytest-cov>=6,<8`, `coverage>=7` (added in PR #24 to the v2 pyproject.toml).

## Schema stability

As of 2026-06-11, the v2 output schema is not yet versioned. The integration assumes:

- The 13 JSON outputs documented in `application-test-automation-v2/README.md` are present.
- The field names in `risk_scores.json` are stable: `path`, `line_coverage`, `coverage_gap`, `complexity`, `churn`, `public_api_exposure`, `dependency_fan_in`, `defect_history`, `data_or_security_sensitivity`, `risk_score`, `module`.
- The work-item filenames are stable: `ai_work_items/wi-<10-char-hex>.md`.

If v2's schema changes, the integration breaks silently. **Followup**: add a `schema_version` field to each v2 JSON output and have `integrate-v2.sh` verify it matches what the coverage workflow expects. Tracked separately; out of scope for the initial integration.

## Performance

| Repo size | v2 cold run (no `--generate-coverage`) | v2 warm run (pre-existing reports) | With `--generate-coverage` |
|---|---:|---:|---:|
| Small (< 100 source files) | ~5s | <1s | + 30-60s (depends on test count) |
| Medium (100-1000 files) | ~20s | ~5s | + 1-5 min |
| Large multi-module (1k+ files) | ~60-120s | ~20-30s | + 5-20 min |

The `coverage` workflow's manual Phase 3-9 takes the LLM 5-15 minutes on a small repo and 30+ minutes on a large one. v2 is consistently faster.

## Validation gates

Two new gates are added to `application-test-coverage/validation.md`:

- **TC-VAL-22 [v2 Analysis Consumed]** — if `test-factory` is on PATH, the artifacts directory contains `v2/v2_summary.md` and the LLM has cited at least 5 of v2's JSON files in the ledger evidence fields.
- **TC-VAL-23 [No Re-Detection]** — TC-FRAMEWORK-1, TC-VAL-3, TC-CKPT-5, TC-CKPT-7, TC-CKPT-8 all have evidence fields that cite v2 artifacts. If the LLM re-derived any of these from manual reading, it MUST document the disagreement in TC-OBS-1.

## Example end-to-end run

```bash
# Phase 0.5: env pre-flight (existing coverage workflow logic)
workflows/shared/environment-pre-flight.sh /data/coverage-runs/broadleaf

# Phase 2.5: deterministic analysis (NEW)
workflows/shared/integrate-v2.sh \
  /data/coverage-runs/broadleaf \
  /data/coverage-runs/broadleaf/artifacts \
  50 \
  --generate-coverage

# Output: /data/coverage-runs/broadleaf/artifacts/v2/v2_summary.md
# Plus:   /data/coverage-runs/broadleaf/artifacts/v2/{13 JSON files}
# Plus:   /data/coverage-runs/broadleaf/artifacts/v2/ai_work_items/wi-*.md

# Phase 10+: LLM-driven test writing (unchanged from coverage workflow)
#   - Read v2_summary.md
#   - Take top 5 from test_gap_queue.json
#   - For each, hand the matching wi-*.md to a test-writer sub-agent
#   - Sub-agent implements tests in its worktree branch
#   - Main agent merges branch, re-runs v2, diffs coverage
```

## Reference

- `workflows/shared/integrate-v2.sh` — the wrapper script.
- `workflows/application-test-coverage/prompt-implementation.md` — Phase 2.5 spec.
- `workflows/application-test-coverage/validation.md` — TC-VAL-22, TC-VAL-23.
- `workflows/application-test-automation-v2/README.md` — v2 tool reference.
- `workflows/application-test-automation-v2/test_factory/cli.py` — the `test-factory` CLI.
