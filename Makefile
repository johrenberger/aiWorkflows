# Makefile for dreaming workflow local validation
#
# PI-008 (cycle-1 follow-up): run dreaming validation locally before pushing,
# to catch detached-HEAD / marker-rule / allowlist false-positives in CI before
# they become fix-up commits.
#
# Usage:
#   make dreaming-validate        # run pytest tests/dreaming/
#   make dreaming-pr-ready        # alias for dreaming-validate
#   make dreaming-clean           # remove generated artifacts (none currently)
#
# These targets must work in CI and on developer machines without docker or act.

.PHONY: dreaming-validate dreaming-pr-ready dreaming-clean dreaming-help

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

dreaming-clean:
	@echo "No generated artifacts to clean."

dreaming-help:
	@echo "Dreaming targets:"
	@echo "  make dreaming-validate   Run pytest tests/dreaming/ (validates artifacts)"
	@echo "  make dreaming-pr-ready   Alias for dreaming-validate"
	@echo "  make dreaming-clean      Remove generated artifacts (none currently)"
