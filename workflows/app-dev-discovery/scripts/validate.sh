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
FINAL_DOC_CANDIDATES=(
  "$WORKSPACE_DIR/docs/${TODAY}-${REPO}-app-dev-discovery.md"
  "$WORKSPACE_DIR/docs/${TODAY}-${REPO}-app-dev-discovery_cursor.md"
)
FOUND_DOC=""
for f in "${FINAL_DOC_CANDIDATES[@]}"; do
  if [[ -f "$f" ]]; then FOUND_DOC="$f"; break; fi
done
# fallback: glob
if [[ -z "$FOUND_DOC" ]]; then
  FOUND_DOC="$(ls "$WORKSPACE_DIR"/docs/*-"${REPO}"*-app-dev-discovery*.md 2>/dev/null | head -1 || true)"
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
