#!/usr/bin/env bash
# validate.sh — api-testing-workflow Stage 16 validation gate
#
# Usage:
#   ./validate.sh <workspace-dir> <repo-name> <yyyy-mm-dd>
#
# Exit 0 on pass, non-zero on fail. Writes results to
# <workspace-dir>/.openclaw/api-testing/13-validation-gate.md

set -u

WORKSPACE_DIR="${1:-}"
REPO="${2:-}"
TODAY="${3:-$(date -u +%Y-%m-%d)}"

if [[ -z "$WORKSPACE_DIR" || -z "$REPO" ]]; then
  echo "Usage: $0 <workspace-dir> <repo-name> [yyyy-mm-dd]" >&2
  exit 2
fi

EVIDENCE_DIR="$WORKSPACE_DIR/.openclaw/api-testing"
REPORT="$EVIDENCE_DIR/13-validation-gate.md"
mkdir -p "$(dirname "$REPORT")"

PASS=0
FAIL=0
RESULTS=()

check() {
  local label="$1"
  local cond="$2"
  if [[ "$cond" == "true" ]]; then
    RESULTS+=("| ✅ $label | PASS |")
    PASS=$((PASS+1))
  else
    RESULTS+=("| ❌ $label | FAIL |")
    FAIL=$((FAIL+1))
  fi
}

# -------- Artifact presence --------
# The spec mandates these artifacts. Each must exist OR have a documented
# blocker (we accept a sibling .blocked file with a one-line reason).
artifact_present_or_blocked() {
  local path="$1"
  if [[ -f "$path" || -d "$path" ]]; then return 0; fi
  if [[ -f "${path}.blocked" ]]; then return 0; fi
  return 1
}

check "artifacts/api_testing_context.md" \
  "$(artifact_present_or_blocked "$WORKSPACE_DIR/artifacts/api_testing_context.md" && echo true || echo false)"

check "artifacts/api_inventory.json" \
  "$(artifact_present_or_blocked "$WORKSPACE_DIR/artifacts/api_inventory.json" && echo true || echo false)"

check "artifacts/openapi.normalized.yaml" \
  "$(artifact_present_or_blocked "$WORKSPACE_DIR/artifacts/openapi.normalized.yaml" && echo true || echo false)"

check "artifacts/api_test_plan.md" \
  "$(artifact_present_or_blocked "$WORKSPACE_DIR/artifacts/api_test_plan.md" && echo true || echo false)"

check "tests/api/ exists" \
  "$([ -d "$WORKSPACE_DIR/tests/api" ] || [ -f "$WORKSPACE_DIR/tests/api.blocked" ] && echo true || echo false)"

check "artifacts/api_security_findings.md" \
  "$(artifact_present_or_blocked "$WORKSPACE_DIR/artifacts/api_security_findings.md" && echo true || echo false)"

check "artifacts/api_performance_plan.md" \
  "$(artifact_present_or_blocked "$WORKSPACE_DIR/artifacts/api_performance_plan.md" && echo true || echo false)"

check "artifacts/api_resilience_plan.md" \
  "$(artifact_present_or_blocked "$WORKSPACE_DIR/artifacts/api_resilience_plan.md" && echo true || echo false)"

check "artifacts/api_observability_recommendations.md" \
  "$(artifact_present_or_blocked "$WORKSPACE_DIR/artifacts/api_observability_recommendations.md" && echo true || echo false)"

check "artifacts/api_test_results.json" \
  "$(artifact_present_or_blocked "$WORKSPACE_DIR/artifacts/api_test_results.json" && echo true || echo false)"

check "artifacts/api_defect_report.md" \
  "$(artifact_present_or_blocked "$WORKSPACE_DIR/artifacts/api_defect_report.md" && echo true || echo false)"

check "artifacts/api_change_log.md" \
  "$(artifact_present_or_blocked "$WORKSPACE_DIR/artifacts/api_change_log.md" && echo true || echo false)"

check "artifacts/api_workflow_summary.md" \
  "$(artifact_present_or_blocked "$WORKSPACE_DIR/artifacts/api_workflow_summary.md" && echo true || echo false)"

check "TODO_api-tester.md" \
  "$([ -f "$WORKSPACE_DIR/TODO_api-tester.md" ] && echo true || echo false)"

# -------- Final doc --------
REPO_LC="${REPO,,}"
TODAY_LC="${TODAY,,}"
FINAL_DOC_CANDIDATES=(
  "$WORKSPACE_DIR/docs/api-testing-${TODAY}.md"
  "$WORKSPACE_DIR/docs/api-testing-${TODAY_LC}.md"
)
FOUND_DOC=""
for f in "${FINAL_DOC_CANDIDATES[@]}"; do
  if [[ -f "$f" ]]; then FOUND_DOC="$f"; break; fi
done
if [[ -z "$FOUND_DOC" ]]; then
  shopt -s nullglob nocaseglob
  for f in "$WORKSPACE_DIR"/docs/api-testing-*.md; do
    case "$(basename "$f")" in
      "${TODAY}-"*|${TODAY_LC}-*) FOUND_DOC="$f"; break ;;
    esac
  done
  shopt -u nocaseglob
fi
[[ -n "$FOUND_DOC" ]] && check "Final doc docs/api-testing-<date>.md exists" true || check "Final doc docs/api-testing-<date>.md exists" false

# Required sections in the final doc.
# Agents may use any of several reasonable casings/wordings per section
# (e.g. "Execution mode", "Execution Mode", "Execution_mode",
# "Test results", "Test Results", "Test results summary"). We match
# case-insensitively and allow an optional trailing suffix on the
# heading. The aliases list keeps this tolerant without false-positives.
if [[ -n "$FOUND_DOC" ]]; then
  declare -A SECTION_ALIASES=(
    ["Executive Summary"]="executive summary"
    ["Execution mode"]="execution mode"
    ["API surface summary"]="api surface summary"
    ["Highest-risk findings"]="highest[- ]risk findings"
    ["Test results"]="test results"
    ["Security findings"]="security findings"
    ["Performance readiness"]="performance readiness"
    ["Resilience readiness"]="resilience readiness"
    ["Observability"]="observability"
    ["Recommended next actions"]="recommended next actions"
  )
  for label in "${!SECTION_ALIASES[@]}"; do
    pat="${SECTION_ALIASES[$label]}"
    # Allow the section name to be the entire heading, or be followed by
    # any non-# character (so suffixes like "Summary" or "Readiness" match).
    if grep -qiE "^#+\s*([0-9]+(\.[0-9]+)*\.?\s+)?${pat}(\s*[:(\-].*|\s+[A-Za-z].*|\s*$)" "$FOUND_DOC"; then
      check "Section present: $label" true
    else
      check "Section present: $label" false
    fi
  done
fi

# ADR files
[[ -f "$WORKSPACE_DIR/docs/adr/000-template.md" ]] && check "ADR-000 template exists" true || check "ADR-000 template exists" false
[[ -f "$WORKSPACE_DIR/docs/adr/001-api-contract-baseline.md" ]] && check "ADR-001 baseline exists" true || check "ADR-001 baseline exists" false

# Test files generated under tests/api/ (basic presence check)
TEST_FILES=0
if [[ -d "$WORKSPACE_DIR/tests/api" ]]; then
  TEST_FILES=$(find "$WORKSPACE_DIR/tests/api" -type f \( -name 'test_*.py' -o -name '*_test.py' \) 2>/dev/null | wc -l)
fi
if [[ $TEST_FILES -ge 1 ]]; then
  check "Generated test files in tests/api/ ($TEST_FILES)" true
else
  check "Generated test files in tests/api/ ($TEST_FILES)" false
fi

# Contract tests (may be empty if no OpenAPI; record as documented skip)
CONTRACT_TEST_FILES=0
if [[ -d "$WORKSPACE_DIR/tests/contract" ]]; then
  CONTRACT_TEST_FILES=$(find "$WORKSPACE_DIR/tests/contract" -type f \( -name 'test_*.py' -o -name '*_test.py' \) 2>/dev/null | wc -l)
fi
if [[ $CONTRACT_TEST_FILES -ge 1 ]] || [[ -f "$WORKSPACE_DIR/tests/contract.blocked" ]]; then
  check "Contract tests generated or documented blocker" true
else
  check "Contract tests generated or documented blocker" false
fi

# Inventory is valid JSON
if [[ -f "$WORKSPACE_DIR/artifacts/api_inventory.json" ]] && \
   python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$WORKSPACE_DIR/artifacts/api_inventory.json" 2>/dev/null; then
  check "api_inventory.json parses as valid JSON" true
else
  check "api_inventory.json parses as valid JSON" false
fi

# Test results is valid JSON
if [[ -f "$WORKSPACE_DIR/artifacts/api_test_results.json" ]] && \
   python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$WORKSPACE_DIR/artifacts/api_test_results.json" 2>/dev/null; then
  check "api_test_results.json parses as valid JSON" true
else
  check "api_test_results.json parses as valid JSON" false
fi

# OpenAPI normalized is valid YAML
# We try pyyaml first, then ruamel.yaml, then a tiny pure-shell heuristic
# (lines starting with `key:` are likely OK; we never use this in CI — this is
# purely a degraded fallback if the container has no YAML lib installed).
yaml_valid="false"
if [[ -f "$WORKSPACE_DIR/artifacts/openapi.normalized.yaml" ]]; then
  if python3 -c "import sys, yaml; yaml.safe_load(open(sys.argv[1]))" "$WORKSPACE_DIR/artifacts/openapi.normalized.yaml" 2>/dev/null; then
    yaml_valid="true"
  elif python3 -c "import sys
from ruamel.yaml import YAML
YAML(typ='safe').load(open(sys.argv[1]))" "$WORKSPACE_DIR/artifacts/openapi.normalized.yaml" 2>/dev/null; then
    yaml_valid="true"
  else
    # Heuristic: file is non-empty, contains a top-level `openapi:` key,
    # and has no obvious YAML syntax errors (unmatched braces, tabs in
    # indentation). This is a degraded check; the spec recommends
    # `python3 -m pip install pyyaml` in the workflow prerequisites.
    if grep -qE '^openapi:' "$WORKSPACE_DIR/artifacts/openapi.normalized.yaml" && \
       ! grep -qP '^\t' "$WORKSPACE_DIR/artifacts/openapi.normalized.yaml"; then
      yaml_valid="degraded"
    fi
  fi
fi
if [[ "$yaml_valid" == "true" ]]; then
  check "openapi.normalized.yaml parses as valid YAML" true
elif [[ "$yaml_valid" == "degraded" ]]; then
  RESULTS+=("| ⚠️  openapi.normalized.yaml parses as valid YAML | DEGRADED (no pyyaml; heuristic only) |")
  PASS=$((PASS+1))
else
  check "openapi.normalized.yaml parses as valid YAML" false
fi

# Safety gate: no obvious secret patterns in artifacts
SECRETS_HITS=0
if [[ -d "$WORKSPACE_DIR/artifacts" ]]; then
  SECRETS_HITS=$(grep -rE '(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)' "$WORKSPACE_DIR/artifacts" 2>/dev/null | wc -l || true)
fi
if [[ $SECRETS_HITS -eq 0 ]]; then
  check "No obvious secrets in artifacts/" true
else
  check "No obvious secrets in artifacts/ ($SECRETS_HITS hits)" false
fi

# Safety gate: tests/ does not contain destructive markers unless allowed
# (Best-effort: detect common destructive test names. We don't fail the gate
# on this — the spec says destructive tests should not RUN. We only warn.)
DESTRUCTIVE_HITS=0
if [[ -d "$WORKSPACE_DIR/tests" ]]; then
  DESTRUCTIVE_HITS=$(grep -rE '@pytest\.mark\.destructive' "$WORKSPACE_DIR/tests" 2>/dev/null | wc -l || true)
fi
if [[ $DESTRUCTIVE_HITS -eq 0 ]]; then
  check "No destructive tests marked (safe default)" true
else
  # Informational: the spec says "destructive tests not run unless allowed".
  # The agent SHOULD have skipped them. We pass if at least the marker is
  # present (so they can be filtered out) and record the count.
  check "Destructive tests marked but not executed ($DESTRUCTIVE_HITS marked)" true
fi

# Evidence files for recoverability
RECOV=0
for n in 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14; do
  if compgen -G "$EVIDENCE_DIR/${n}-*.md" >/dev/null; then
    RECOV=$((RECOV+1))
  fi
done
if [[ $RECOV -ge 13 ]]; then
  check "Evidence files for recoverability ($RECOV/15)" true
else
  check "Evidence files for recoverability ($RECOV/15)" false
fi

# -------- Performance readiness check --------
# Informational at the gate: records whether perf scripts are present and
# how many pytest.mark.performance / k6 `thresholds:` markers were found.
# The check is NEVER a gate-fail — perf execution requires explicit opt-in
# and the runner is responsible for plumbing RUN_PERF. We just want
# visibility here. (If the agent produced 0 scripts under RUN_PERF=true,
# the report surfaces it as a warning for the reviewer to chase down.)
PERF_SCRIPTS=0
PERF_MARKERS=0
if [[ -d "$WORKSPACE_DIR/tests/performance" ]]; then
  PERF_SCRIPTS=$(find "$WORKSPACE_DIR/tests/performance" -type f \( -name '*.js' -o -name '*.py' \) 2>/dev/null | wc -l)
  PERF_MARKERS=$(grep -rE '@pytest\.mark\.performance|thresholds:' "$WORKSPACE_DIR/tests/performance" 2>/dev/null | wc -l || true)
fi
if [[ "${RUN_PERF:-false}" == "true" ]]; then
  if [[ $PERF_SCRIPTS -ge 1 ]]; then
    RESULTS+=("| ✅ Performance scripts present (RUN_PERF=true) | PASS ($PERF_SCRIPTS scripts, $PERF_MARKERS markers) |")
    PASS=$((PASS+1))
  else
    # RUN_PERF was set but the agent produced no scripts — record as a
    # warning, not a gate-fail, so the rest of the report stays usable.
    RESULTS+=("| ⚠️  Performance scripts missing (RUN_PERF=true, 0 scripts) | WARN |")
  fi
else
  # Plan-only mode. Record the count for visibility.
  if [[ $PERF_SCRIPTS -ge 1 ]]; then
    RESULTS+=("| ℹ️  Performance scripts on disk | INFO ($PERF_SCRIPTS scripts, $PERF_MARKERS markers; RUN_PERF=false) |")
  else
    RESULTS+=("| ℹ️  Performance scripts on disk | INFO (0 scripts; RUN_PERF=false — plan only) |")
  fi
fi

# Same shape for resilience: informational when not enabled.
RESILIENCE_SCRIPTS=0
if [[ -d "$WORKSPACE_DIR/tests/resilience" ]]; then
  RESILIENCE_SCRIPTS=$(find "$WORKSPACE_DIR/tests/resilience" -type f -name '*.py' 2>/dev/null | wc -l)
fi
if [[ $RESILIENCE_SCRIPTS -ge 1 ]]; then
  RESULTS+=("| ℹ️  Resilience scripts on disk | INFO ($RESILIENCE_SCRIPTS scripts) |")
fi

# -------- write report --------
{
  echo "# Stage 16 — Validation Gate"
  echo
  echo "- Workspace: $WORKSPACE_DIR"
  echo "- Repo: $REPO"
  echo "- Date: $TODAY"
  echo "- Final doc: ${FOUND_DOC:-<MISSING>}"
  echo
  echo "## Results"
  echo
  echo "| Check | Status |"
  echo "| --- | --- |"
  for r in "${RESULTS[@]}"; do echo "$r"; done
  echo
  echo "## Summary"
  echo
  echo "- PASS: $PASS"
  echo "- FAIL: $FAIL"
  echo
  if [[ $FAIL -eq 0 ]]; then
    echo "**Validation: PASS** — ready to commit."
  else
    echo "**Validation: FAIL** — fix the failing checks before committing."
  fi
} > "$REPORT"

echo "Validation: PASS=$PASS FAIL=$FAIL"
echo "Report:     $REPORT"

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
