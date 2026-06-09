#!/usr/bin/env bash
# run.sh — repo-discovery-analyzer workflow runner
#
# Usage:
#   ./run.sh <github-repo-url> [--workspace <dir>] [--keep-temp] [--dry-run]
#
# Exit codes:
#   0  success
#   2  bad usage
#   3  repository acquisition failed
#   4  agent invocation failed
#   5  validation failed
#   6  commit/push failed (non-fatal in dry-run)

set -Eeuo pipefail

REPO_URL=""
WORKSPACE_DIR=""
KEEP_TEMP="false"
DRY_RUN="false"

usage() {
  sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) WORKSPACE_DIR="$2"; shift 2 ;;
    --keep-temp) KEEP_TEMP="true"; shift ;;
    --dry-run) DRY_RUN="true"; shift ;;
    -h|--help) usage ;;
    --*) echo "Unknown flag: $1" >&2; usage ;;
    *)
      if [[ -z "$REPO_URL" ]]; then
        REPO_URL="$1"
        shift
      else
        echo "Unexpected positional: $1" >&2
        usage
      fi
      ;;
  esac
done

if [[ -z "$REPO_URL" ]]; then
  usage
fi

REPO_URL="${REPO_URL%/}"

if [[ "$REPO_URL" =~ ^https?://github\.com/([^/]+)/([^/]+)$ ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
elif [[ "$REPO_URL" =~ ^git@github\.com:([^/]+)/([^/]+)\.git$ ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
else
  echo "ERROR: GITHUB_PROJECT_URL must look like https://github.com/<org>/<repo>" >&2
  exit 2
fi

if [[ -z "$WORKSPACE_DIR" ]]; then
  WORKSPACE_DIR="/tmp/${REPO}"
fi

WORKSPACE_DIR="$(cd "$(dirname "$WORKSPACE_DIR")" 2>/dev/null && pwd)/$(basename "$WORKSPACE_DIR")" || WORKSPACE_DIR="$WORKSPACE_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_FILE="$SCRIPT_DIR/prompt.md"
EVIDENCE_DIR=".openclaw/repo-discovery-analyzer"
TODAY="$(date -u +%Y-%m-%d)"

echo "→ repo-discovery-analyzer"
echo "  repo:      $OWNER/$REPO"
echo "  url:       $REPO_URL"
echo "  workspace: $WORKSPACE_DIR"
echo "  date:      $TODAY"
echo "  dry-run:   $DRY_RUN"
echo

echo "[Phase 0] Repository acquisition"
mkdir -p "$WORKSPACE_DIR"

if [[ -d "$WORKSPACE_DIR/.git" ]]; then
  cd "$WORKSPACE_DIR"
  git fetch --tags --prune origin || echo "  - fetch warnings (continuing)"
else
  TOKEN=""
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    TOKEN="$GITHUB_TOKEN"
  elif [[ -n "${GH_TOKEN:-}" ]]; then
    TOKEN="$GH_TOKEN"
  elif command -v gh >/dev/null 2>&1 && gh auth token >/dev/null 2>&1; then
    TOKEN="$(gh auth token 2>/dev/null || true)"
  fi

  if [[ -n "$TOKEN" ]]; then
    AUTH_URL="https://x-access-token:${TOKEN}@github.com/${OWNER}/${REPO}.git"
    if ! git -c credential.helper= clone --quiet "$AUTH_URL" "$WORKSPACE_DIR"; then
      echo "ERROR: git clone failed" >&2
      exit 3
    fi
    git -C "$WORKSPACE_DIR" remote set-url origin "https://github.com/${OWNER}/${REPO}.git"
  else
    if ! git clone --quiet "$REPO_URL" "$WORKSPACE_DIR"; then
      echo "ERROR: anonymous clone failed" >&2
      exit 3
    fi
  fi
  cd "$WORKSPACE_DIR"
fi

DEFAULT_BRANCH="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||' || true)"
if [[ -z "$DEFAULT_BRANCH" ]]; then
  DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk -F': ' '/HEAD branch/ {print $2}' || echo main)"
fi

git checkout "$DEFAULT_BRANCH" 2>/dev/null || git checkout main 2>/dev/null || git checkout master 2>/dev/null || true
git pull --ff-only 2>/dev/null || true

CURRENT_COMMIT="$(git rev-parse HEAD)"
BRANCH_NAME="feat/repo-discovery-analyzer-$TODAY"

mkdir -p "$WORKSPACE_DIR/$EVIDENCE_DIR"
shopt -s nullglob
for tmpl in "$SCRIPT_DIR"/templates/[0-9][0-9]-*.md; do
  cp "$tmpl" "$WORKSPACE_DIR/$EVIDENCE_DIR/"
done
shopt -u nullglob

cat > "$WORKSPACE_DIR/$EVIDENCE_DIR/00-run-metadata.md" <<EOF
# Run Metadata

- Repository: $OWNER/$REPO
- Remote URL: $REPO_URL
- Default branch: $DEFAULT_BRANCH
- Checked-out branch: $(git symbolic-ref --short HEAD 2>/dev/null || echo "$DEFAULT_BRANCH")
- Current commit: $CURRENT_COMMIT
- Commit-pinned URL prefix: https://github.com/$OWNER/$REPO/blob/$CURRENT_COMMIT/
- Run date: $TODAY
- Workspace: $WORKSPACE_DIR
- Workflow: repo-discovery-analyzer
EOF

AGENT_MESSAGE_FILE="$WORKSPACE_DIR/$EVIDENCE_DIR/00-agent-prompt.md"
{
  cat "$PROMPT_FILE"
  cat <<EOF

---

# Runtime Context

- GITHUB_PROJECT_URL=$REPO_URL
- WORKSPACE_DIR=$WORKSPACE_DIR
- EVIDENCE_DIR=$EVIDENCE_DIR
- TODAY=$TODAY
- DEFAULT_BRANCH=$DEFAULT_BRANCH
- CURRENT_COMMIT=$CURRENT_COMMIT
EOF
} > "$AGENT_MESSAGE_FILE"

if [[ "$DRY_RUN" == "true" ]]; then
  echo
  echo "[Dry-run] Skipping agent invocation."
  echo "Prompt file: $PROMPT_FILE"
  exit 0
fi

AGENT_MESSAGE="$(cat "$AGENT_MESSAGE_FILE")"
AGENT_OUTPUT_FILE="$WORKSPACE_DIR/$EVIDENCE_DIR/00-agent-output.txt"

if ! openclaw agent --agent main --local --timeout "${AGENT_TIMEOUT:-1800}" \
  --message "$AGENT_MESSAGE" > "$AGENT_OUTPUT_FILE" 2>&1; then
  echo "ERROR: agent invocation failed. See $AGENT_OUTPUT_FILE" >&2
  exit 4
fi

echo
echo "[Validation]"
if ! bash "$SCRIPT_DIR/scripts/validate.sh" "$WORKSPACE_DIR" "$REPO" "$TODAY"; then
  echo "ERROR: validation failed" >&2
  exit 5
fi

echo
echo "[Commit]"
cd "$WORKSPACE_DIR"
if ! git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
  git checkout -b "$BRANCH_NAME"
else
  SHORT_COMMIT="$(git rev-parse --short HEAD)"
  BRANCH_NAME="${BRANCH_NAME}-${SHORT_COMMIT}"
  git checkout -b "$BRANCH_NAME"
fi

git add .openclaw/tools/repo-discovery-analyzer 2>/dev/null || true
if ! git diff --cached --quiet; then
  git commit -m "feat: add repo discovery analyzer"
fi

if [[ "$KEEP_TEMP" != "true" ]]; then
  rm -rf "$WORKSPACE_DIR/$EVIDENCE_DIR"
fi

echo
echo "✅ repo-discovery-analyzer complete"
echo "  branch: $BRANCH_NAME"
echo "  commit: $(git rev-parse --short HEAD)"
