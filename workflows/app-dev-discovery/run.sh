#!/usr/bin/env bash
# run.sh — app-dev-discovery workflow runner
#
# Usage:
#   ./run.sh <github-repo-url> [--workspace <dir>] [--keep-temp] [--dry-run] [--no-agent]
#
# Examples:
#   ./run.sh https://github.com/foo/bar
#   ./run.sh https://github.com/foo/bar --workspace /tmp/discover --keep-temp
#   ./run.sh https://github.com/foo/bar --dry-run    # scaffold + emit prompt only
#
# Exit codes:
#   0  success
#   2  bad usage
#   3  repository acquisition failed
#   4  agent invocation failed
#   5  validation failed
#   6  commit/push failed (non-fatal in dry-run)

set -Eeuo pipefail

# -------- argument parsing --------
REPO_URL=""
WORKSPACE_DIR=""
KEEP_TEMP="false"
DRY_RUN="false"
NO_AGENT="false"

usage() {
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) WORKSPACE_DIR="$2"; shift 2 ;;
    --keep-temp) KEEP_TEMP="true"; shift ;;
    --dry-run)   DRY_RUN="true"; shift ;;
    --no-agent)  NO_AGENT="true"; shift ;;
    -h|--help)   usage ;;
    --*) echo "Unknown flag: $1" >&2; usage ;;
    *)
      if [[ -z "$REPO_URL" ]]; then REPO_URL="$1"; shift
      else echo "Unexpected positional: $1" >&2; usage
      fi
      ;;
  esac
done

if [[ -z "$REPO_URL" ]]; then usage; fi

# Normalize URL: strip trailing slash
REPO_URL="${REPO_URL%/}"

# Extract owner/repo
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

# Default workspace — keep analysis isolated from the agent's CWD.
# Putting it in /tmp avoids contaminating the agent's own workspace
# and prevents the agent from confusing target-repo files with its own.
if [[ -z "$WORKSPACE_DIR" ]]; then
  WORKSPACE_DIR="/tmp/${REPO}"
fi

# Resolve to absolute path
WORKSPACE_DIR="$(cd "$(dirname "$WORKSPACE_DIR")" 2>/dev/null && pwd)/$(basename "$WORKSPACE_DIR")" || WORKSPACE_DIR="$WORKSPACE_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_FILE="$SCRIPT_DIR/prompt.md"
EVIDENCE_DIR=".openclaw/app-dev-discovery"
TODAY="$(date -u +%Y-%m-%d)"

echo "→ app-dev-discovery"
echo "  repo:     $OWNER/$REPO"
echo "  url:      $REPO_URL"
echo "  workspace: $WORKSPACE_DIR"
echo "  date:     $TODAY"
echo "  dry-run:  $DRY_RUN"
echo

# -------- Phase 0: repository acquisition --------
echo "[Phase 0] Repository acquisition"
mkdir -p "$WORKSPACE_DIR"

if [[ -d "$WORKSPACE_DIR/.git" ]]; then
  echo "  - already cloned, verifying remote"
  cd "$WORKSPACE_DIR"
  EXISTING_REMOTE="$(git remote get-url origin 2>/dev/null || true)"
  if [[ -n "$EXISTING_REMOTE" && "$EXISTING_REMOTE" != *"$OWNER/$REPO"* ]]; then
    echo "ERROR: existing remote $EXISTING_REMOTE does not match $REPO_URL" >&2
    exit 3
  fi
  git fetch --tags --prune origin || echo "  - fetch warnings (continuing)"
else
  echo "  - cloning $REPO_URL"
  # Token resolution order (in priority order):
  #   1. $GITHUB_TOKEN env var (preferred)
  #   2. $GH_TOKEN env var (gh-cli convention)
  #   3. `gh auth token` (gh's hosts.yml store, may be stale)
  #   4. anonymous (public repos only)
  #
  # SECURITY: We never let git's credential helper run during this workflow,
  # because the global helper is `!gh auth git-credential`, which injects the
  # token onto the git-remote-https cmdline and exposes it via `ps`. We always
  # use -c credential.helper= to suppress the helper.
  TOKEN=""
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    TOKEN="$GITHUB_TOKEN"
    echo "  - using GITHUB_TOKEN from env"
  elif [[ -n "${GH_TOKEN:-}" ]]; then
    TOKEN="$GH_TOKEN"
    echo "  - using GH_TOKEN from env"
  elif command -v gh >/dev/null 2>&1 && gh auth token >/dev/null 2>&1; then
    TOKEN=$(gh auth token 2>/dev/null || true)
    echo "  - using gh auth token (hosts.yml)"
  fi

  if [[ -n "$TOKEN" ]]; then
    AUTH_URL="https://x-access-token:${TOKEN}@github.com/${OWNER}/${REPO}.git"
    if ! git -c credential.helper= clone --quiet "$AUTH_URL" "$WORKSPACE_DIR" 2>/tmp/clone.err; then
      echo "ERROR: git clone failed:" >&2
      sed -i "s|x-access-token:[^@]*@|x-access-token:REDACTED@|g" /tmp/clone.err 2>/dev/null
      cat /tmp/clone.err >&2
      rm -f /tmp/clone.err
      exit 3
    fi
    rm -f /tmp/clone.err
    # Rewrite origin to the public form so the token isn't kept in .git/config
    git -C "$WORKSPACE_DIR" remote set-url origin "https://github.com/${OWNER}/${REPO}.git"
  else
    echo "  - no token available, attempting anonymous clone (public repos only)"
    if ! git clone --quiet "$REPO_URL" "$WORKSPACE_DIR" 2>/tmp/clone.err; then
      echo "ERROR: anonymous clone failed. Repo is private and no token is configured." >&2
      cat /tmp/clone.err >&2
      rm -f /tmp/clone.err
      exit 3
    fi
    rm -f /tmp/clone.err
  fi
  cd "$WORKSPACE_DIR"
fi

# Determine default branch
DEFAULT_BRANCH="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||' || true)"
if [[ -z "$DEFAULT_BRANCH" ]]; then
  DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk -F': ' '/HEAD branch/ {print $2}' || echo main)"
fi

# Check out default branch (non-destructive)
git checkout "$DEFAULT_BRANCH" 2>/dev/null || git checkout main 2>/dev/null || git checkout master 2>/dev/null || true
git pull --ff-only 2>/dev/null || echo "  - pull skipped (non-ff or no upstream)"

CURRENT_COMMIT="$(git rev-parse HEAD)"
BRANCH_NAME="docs/app-dev-discovery-$TODAY"

# -------- Scaffold evidence directory --------
echo "[Scaffold] $EVIDENCE_DIR"
mkdir -p "$WORKSPACE_DIR/$EVIDENCE_DIR"

# Copy blank templates (Phase 1+ agents fill these in)
shopt -s nullglob
for tmpl in "$SCRIPT_DIR"/templates/[0-9][0-9]-*.md; do
  cp "$tmpl" "$WORKSPACE_DIR/$EVIDENCE_DIR/"
done
shopt -u nullglob

# Write Phase 0 metadata
cat > "$WORKSPACE_DIR/$EVIDENCE_DIR/00-run-metadata.md" <<EOF
# Phase 0 — Run Metadata

- **Repository:** $OWNER/$REPO
- **Remote URL:** $REPO_URL
- **Default branch:** $DEFAULT_BRANCH
- **Checked-out branch:** $(git symbolic-ref --short HEAD 2>/dev/null || echo "$DEFAULT_BRANCH")
- **Current commit:** $CURRENT_COMMIT
- **Commit-pinned URL prefix:** https://github.com/$OWNER/$REPO/blob/$CURRENT_COMMIT/
- **Run date:** $TODAY
- **Workspace:** $WORKSPACE_DIR
- **Workflow:** app-dev-discovery
EOF

echo "  - metadata written to $EVIDENCE_DIR/00-run-metadata.md"

# -------- Phase 0.5: Analyzer-accelerated evidence synthesis --------
#
# Run the repo-discovery-analyzer over the target repo and use the
# synthesize-evidence.sh script to convert the JSON outputs into the
# 16 evidence markdown templates. This pre-computes ~80% of the
# evidence deterministically, leaving the agent to focus on narrative
# synthesis, Mermaid diagrams, and risk interpretation.
ANALYZER_OUT="$WORKSPACE_DIR/.openclaw/analyzer-output"
SYNTHESIZER="$SCRIPT_DIR/scripts/synthesize-evidence.sh"

if [[ -f "$SYNTHESIZER" ]]; then
  echo
  echo "[Phase 0.5] Analyzer-accelerated evidence synthesis"
  if bash "$SYNTHESIZER" \
      "$WORKSPACE_DIR" \
      "$ANALYZER_OUT" \
      "$WORKSPACE_DIR/$EVIDENCE_DIR" \
      "$OWNER" "$REPO" "$CURRENT_COMMIT" 2>&1 | tail -20; then
    echo "  - synthesizer complete"
  else
    echo "WARNING: synthesizer failed; agent will need to discover evidence manually" >&2
  fi
else
  echo "WARN: synthesizer not found at $SYNTHESIZER — falling back to agent-only mode" >&2
fi

# -------- Agent invocation (or prompt-only) --------
if [[ "$NO_AGENT" == "true" || "$DRY_RUN" == "true" ]]; then
  echo
  echo "[Dry-run] Skipping agent invocation."
  echo "  Prompt file: $PROMPT_FILE"
  echo "  To execute manually:"
  echo "    openclaw agent --agent main --local --timeout 1800 \\"
  echo "      --message \"\$(cat $PROMPT_FILE)\""
  echo
  echo "  Scaffolding complete. Exiting."
  exit 0
fi

echo
echo "[Agent] Invoking agent with prompt.md"
echo "  (Use --dry-run to scaffold without invoking)"

# Build the message: prompt + a small tail telling the agent the runtime context
AGENT_MESSAGE="$(cat "$PROMPT_FILE")

---

# Runtime Context (provided by run.sh)

- GITHUB_PROJECT_URL=$REPO_URL
- WORKSPACE_DIR=$WORKSPACE_DIR
- EVIDENCE_DIR=$EVIDENCE_DIR
- TODAY=$TODAY
- DEFAULT_BRANCH=$DEFAULT_BRANCH
- CURRENT_COMMIT=$CURRENT_COMMIT
- COMMIT_PINNED_PREFIX=https://github.com/$OWNER/$REPO/blob/$CURRENT_COMMIT/

You are operating inside $WORKSPACE_DIR. Follow the phases in this prompt sequentially.
When finished, the runner will handle branch creation, commit, and push. Just produce
the final docs/ artifacts and write a summary of: final doc path, ADR paths,
validation status, top 5 files to read first, unknowns.
"

# Save the message to disk for audit
echo "$AGENT_MESSAGE" > "$WORKSPACE_DIR/$EVIDENCE_DIR/00-agent-prompt.md"

# Invoke the agent. In OpenClaw 2026.5.x, --message alone is not enough — we
# need to pick a session. We use --agent main --local for fire-and-forget
# batch work: the agent runs to completion in this process, prints its reply
# to stdout, and we capture it. --timeout extends the default 600s window
# since 18 phases of repo analysis can take a while.
AGENT_OUTPUT_FILE="$WORKSPACE_DIR/$EVIDENCE_DIR/00-agent-output.txt"
AGENT_TIMEOUT="${AGENT_TIMEOUT:-1800}"  # 30 min default

if ! openclaw agent --agent main --local --timeout "$AGENT_TIMEOUT" \
     --message "$AGENT_MESSAGE" > "$AGENT_OUTPUT_FILE" 2>&1; then
  echo "WARNING: agent exited non-zero. Checking if deliverables are on disk anyway..." >&2
  # Some OpenClaw embedded-agent runs hit a session-takeover race during
  # cleanup (EmbeddedAttemptSessionTakeoverError) AFTER all the work has
  # been written. Treat the run as successful if the final doc exists and
  # validation passed; only fail if deliverables are missing.
  if [[ ! -f "$WORKSPACE_DIR/docs/${TODAY}-${REPO}-app-dev-discovery.md" ]] \
     && ! ls "$WORKSPACE_DIR/docs/${TODAY}-${REPO}"*-app-dev-discovery*.md >/dev/null 2>&1; then
    echo "ERROR: agent invocation failed AND no final doc was produced. See $AGENT_OUTPUT_FILE" >&2
    exit 4
  fi
  echo "  - deliverables found on disk; treating as success despite agent cleanup error"
fi

echo "  - agent output: $AGENT_OUTPUT_FILE"

# -------- Phase 17 validation --------
echo
echo "[Phase 17] Validation gate"
if ! bash "$SCRIPT_DIR/scripts/validate.sh" "$WORKSPACE_DIR" "$REPO" "$TODAY"; then
  echo "ERROR: validation failed. Inspect $WORKSPACE_DIR/$EVIDENCE_DIR/16-final-validation.md" >&2
  exit 5
fi

# -------- Phase 18 commit --------
echo
echo "[Phase 18] Commit"
cd "$WORKSPACE_DIR"

# Determine final doc path
# Try a few casings — the agent may have lowercased the repo segment.
REPO_LC="${REPO,,}"
TODAY_LC="${TODAY,,}"
FINAL_DOC=""
for cand in \
  "docs/${TODAY}-${REPO}-app-dev-discovery.md" \
  "docs/${TODAY}-${REPO}-app-dev-discovery_cursor.md" \
  "docs/${TODAY_LC}-${REPO_LC}-app-dev-discovery.md" \
  "docs/${TODAY_LC}-${REPO_LC}-app-dev-discovery_cursor.md"
do
  if [[ -f "$cand" ]]; then FINAL_DOC="$cand"; break; fi
done
# Last-resort: case-insensitive glob
if [[ -z "$FINAL_DOC" ]]; then
  shopt -s nullglob nocaseglob
  for f in docs/*-*-app-dev-discovery*.md; do
    case "$(basename "$f")" in
      "${TODAY}"-*|"${TODAY_LC}"-*) FINAL_DOC="$f"; break ;;
    esac
  done
  shopt -u nocaseglob
fi

if [[ -z "$FINAL_DOC" || ! -f "$FINAL_DOC" ]]; then
  echo "ERROR: final document not found in docs/ (tried multiple casings)" >&2
  ls docs/ >&2
  exit 5
fi

# Check branch collision
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
  SHORT_COMMIT="$(git rev-parse --short HEAD)"
  BRANCH_NAME="${BRANCH_NAME}-${SHORT_COMMIT}"
fi

git checkout -b "$BRANCH_NAME"
git add docs/
if git diff --cached --quiet; then
  echo "  - no doc changes to commit"
else
  git commit -m "docs: generate developer discovery guide

Generated by app-dev-discovery workflow on $TODAY.
Target: $OWNER/$REPO @ $CURRENT_COMMIT"
fi

# Push (best effort, with the same token resolution as the clone).
#
# SECURITY: We avoid putting the token on git's cmdline by using GIT_ASKPASS.
# git invokes the askpass script with no arguments, reads the response from
# stdout, and uses it as the password. The token only ever lives in a 0600
# temp file. This prevents the token from appearing in `ps` output.
if git remote get-url origin >/dev/null 2>&1; then
  PUSH_OK=false
  PUSH_TOKEN=""
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    PUSH_TOKEN="$GITHUB_TOKEN"
  elif [[ -n "${GH_TOKEN:-}" ]]; then
    PUSH_TOKEN="$GH_TOKEN"
  elif command -v gh >/dev/null 2>&1 && gh auth token >/dev/null 2>&1; then
    PUSH_TOKEN=$(gh auth token 2>/dev/null || true)
  fi
  if [[ -n "$PUSH_TOKEN" ]]; then
    # Write the token to a 0600 file, write an askpass script that reads it,
    # invoke git with the public origin URL, then clean up.
    ASKPASS_DIR="$(mktemp -d -t app-dev-discovery-push-XXXXXX)"
    chmod 700 "$ASKPASS_DIR"
    ASKPASS_SCRIPT="$ASKPASS_DIR/askpass.sh"
    TOKEN_FILE="$ASKPASS_DIR/token"
    printf '%s' "$PUSH_TOKEN" > "$TOKEN_FILE"
    chmod 600 "$TOKEN_FILE"
    cat > "$ASKPASS_SCRIPT" <<'AP_EOF'
#!/usr/bin/env bash
# askpass helper — prints the GitHub token from a file
cat "$GIT_TOKEN_FILE"
AP_EOF
    chmod 700 "$ASKPASS_SCRIPT"
    GIT_TOKEN_FILE="$TOKEN_FILE" \
    GIT_ASKPASS="$ASKPASS_SCRIPT" \
      git -c credential.helper= \
          push -u origin "$BRANCH_NAME" 2>/tmp/push.err
    PUSH_EXIT=$?
    # Clean up token material
    shred -u "$TOKEN_FILE" 2>/dev/null || rm -f "$TOKEN_FILE"
    rm -rf "$ASKPASS_DIR"
    unset GIT_TOKEN_FILE GIT_ASKPASS PUSH_TOKEN
    if [[ $PUSH_EXIT -eq 0 ]]; then
      PUSH_OK=true
    fi
  else
    if git push -u origin "$BRANCH_NAME" 2>/tmp/push.err; then
      PUSH_OK=true
    fi
  fi
  if [[ "$PUSH_OK" == "true" ]]; then
    echo "  - pushed branch $BRANCH_NAME"
  else
    sed -i "s|x-access-token:[^@]*@|x-access-token:REDACTED@|g" /tmp/push.err 2>/dev/null
    echo "  - push failed. Commit is local; you can push manually:"
    echo "    git push -u origin $BRANCH_NAME"
    cat /tmp/push.err >&2
  fi
  rm -f /tmp/push.err
else
  echo "  - no origin remote, skipping push"
fi

# -------- Cleanup --------
if [[ "$KEEP_TEMP" != "true" ]]; then
  echo
  echo "[Cleanup] Removing $EVIDENCE_DIR (KEEP_TEMP=$KEEP_TEMP)"
  rm -rf "$WORKSPACE_DIR/$EVIDENCE_DIR"
fi

# -------- Completion --------
echo
echo "✅ app-dev-discovery complete"
echo "  final doc:   $FINAL_DOC"
echo "  ADRs:        docs/adr/000-template.md, docs/adr/001-current-architecture-baseline.md"
echo "  branch:      $BRANCH_NAME"
echo "  commit:      $(git rev-parse --short HEAD)"
echo "  validation:  PASS"
