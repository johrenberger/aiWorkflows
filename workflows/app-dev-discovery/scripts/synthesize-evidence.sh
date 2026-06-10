#!/usr/bin/env bash
# synthesize-evidence.sh — Convert repo-discovery-analyzer JSON outputs into
# the 16 app-dev-discovery evidence markdown templates, deterministically.
#
# Usage:
#   synthesize-evidence.sh <analyzer-output-dir> <evidence-dir> <owner> <repo> <commit>
#
# What it does:
#   1. Runs `python3 -m repo_discovery_analyzer.cli` over the target repo
#      (the caller has already cloned it).
#   2. Reads the resulting JSON files and synthesizes the corresponding
#      evidence markdown files at <evidence-dir>/NN-*.md, one per
#      app-dev-discovery phase.
#   3. Leaves the 16th evidence file (16-final-validation.md) to the agent,
#      since confidence scoring is partly LLM judgment.
#
# This script is the deterministic backbone of the workflow. The agent is
# invoked afterwards to do the parts that genuinely require judgment:
# narrative synthesis, Mermaid diagrams, risk interpretation, contradiction
# explanation, and confidence scoring.

set -Eeuo pipefail

if [[ $# -lt 5 ]]; then
  echo "Usage: $0 <repo-path> <analyzer-output-dir> <evidence-dir> <owner> <repo> [commit]" >&2
  exit 2
fi

REPO_PATH="$1"
ANALYZER_OUT="$2"
EVIDENCE_DIR="$3"
OWNER="$4"
REPO="$5"
COMMIT="${6:-}"

mkdir -p "$ANALYZER_OUT" "$EVIDENCE_DIR"

# ---- Step 1: run the analyzer ----
echo "[Synthesize] Running repo-discovery-analyzer on $REPO_PATH"
python3 -m repo_discovery_analyzer.cli \
  --repo-path "$REPO_PATH" \
  --github-url "https://github.com/${OWNER}/${REPO}" \
  --commit "${COMMIT:-HEAD}" \
  --output-dir "$ANALYZER_OUT" \
  --include-large-files \
  --json-indent 2

# ---- Step 2: locate the python helper that does the JSON→markdown conversion ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPER="$SCRIPT_DIR/synthesize_evidence.py"

if [[ ! -f "$HELPER" ]]; then
  echo "ERROR: helper not found at $HELPER" >&2
  exit 3
fi

echo "[Synthesize] Rendering evidence markdown into $EVIDENCE_DIR"
python3 "$HELPER" \
  --analyzer-out "$ANALYZER_OUT" \
  --evidence-dir "$EVIDENCE_DIR" \
  --owner "$OWNER" \
  --repo "$REPO" \
  --commit "$COMMIT"

echo "[Synthesize] Done. Evidence files:"
ls -la "$EVIDENCE_DIR"
