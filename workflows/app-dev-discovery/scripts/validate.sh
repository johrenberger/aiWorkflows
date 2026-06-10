#!/usr/bin/env bash
# validate.sh — app-dev-discovery Phase 17 validation gate
#
# Usage:
#   ./validate.sh <workspace-dir> <repo-name> <yyyy-mm-dd>
#
# Exit 0 on pass, non-zero on fail. Writes results to
# <workspace-dir>/.openclaw/app-dev-discovery/16-final-validation.md

set -u

WORKSPACE_DIR="${1:-}"
REPO="${2:-}"
TODAY="${3:-$(date -u +%Y-%m-%d)}"

if [[ -z "$WORKSPACE_DIR" || -z "$REPO" ]]; then
  echo "Usage: $0 <workspace-dir> <repo-name> [yyyy-mm-dd]" >&2
  exit 2
fi

EVIDENCE_DIR="$WORKSPACE_DIR/.openclaw/app-dev-discovery"
REPORT="$EVIDENCE_DIR/16-final-validation.md"
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

# 1. Final doc exists
# Repo name casing can differ between the URL arg (capitalized as on GitHub)
# and the actual filename the agent writes (often lowercased). Match
# case-insensitively across all candidates to avoid false negatives.
REPO_LC="${REPO,,}"
TODAY_LC="${TODAY,,}"
FINAL_DOC_CANDIDATES=(
  "$WORKSPACE_DIR/docs/${TODAY}-${REPO}-app-dev-discovery.md"
  "$WORKSPACE_DIR/docs/${TODAY}-${REPO}-app-dev-discovery_cursor.md"
  "$WORKSPACE_DIR/docs/${TODAY_LC}-${REPO_LC}-app-dev-discovery.md"
  "$WORKSPACE_DIR/docs/${TODAY_LC}-${REPO_LC}-app-dev-discovery_cursor.md"
)
FOUND_DOC=""
for f in "${FINAL_DOC_CANDIDATES[@]}"; do
  if [[ -f "$f" ]]; then FOUND_DOC="$f"; break; fi
done
# fallback: glob (case-insensitive via shopt)
if [[ -z "$FOUND_DOC" ]]; then
  shopt -s nullglob nocaseglob
  for f in "$WORKSPACE_DIR"/docs/*-*-app-dev-discovery*.md; do
    # Filter to the right date prefix
    case "$(basename "$f")" in
      "${TODAY}"-*|${TODAY_LC}-*) FOUND_DOC="$f"; break ;;
    esac
  done
  shopt -u nocaseglob
fi
[[ -n "$FOUND_DOC" ]] && check "Final onboarding document exists" true || check "Final onboarding document exists" false

# 2. Required sections — match flexibly. Agents may number sections ("## 1. X"),
# use different casing, or vary the phrasing slightly. We look for either:
#   (a) the section name as a heading (with optional leading numbering), or
#   (b) the section name as standalone text (for prose mentions).
# This avoids the brittleness of exact grep -F on a single canonical string.
if [[ -n "$FOUND_DOC" ]]; then
  for section in \
    "README / Instruction Files Summary" \
    "Detailed Technology Stack" \
    "System Overview and Purpose" \
    "Project Structure and Reading Recommendations" \
    "Key Components" \
    "Execution and Data Flows" \
    "Database Schema Overview" \
    "Dependencies and Integrations" \
    "API Documentation" \
    "Architecture Diagrams" \
    "Testing" \
    "Error Handling and Logging" \
    "Security Considerations" \
    "Architecture Risks and Observations" \
    "Developer Productivity Guide" \
    "Build / Deploy / Infrastructure" \
    "ADR Baseline" \
    "Discovery Confidence and Unknowns"
  do
    # Escape regex metacharacters in the section name (slashes, dots, parens)
    esc="$(printf '%s' "$section" | sed 's/[][\.*^$/]/\\&/g')"
    # Match:  ## [N.|N.M.|Section] <section name>[suffix]
    # The section name must lead the heading (after optional numbering).
    # We do NOT fall back to prose matching — that gives false positives when
    # an agent mentions a section name in body text without actually having
    # the section.
    if grep -qE "^#+\s*([0-9]+(\.[0-9]+)*\.?\s+)?${esc}([ \t]*$|[ \t]+[(:].*$|[ \t]+-.*$)" "$FOUND_DOC"; then
      check "Section present: $section" true
    else
      check "Section present: $section" false
    fi
  done
fi

# 7. ADR files
[[ -f "$WORKSPACE_DIR/docs/adr/000-template.md" ]] && check "ADR-000 template exists" true || check "ADR-000 template exists" false
[[ -f "$WORKSPACE_DIR/docs/adr/001-current-architecture-baseline.md" ]] && check "ADR-001 baseline exists" true || check "ADR-001 baseline exists" false

# 8. Commit-pinned GitHub URLs present
if [[ -n "$FOUND_DOC" ]] && grep -qE 'https://github\.com/[^[:space:]]+/blob/[0-9a-f]{7,40}/' "$FOUND_DOC"; then
  check "Commit-pinned GitHub URLs present" true
else
  check "Commit-pinned GitHub URLs present" false
fi

# 9. Mermaid diagrams present
if [[ -n "$FOUND_DOC" ]] && grep -qE '```mermaid' "$FOUND_DOC"; then
  check "Mermaid diagrams present" true
else
  check "Mermaid diagrams present" false
fi

# 10. Confidence scoring
if [[ -n "$FOUND_DOC" ]] && grep -qiE 'Discovery Confidence|Overall Discovery Confidence' "$FOUND_DOC"; then
  check "Discovery confidence scoring present" true
else
  check "Discovery confidence scoring present" false
fi

# 11. Evidence files for recoverability
RECOV=0
for n in 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15; do
  if compgen -G "$EVIDENCE_DIR/${n}-*.md" >/dev/null; then
    RECOV=$((RECOV+1))
  fi
done
if [[ $RECOV -ge 14 ]]; then
  check "Evidence files for recoverability ($RECOV/16)" true
else
  check "Evidence files for recoverability ($RECOV/16)" false
fi

# 11b. Analyzer JSON outputs present (analyzer-accelerated workflow)
# These are the raw outputs the synthesizer consumes. Missing means the
# synthesizer was never run, which would invalidate the deterministic
# evidence backbone.
ANALYZER_OUT="$EVIDENCE_DIR/../analyzer-output"
ANALYZER_FILES=0
for f in analysis_manifest.json tech_stack.json routes.json dependencies.json \
          integrations.json repo_inventory.json tests.json db_schema.json \
          build_deploy.json error_logging.json security_signals.json \
          hygiene_findings.json contradiction_candidates.json project_structure.json \
          entry_points.json; do
  if [[ -f "$ANALYZER_OUT/$f" ]]; then
    ANALYZER_FILES=$((ANALYZER_FILES+1))
  fi
done
if [[ $ANALYZER_FILES -ge 14 ]]; then
  check "Analyzer JSON outputs present ($ANALYZER_FILES/15)" true
else
  check "Analyzer JSON outputs present ($ANALYZER_FILES/15)" false
fi

# 11c. LLM-only sections were filled in (not left as skeletons)
# The synthesizer injects `<!-- AGENT_FILL_REQUIRED -->` markers into
# files where the agent must write narrative content. The agent must
# remove these markers when filling in the section.
LLM_SKIPPED=0
for skel in 02-documentation-evidence.md 05-components-evidence.md 06-flows-evidence.md 14-risk-hygiene-evidence.md 15-contradiction-detection.md; do
  if [[ -f "$EVIDENCE_DIR/$skel" ]] && grep -qF '<!-- AGENT_FILL_REQUIRED -->' "$EVIDENCE_DIR/$skel"; then
    LLM_SKIPPED=$((LLM_SKIPPED+1))
  fi
done
if [[ $LLM_SKIPPED -eq 0 ]]; then
  check "LLM-only sections filled (no remaining AGENT_FILL_REQUIRED markers)" true
else
  check "LLM-only sections filled ($LLM_SKIPPED marker(s) remain)" false
fi

# 12. Filename format check
if [[ -n "$FOUND_DOC" ]]; then
  base="$(basename "$FOUND_DOC")"
  if [[ "$base" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-.+\-app-dev-discovery.*\.md$ ]]; then
    check "Filename format yyyy-mm-dd-<repo>-app-dev-discovery.md" true
  else
    check "Filename format yyyy-mm-dd-<repo>-app-dev-discovery.md" false
  fi
fi

# -------- write report --------
{
  echo "# Phase 17 — Final Validation"
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
