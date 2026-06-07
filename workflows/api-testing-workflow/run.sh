#!/usr/bin/env bash
# run.sh — api-testing-workflow runner
#
# Usage:
#   ./run.sh <github-repo-url> [--workspace <dir>] [--keep-temp] [--dry-run] [--no-agent] [--run-perf]
#
# Examples:
#   ./run.sh https://github.com/foo/bar
#   ./run.sh https://github.com/foo/bar --workspace /tmp/api-test --keep-temp
#   ./run.sh https://github.com/foo/bar --dry-run    # scaffold + emit prompt only
#   ./run.sh https://github.com/foo/bar --run-perf   # require executable perf scripts
#
# RUN_PERF (also settable via env var):
#   When true, the agent must produce executable k6 / locust / pytest
#   scripts under tests/performance/ (not just a plan), and a short
#   baseline run is encouraged against a local/staging URL. Default: false.
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
# RUN_PERF defaults to whatever the caller exported; the --run-perf flag
# below forces it on.
RUN_PERF="${RUN_PERF:-false}"

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
    --run-perf)  RUN_PERF="true"; shift ;;
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
EVIDENCE_DIR=".openclaw/api-testing"
TODAY="$(date -u +%Y-%m-%d)"

echo "→ api-testing-workflow"
echo "  repo:      $OWNER/$REPO"
echo "  url:       $REPO_URL"
echo "  workspace: $WORKSPACE_DIR"
echo "  date:      $TODAY"
echo "  dry-run:   $DRY_RUN"
echo "  RUN_PERF:  ${RUN_PERF:-false}"
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
BRANCH_NAME="docs/api-testing-$TODAY"

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
# Stage 1 — Run Metadata (filled in by the agent)

- **Repository:** $OWNER/$REPO
- **Remote URL:** $REPO_URL
- **Default branch:** $DEFAULT_BRANCH
- **Checked-out branch:** $(git symbolic-ref --short HEAD 2>/dev/null || echo "$DEFAULT_BRANCH")
- **Current commit:** $CURRENT_COMMIT
- **Commit-pinned URL prefix:** https://github.com/$OWNER/$REPO/blob/$CURRENT_COMMIT/
- **Run date:** $TODAY
- **Workspace:** $WORKSPACE_DIR
- **Workflow:** api-testing-workflow
- **Input mode:** GitHub URL (cloned by the runner)
EOF

echo "  - metadata written to $EVIDENCE_DIR/00-run-metadata.md"

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

# Build the message: prompt + a small tail telling the agent the runtime context.
# We use a here-string approach: write the prompt and the runtime context to
# temp files, concatenate, then read into AGENT_MESSAGE without quote-
# expansion backticks. The previous in-line $() approach tripped over the
# backticks we use in markdown code spans.
PROMPT_TMP="$(mktemp -t api-testing-prompt-XXXXXX)"
CONTEXT_TMP="$(mktemp -t api-testing-ctx-XXXXXX)"
trap 'rm -f "$PROMPT_TMP" "$CONTEXT_TMP"' EXIT

cp "$PROMPT_FILE" "$PROMPT_TMP"

cat > "$CONTEXT_TMP" <<EOF

---

# Runtime Context (provided by run.sh)

- GITHUB_PROJECT_URL=$REPO_URL
- WORKSPACE_DIR=$WORKSPACE_DIR
- EVIDENCE_DIR=$EVIDENCE_DIR
- TODAY=$TODAY
- DEFAULT_BRANCH=$DEFAULT_BRANCH
- CURRENT_COMMIT=$CURRENT_COMMIT
- COMMIT_PINNED_PREFIX=https://github.com/$OWNER/$REPO/blob/$CURRENT_COMMIT/

## Default runtime config (unless overridden here)

\`\`\`yaml
target:
  api_type: unknown
auth:
  required: false
  type: none
testing:
  mode: auto
  generate_tests: true
  execute_tests: true
  patch_application_code: false
  commit_changes: false
  include_security_baseline: true
  include_performance_tests: ${RUN_PERF:-false}
  include_resilience_tests: false
  include_chaos_tests: false
  include_observability_review: true
  fail_on_contract_drift: true
  allow_destructive_tests: false
  allow_production_load_tests: false
\`\`\`

\`\`\`
RUN_PERF=${RUN_PERF:-false}
\`\`\`

If RUN_PERF is \`true\`:
- Stage 10 (Performance Readiness Module) must produce **executable** scripts
  under \`tests/performance/\` (k6 / locust / hey / wrk) — not just a plan.
- The scripts must use \`@pytest.mark.performance\` markers (or k6's native
  thresholds) so they can be filtered.
- The agent SHOULD attempt a short **baseline** run if the API is locally
  runnable (e.g. \`hey -n 200 -c 10 http://localhost:8000/...\` or a k6
  scenario with low VU counts and short duration). It MUST NOT ramp into
  stress / spike / soak / production-load scenarios without an explicit
  operator confirmation captured in the run log.
- The agent must record what was executed in
  \`artifacts/api_performance_plan.md\` under an "Executed runs" section,
  with command lines, exit codes, and observed metrics.
- \`artifacts/api_test_results.json\` must include the perf runs in its
  \`commands\` list.

If RUN_PERF is \`false\` (the default):
- Stage 10 produces a **plan only** — no execution. The
  \`tests/performance/\` dir is scaffolded but may be empty.
- The plan must still enumerate scenarios, tooling, and thresholds — same
  as before.

You are operating inside $WORKSPACE_DIR. Follow the stages in this prompt
sequentially. When finished, the runner will handle branch creation, commit,
and push. Just produce the artifacts under \`artifacts/\`, the tests under
\`tests/{api,contract,performance,resilience}/\`, the human-readable rollup at
\`docs/api-testing-$TODAY.md\`, the ADR-001 baseline, and the TODO tracker.
Write a summary of: final doc path, artifact paths, validation status,
top 5 highest-risk findings, blockers.
EOF

# Concatenate prompt + context. We use a single read into a variable that is
# then re-quoted; backticks inside the source files are now literal because
# they are not inside an active $() / "" evaluation.
AGENT_MESSAGE="$(cat "$PROMPT_TMP" "$CONTEXT_TMP")"

# Save the message to disk for audit
echo "$AGENT_MESSAGE" > "$WORKSPACE_DIR/$EVIDENCE_DIR/00-agent-prompt.md"

# Invoke the agent. In OpenClaw 2026.5.x, --message alone is not enough — we
# need to pick a session. We use --agent main --local for fire-and-forget
# batch work: the agent runs to completion in this process, prints its reply
# to stdout, and we capture it. --timeout extends the default 600s window
# since 17 stages of API analysis can take a while.
AGENT_OUTPUT_FILE="$WORKSPACE_DIR/$EVIDENCE_DIR/00-agent-output.txt"
AGENT_TIMEOUT="${AGENT_TIMEOUT:-1800}"  # 30 min default

if ! openclaw agent --agent main --local --timeout "$AGENT_TIMEOUT" \
     --message "$AGENT_MESSAGE" > "$AGENT_OUTPUT_FILE" 2>&1; then
  echo "WARNING: agent exited non-zero. Checking if deliverables are on disk anyway..." >&2
  # Some OpenClaw embedded-agent runs hit a session-takeover race during
  # cleanup (EmbeddedAttemptSessionTakeoverError) AFTER all the work has
  # been written. Treat the run as successful if the final doc exists and
  # validation passed; only fail if deliverables are missing.
  if [[ ! -f "$WORKSPACE_DIR/docs/api-testing-${TODAY}.md" ]]; then
    echo "ERROR: agent invocation failed AND no final doc was produced. See $AGENT_OUTPUT_FILE" >&2
    exit 4
  fi
  echo "  - deliverables found on disk; treating as success despite agent cleanup error"
fi

echo "  - agent output: $AGENT_OUTPUT_FILE"

# -------- Stage 16 validation --------
echo
echo "[Stage 16] Validation gate"
# Pass RUN_PERF through so the validator can distinguish plan-only vs.
# executable-scripts mode. Without this export the child sees an unset
# RUN_PERF and silently treats the run as plan-only.
if ! env RUN_PERF="${RUN_PERF:-false}" \
  bash "$SCRIPT_DIR/scripts/validate.sh" "$WORKSPACE_DIR" "$REPO" "$TODAY"; then
  echo "ERROR: validation failed. Inspect $WORKSPACE_DIR/$EVIDENCE_DIR/13-validation-gate.md" >&2
  exit 5
fi

# -------- Commit --------
echo
echo "[Commit]"
cd "$WORKSPACE_DIR"

# Check branch collision
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
  SHORT_COMMIT="$(git rev-parse --short HEAD)"
  BRANCH_NAME="${BRANCH_NAME}-${SHORT_COMMIT}"
fi

git checkout -b "$BRANCH_NAME"
git add docs/ artifacts/ tests/ scripts/ TODO_api-tester.md 2>/dev/null || true
if git diff --cached --quiet; then
  echo "  - no changes to commit"
else
  git commit -m "test(api): add API testing workflow artifacts

Generated by api-testing-workflow on $TODAY.
Target: $OWNER/$REPO @ $CURRENT_COMMIT

Produces:
- docs/api-testing-$TODAY.md (human-readable rollup)
- artifacts/api_testing_context.md
- artifacts/api_inventory.json
- artifacts/openapi.normalized.yaml
- artifacts/api_test_plan.md
- artifacts/api_security_findings.md
- artifacts/api_performance_plan.md
- artifacts/api_resilience_plan.md
- artifacts/api_observability_recommendations.md
- artifacts/api_test_results.json
- artifacts/api_defect_report.md
- artifacts/api_change_log.md
- artifacts/api_workflow_summary.md
- tests/api/ (pytest + httpx functional tests)
- tests/contract/ (contract tests)
- TODO_api-tester.md (task tracker)
- docs/adr/001-api-contract-baseline.md"
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
    ASKPASS_DIR="$(mktemp -d -t api-testing-push-XXXXXX)"
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
echo "✅ api-testing-workflow complete"
echo "  final doc:    docs/api-testing-$TODAY.md"
echo "  artifacts:    artifacts/"
echo "  tests:        tests/{api,contract,performance,resilience}/"
echo "  ADR:          docs/adr/001-api-contract-baseline.md"
echo "  tracker:      TODO_api-tester.md"
echo "  branch:       $BRANCH_NAME"
echo "  commit:       $(git rev-parse --short HEAD)"
echo "  validation:   PASS"
