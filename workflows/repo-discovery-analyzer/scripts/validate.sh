#!/usr/bin/env bash
# validate.sh — repo-discovery-analyzer workflow validator

set -u

WORKSPACE_DIR="${1:-}"
REPO="${2:-}"
TODAY="${3:-$(date -u +%Y-%m-%d)}"

if [[ -z "$WORKSPACE_DIR" || -z "$REPO" ]]; then
  echo "Usage: $0 <workspace-dir> <repo-name> [yyyy-mm-dd]" >&2
  exit 2
fi

EVIDENCE_DIR="$WORKSPACE_DIR/.openclaw/repo-discovery-analyzer"
REPORT="$EVIDENCE_DIR/02-validation-checklist.md"
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

BASE="$WORKSPACE_DIR/.openclaw/tools/repo-discovery-analyzer"
check "Implementation directory exists" "$( [[ -d "$BASE" ]] && echo true || echo false )"

REQUIRED_PATHS=(
  "README.md"
  "repo_discovery_analyzer/__init__.py"
  "repo_discovery_analyzer/cli.py"
  "repo_discovery_analyzer/model.py"
  "repo_discovery_analyzer/io_utils.py"
  "repo_discovery_analyzer/github_links.py"
  "repo_discovery_analyzer/inventory.py"
  "repo_discovery_analyzer/loc_metrics.py"
  "repo_discovery_analyzer/detectors/__init__.py"
  "repo_discovery_analyzer/detectors/stack.py"
  "repo_discovery_analyzer/detectors/entry_points.py"
  "repo_discovery_analyzer/detectors/java_spring.py"
  "repo_discovery_analyzer/detectors/javascript.py"
  "repo_discovery_analyzer/detectors/database.py"
  "repo_discovery_analyzer/detectors/dependencies.py"
  "repo_discovery_analyzer/detectors/testing.py"
  "repo_discovery_analyzer/detectors/security.py"
  "repo_discovery_analyzer/detectors/error_logging.py"
  "repo_discovery_analyzer/detectors/build_deploy.py"
  "repo_discovery_analyzer/detectors/hygiene.py"
  "repo_discovery_analyzer/detectors/contradictions.py"
  "validation.py"
  "tests/test_cli.py"
  "tests/test_github_links.py"
  "tests/test_inventory.py"
  "tests/test_java_spring_routes.py"
  "tests/test_javascript_routes.py"
  "tests/test_security_redaction.py"
  "tests/test_validation.py"
  "pyproject.toml"
)

for rel in "${REQUIRED_PATHS[@]}"; do
  check "Exists: $rel" "$( [[ -e "$BASE/$rel" ]] && echo true || echo false )"
done

{
  echo "# Validation Checklist"
  echo
  echo "- Workspace: $WORKSPACE_DIR"
  echo "- Repo: $REPO"
  echo "- Date: $TODAY"
  echo
  echo "| Check | Status |"
  echo "| --- | --- |"
  for r in "${RESULTS[@]}"; do echo "$r"; done
  echo
  echo "- PASS: $PASS"
  echo "- FAIL: $FAIL"
} > "$REPORT"

echo "Validation: PASS=$PASS FAIL=$FAIL"
echo "Report:     $REPORT"

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
