# Makefile for dreaming workflow local validation
#
# PI-008 (cycle-1 follow-up): run dreaming validation locally before pushing,
# to catch detached-HEAD / marker-rule / allowlist false-positives in CI before
# they become fix-up commits.
#
# Usage:
#   make dreaming-validate        # run pytest tests/dreaming/
#   make dreaming-pr-ready        # alias for dreaming-validate
#   make dreaming-precheck        # workspace-state pre-check (PI-012)
#   make dreaming-clean           # remove generated artifacts (none currently)
#   make dreaming-help            # list targets
#
# These targets must work in CI and on developer machines without docker or act.

.PHONY: dreaming-validate dreaming-pr-ready dreaming-precheck dreaming-clean dreaming-help

# Resolve the base ref the same way the CI workflow does:
#   1. DREAMING_MERGE_BASE env var (CI-provided)
#   2. GITHUB_BASE_REF / GITHUB_HEAD_REF (CI env)
#   3. local 'main' / 'origin/main'
dreaming-resolve-base:
	@bash -c '\
	  if [ -n "$${DREAMING_MERGE_BASE:-}" ]; then \
	    echo "Using DREAMING_MERGE_BASE=$$DREAMING_MERGE_BASE"; exit 0; \
	  fi; \
	  if [ -n "$${GITHUB_BASE_REF:-}" ]; then \
	    echo "GITHUB_BASE_REF=$$GITHUB_BASE_REF"; \
	    echo "GITHUB_HEAD_REF=$${GITHUB_HEAD_REF:-}"; \
	    MB=$$(gh api "repos/johrenberger/aiWorkflows/compare/$${GITHUB_BASE_REF}...$${GITHUB_HEAD_REF}" --jq .merge_base_commit.sha 2>/dev/null || true); \
	    if [ -n "$$MB" ]; then echo "DREAMING_MERGE_BASE=$$MB"; exit 0; fi; \
	  fi; \
	  if git rev-parse --verify main^{commit} >/dev/null 2>&1; then \
	    echo "Resolving merge-base from local main"; \
	    MB=$$(git merge-base HEAD main 2>/dev/null || true); \
	    [ -n "$$MB" ] && echo "DREAMING_MERGE_BASE=$$MB"; \
	  fi; \
	'

dreaming-validate: dreaming-resolve-base
	@echo "Running dreaming validation tests..."
	@cd "$(CURDIR)" && python3 -m pytest tests/dreaming/ -v

dreaming-pr-ready: dreaming-validate

# Workspace-state pre-check (PI-012, cycle 4). Surfaces conditions that have
# historically caused CI-only fix-ups:
#   - prior-cycle dreaming branches lingering on disk (RS-014)
#   - main out of date with origin (fragile local merge-base, cycle-1 fix-up source)
#   - on the dreaming branch when we expected main (early-warning)
# These are warnings, not failures; the goal is to make state visible at
# human time rather than push time.
dreaming-precheck:
	@bash -c '\
	  echo "Dreaming workspace pre-check (PI-012)"; \
	  echo "---"; \
	  echo "Current branch:"; \
	  git -C "$(CURDIR)" rev-parse --abbrev-ref HEAD; \
	  echo "---"; \
	  echo "Dreaming branches on disk:"; \
	  git -C "$(CURDIR)" branch --list "dreaming/nightly-execution-quality-*"; \
	  echo "---"; \
	  echo "Main vs origin/main:"; \
	  LOCAL=$$(git -C "$(CURDIR)" rev-parse main^{commit} 2>/dev/null || echo MISSING); \
	  REMOTE=$$(git -C "$(CURDIR)" rev-parse origin/main^{commit} 2>/dev/null || echo MISSING); \
	  echo "  local:  $$LOCAL"; \
	  echo "  remote: $$REMOTE"; \
	  if [ "$$LOCAL" = "$$REMOTE" ]; then \
	    echo "  status: in sync"; \
	  else \
	    echo "  status: AHEAD or BEHIND — run: git fetch origin main && git merge --ff-only origin/main"; \
	  fi; \
	  echo "---"; \
	  echo "Untracked paths (filtered to top-level):"; \
	  git -C "$(CURDIR)" status --porcelain | grep "^??" | awk "{print \$$2}" | head -10; \
	  echo "---"; \
	  echo "Done. None of the above blocks the cycle; it surfaces state for review."; \
	'

dreaming-clean:
	@echo "No generated artifacts to clean."

dreaming-help:
	@echo "Dreaming targets:"
	@echo "  make dreaming-validate   Run pytest tests/dreaming/ (validates artifacts)"
	@echo "  make dreaming-pr-ready   Alias for dreaming-validate"
	@echo "  make dreaming-precheck   Workspace-state pre-check (PI-012, cycle 4)"
	@echo "  make dreaming-clean      Remove generated artifacts (none currently)"
