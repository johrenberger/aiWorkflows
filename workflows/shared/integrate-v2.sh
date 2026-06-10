#!/usr/bin/env bash
# integrate-v2.sh
# -----------------------------------------------------------------------------
# Run application-test-automation-v2 against the target repo and emit a
# v2_summary.md that the application-test-coverage workflow can consume
# directly as evidence for Phases 3-9 (framework detection, baseline
# coverage, eligibility, gap mapping, work batch).
#
# This is the "deterministic core" half of the v2 × coverage integration.
# The "LLM at the seams" half lives in application-test-coverage's
# prompt-implementation.md (Phase 2.5), which tells the LLM to source
# framework/eligibility/gap evidence from this script's output instead
# of re-deriving it by reading the repo manually.
#
# Usage:
#   ./integrate-v2.sh <REPO_PATH> <ARTIFACTS_DIR> [LIMIT] [EXTRA_FLAGS...]
#
# Examples:
#   # Default — limit 50, no --generate-coverage (assumes pre-existing reports)
#   ./integrate-v2.sh /data/coverage-runs/broadleaf /tmp/coverage-artifacts
#
#   # End-to-end — also produce coverage.json from scratch
#   ./integrate-v2.sh /data/coverage-runs/broadleaf /tmp/coverage-artifacts 50 --generate-coverage
#
#   # Pass-through to test-factory for advanced flags
#   ./integrate-v2.sh . /tmp/art 20 --module core --exclude-tests
#
# Outputs (under $ARTIFACTS_DIR/v2/):
#   coverage_baseline.json     <- 1 record per covered file
#   risk_scores.json           <- 1 record per source file
#   test_gap_queue.json        <- sorted queue, top entry is highest priority
#   source_test_map.json       <- candidate tests + recommended test type
#   exclusions.json            <- excluded files with rationale
#   language_stack.json        <- detected languages
#   module_graph.json          <- module boundaries (multi-module repos)
#   adapter_detections.json    <- per-adapter detect() confidence
#   commands_discovered.json   <- canonical test/coverage commands
#   repo_inventory.json        <- full file inventory
#   coverage_runs/generate.json <- status of the --generate-coverage step
#   final_report.md            <- human-readable summary
#   v2_summary.md              <- TOP-LEVEL hand-off doc the LLM reads
#
# Exit codes:
#   0   v2 ran cleanly; artifacts are present
#   1   v2 not installed (test-factory not on PATH)
#   2   user input error (missing args, bad path)
#   3   v2 ran but produced no coverage_baseline.json
#   4   v2 ran but emit_coverage_workflow.sh emitted a TC-BLK-V2Failure
#       (typically: no eligible files — common on greenfield repos)
#
# Side effects:
#   - Runs the full v2 pipeline against the target repo. Can take 30s-5min
#     depending on repo size and whether --generate-coverage is set.
#   - Writes artifacts to $ARTIFACTS_DIR/v2/. The caller decides whether
#     to commit those artifacts.
#
# See also:
#   shared/v2-integration.md            (full protocol)
#   application-test-coverage/prompt-implementation.md (Phase 2.5)
#   application-test-automation-v2/README.md (v2 tool reference)
# -----------------------------------------------------------------------------
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <REPO_PATH> <ARTIFACTS_DIR> [LIMIT] [EXTRA_FLAGS...]" >&2
  exit 2
fi

REPO_PATH="$1"
ARTIFACTS_DIR="$2"
LIMIT="${3:-50}"
shift 2
# Pop LIMIT off if it was provided
if [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; then
  shift
fi
EXTRA_FLAGS=("$@")

if [[ ! -d "$REPO_PATH" ]]; then
  echo "ERROR: repo path '$REPO_PATH' does not exist or is not a directory" >&2
  exit 2
fi

if ! command -v test-factory >/dev/null 2>&1; then
  cat >&2 <<EOF
ERROR: 'test-factory' not on PATH. Install v2 first:

    pip install --break-system-packages \\
        -e "$HOME/.openclaw/workspace/workflows/application-test-automation-v2[dev]"

(or wherever the v2 source lives in your checkout)
EOF
  exit 1
fi

REPO_PATH="$(cd "$REPO_PATH" && pwd)"
ARTIFACTS_DIR="$(mkdir -p "$ARTIFACTS_DIR" && cd "$ARTIFACTS_DIR" && pwd)"
V2_OUT="$ARTIFACTS_DIR/v2"

mkdir -p "$V2_OUT"

echo "[integrate-v2] repo:   $REPO_PATH"
echo "[integrate-v2] out:    $V2_OUT"
echo "[integrate-v2] limit:  $LIMIT"
if [[ ${#EXTRA_FLAGS[@]} -gt 0 ]]; then
  echo "[integrate-v2] extra:  ${EXTRA_FLAGS[*]}"
fi

# Run the v2 pipeline. We do NOT use --generate-coverage by default
# because the coverage workflow's Phase 5 expects the user to have a
# coverage report already; the LLM will set USE_GENERATE_COVERAGE=1
# (via the extra flag) when the user has opted in.
test-factory run \
  --repo "$REPO_PATH" \
  --out "$V2_OUT" \
  --limit "$LIMIT" \
  "${EXTRA_FLAGS[@]}"

# The v2 run writes into $V2_OUT/ directly, including coverage_runs/,
# ai_work_items/, test_factory.sqlite, etc. That's the v2 contract.

# Verify the critical outputs exist. If coverage_baseline.json is missing,
# v2 either crashed or the repo has nothing to cover (e.g. docs-only).
if [[ ! -f "$V2_OUT/coverage_baseline.json" ]]; then
  cat >&2 <<EOF
WARNING: v2 ran but $V2_OUT/coverage_baseline.json was not produced.

This usually means the repo has no scannable source files, or v2's
adapters failed to detect a language stack. Check:
  - $V2_OUT/final_report.md
  - $V2_OUT/exceptions_register.yaml
  - $V2_OUT/adapter_detections.json

Returning exit 3 so the caller can fall back to manual detection.
EOF
  exit 3
fi

# Emit v2_summary.md — the hand-off doc the LLM reads.
# This is the "deterministic functions" payload for Phases 3-9.
SUMMARY="$V2_OUT/v2_summary.md"
{
  echo "# v2 Analysis Summary"
  echo
  echo "Generated by \`workflows/shared/integrate-v2.sh\` on $(date -u +'%Y-%m-%dT%H:%M:%SZ')."
  echo
  echo "## Inputs"
  echo
  echo "- Repo: \`$REPO_PATH\`"
  echo "- Artifacts: \`$V2_OUT\`"
  echo "- Limit: $LIMIT"
  if [[ ${#EXTRA_FLAGS[@]} -gt 0 ]]; then
    echo "- Extra flags: \`${EXTRA_FLAGS[*]}\`"
  fi
  echo
  echo "## Detected Stack (TC-FRAMEWORK-1 evidence)"
  echo
  echo '```json'
  if [[ -f "$V2_OUT/language_stack.json" ]]; then
    cat "$V2_OUT/language_stack.json"
  else
    echo "{}"
  fi
  echo '```'
  echo
  echo "## Adapter Detections (which stack v2 picked primary)"
  echo
  echo '```json'
  if [[ -f "$V2_OUT/adapter_detections.json" ]]; then
    cat "$V2_OUT/adapter_detections.json"
  else
    echo "{}"
  fi
  echo '```'
  echo
  echo "## Coverage Baseline (TC-VAL-5 evidence)"
  echo
  if [[ -f "$V2_OUT/coverage_baseline.json" ]]; then
    python3 -c "
import json, sys
d = json.load(open('$V2_OUT/coverage_baseline.json'))
print(f'- {len(d)} coverage records')
tf = [r for r in d if r.get('path', '').startswith(('test_factory/', 'src/'))]
if tf:
    avg = sum(r.get('line_coverage', 0) for r in tf) / len(tf)
    print(f'- avg line coverage: {avg:.1f}%')
    print('- files below 80% line coverage:')
    for r in sorted(tf, key=lambda x: x.get('line_coverage', 0))[:10]:
        print(f'  - {r[\"path\"]} ({r.get(\"line_coverage\", 0):.1f}%)')
"
  fi
  echo
  echo "## Top Risk-Weighted Gaps (TC-CKPT-7 evidence, TC-CKPT-8 work batch source)"
  echo
  if [[ -f "$V2_OUT/test_gap_queue.json" ]]; then
    python3 -c "
import json, sys
d = json.load(open('$V2_OUT/test_gap_queue.json'))
items = d if isinstance(d, list) else d.get('items', d.get('queue', []))
print(f'- {len(items)} queue items')
print()
print('| Priority | Coverage Gap | File | Risk Score |')
print('|---:|---:|---|---:|')
for it in items[:10]:
    if isinstance(it, dict):
        path = it.get('path') or it.get('source_path') or it.get('file', '?')
        score = it.get('priority', it.get('risk_score', 0))
        gap = it.get('coverage_gap', it.get('line_coverage', 0))
        rs = it.get('risk_score', 0)
        print(f'| {score:.1f} | {gap:.1f}% | \`{path}\` | {rs:.1f} |')
"
  fi
  echo
  echo "## Exclusions (TC-CKPT-6 evidence)"
  echo
  if [[ -f "$V2_OUT/exclusions.json" ]]; then
    python3 -c "
import json
d = json.load(open('$V2_OUT/exclusions.json'))
if isinstance(d, list):
    print(f'- {len(d)} files excluded')
    for ex in d[:5]:
        print(f'  - {ex.get(\"path\", \"?\")}: {ex.get(\"rationale\", ex.get(\"reason\", \"?\"))}')
elif isinstance(d, dict):
    for k, v in d.items():
        print(f'- {k}: {v}')
"
  fi
  echo
  echo "## Source-Test Map (TC-VAL-21 coverage provenance)"
  echo
  if [[ -f "$V2_OUT/source_test_map.json" ]]; then
    python3 -c "
import json
d = json.load(open('$V2_OUT/source_test_map.json'))
items = d if isinstance(d, list) else d.get('records', d.get('items', []))
print(f'- {len(items)} source-test map records')
direct = sum(1 for it in items if isinstance(it, dict) and any('test' in (t or '').lower() for t in (it.get('candidate_tests') or [])))
print(f'- files with candidate tests: {direct}')
"
  fi
  echo
  echo "## Coverage Generation Status (only if --generate-coverage was passed)"
  echo
  if [[ -f "$V2_OUT/coverage_runs/generate.json" ]]; then
    python3 -c "
import json
d = json.load(open('$V2_OUT/coverage_runs/generate.json'))
print(f'- status: {d.get(\"status\")}')
print(f'- exit_code: {d.get(\"exit_code\")}')
print(f'- new_reports: {d.get(\"new_reports\", [])}')
if d.get('warning'):
    print(f'- warning: {d[\"warning\"][:200]}')
"
  else
    echo "- (not run; pre-existing coverage reports were used)"
  fi
  echo
  echo "## How the LLM Should Use This"
  echo
  echo "1. Read \`coverage_baseline.json\` for the per-file coverage table (TC-VAL-7)."
  echo "2. Read \`risk_scores.json\` for testability/risk factors (Phase 7 classification)."
  echo "3. Read \`test_gap_queue.json\` and take the top N (= MAX_FILES_PER_BATCH) as the work batch (TC-CKPT-8)."
  echo "4. For each work-batch file, read the matching \`ai_work_items/wi-<hash>.md\` — that's the per-file spec the LLM should implement tests against (TC-ITEM-N.N)."
  echo "5. After implementing tests, re-run \`test-factory run --repo . --out /tmp/v2-verify --generate-coverage --limit 50\` and diff \`coverage_baseline.json\` against this run (TC-VAL-2 / TC-VAL-RESULT-2)."
  echo
  echo "**DO NOT re-derive** stack, framework, or coverage values from manual grep. The whole point of this integration is that the deterministic core (v2) produces consistent evidence; the LLM only does test design and implementation."
} > "$SUMMARY"

echo
echo "[integrate-v2] summary: $SUMMARY"
echo "[integrate-v2] OK"
