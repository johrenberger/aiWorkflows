# Handoff Contracts

This document defines the explicit handoff paths from `component-test-analysis` outputs to other workflows. The handoffs are **manual** in v1 — there is no auto-pipeline. The user reads the manifest and decides which downstream workflow to invoke.

## Handoff manifest

Every run of `component-test-analysis` produces `handoff-manifest.json` with this structure:

```json
{
  "produced_at": "<ISO-8601>",
  "profile": "lite|standard|full",
  "repo": "<url>",
  "branch": "<branch>",
  "commit": "<sha>",
  "artifacts": [
    {
      "file": "<name>.json",
      "description": "<text>",
      "consumer": "application-test-coverage|application-mutation-testing|external-ai-test-gen|none",
      "consumer_input_mapping": "<how to consume>"
    }
  ]
}
```

## Handoff 1: gap-backlog.json → application-test-coverage

**Source:** `gap-backlog.json` (LITE+ profile)
**Consumer:** `application-test-coverage`
**Goal:** Pre-populate the coverage workflow's "focused picks" with the analysis-prioritized gaps.

**Translation:**

1. Sort gaps by `priority` (P0 first) and within priority by `risk` (T1 first).
2. For the top N gaps (default 5, configurable via `MAX_FILES_PER_BATCH`):
   - Extract `source_file` from each gap.
   - For Java: `MODULE_LIST=path/to/<module>` for each gap's source module.
   - For Python: pass the test file as `INPUT_TEST_FILE`.
3. Set `ALLOW_PRODUCTION_FIXES=false` (the gap backlog assumes the source is correct; the tests verify it).
4. Set `ENABLE_TESTABILITY_CLASSIFICATION=true` (use the analysis' T1/T2/T3/T4 risk tier as the testability filter; only T1 and T2 are eligible in the first pass).

**Concrete example:**

```bash
# After component-test-analysis produces gap-backlog.json with P0/T1 gaps
python3 -c "
import json
with open('gap-backlog.json') as f:
    gaps = json.load(f)['gaps']
top5 = sorted(
    [g for g in gaps if g['priority'] == 'P0' and g['risk'] in ('T1', 'T2')],
    key=lambda g: (g['priority'], g['risk'])
)[:5]
print(' '.join(set('/'.join(g['source_file'].split('/')[:2]) for g in top5)))
" > /tmp/module-list.txt

# Pass to coverage workflow
MODULE_LIST=$(cat /tmp/module-list.txt) \
  INPUT_GITHUB_REPO=https://github.com/johrenberger/BroadleafCommerce \
  INPUT_BRANCH=main \
  COVERAGE_TARGET_PER_FILE=90 \
  ENABLE_TESTABILITY_CLASSIFICATION=true \
  ALLOW_PRODUCTION_FIXES=false \
  ./run-coverage-workflow.sh
```

**What gets inherited:**

- The component inventory tells coverage workflow which files belong to which component (helpful for repair decisions).
- The risk tier tells coverage workflow which gaps are non-negotiable vs nice-to-have.
- The behavioral coverage score tells coverage workflow what the target is.

**What does NOT transfer:**

- The Java/JS playbooks (those are recommendations, not inputs to the coverage workflow).
- The decision tree (the coverage workflow has its own).
- The mutation roadmap (that's for the mutation workflow).

## Handoff 2: component-inventory.json → application-test-coverage

**Source:** `component-inventory.json` (LITE+ profile)
**Consumer:** `application-test-coverage`
**Goal:** Provide component context for the per-file coverage table.

**Translation:**

- Each component's `risk_tier` becomes the `Risk` column in the per-file coverage table.
- Components marked `UNCLEAR` are flagged for `ENABLE_TESTABILITY_CLASSIFICATION=true` review.
- Components with `test_boundary=unit` are eligible for direct unit-test extension; `test_boundary=component` requires Spring context or equivalent.

**Concrete example:**

The coverage workflow's per-file table gains a `Risk Tier` column populated from `component-inventory.json`. The classification gate (TC-VAL-21 architecture-aware) uses this column to decide which files are eligible in the first pass.

## Handoff 3: mutation-roadmap.json → application-mutation-testing

**Source:** `mutation-roadmap.json` (FULL profile only)
**Consumer:** `application-mutation-testing`
**Goal:** Pre-populate mutation targets, exclusions, and thresholds.

**Translation:**

- `targets` → `INPUT_MUTATION_TARGETS` (comma-separated component IDs)
- `exclusions` → `INPUT_MUTATION_EXCLUSIONS` (one exclusion per line: `<path> # <reason>`)
- `thresholds.mutation_score` → `MUTATION_SCORE_TARGET`
- `thresholds.quality_gate` → `MUTATION_QUALITY_GATE` (block or warn)

**Concrete example:**

```bash
INPUT_MUTATION_TARGETS=CTA-COMP-001,CTA-COMP-002,CTA-COMP-005 \
INPUT_MUTATION_EXCLUSIONS=$(awk '{print $1" # "$2}' < mutation-roadmap.json exclusions) \
MUTATION_SCORE_TARGET=60 \
MUTATION_QUALITY_GATE=block \
  ./run-mutation-workflow.sh
```

## Handoff 4: test-creation-input-schema.json → external AI test-gen

**Source:** `test-creation-input-schema.json` (FULL profile only)
**Consumer:** External AI test-generation systems (e.g. CodiumAI, Diffblue, internal tools)
**Goal:** Define a stable input contract for AI test generators.

**Translation:**

The JSON Schema in `test-creation-input-schema.json` describes the input shape an AI test-gen system should accept. The system reads `gap-backlog.json` (or a derived slice) and emits test files.

This handoff is **out of scope for OpenClaw** — we don't ship an AI test-gen system. But the schema is the contract any such system can implement against.

**Example payload for an AI test-gen system:**

```json
{
  "github_url": "https://github.com/johrenberger/BroadleafCommerce",
  "branch": "main",
  "component": {
    "id": "CTA-COMP-001",
    "name": "OrderService",
    "source_paths": ["core/broadleaf-framework/src/main/java/.../OrderService.java"]
  },
  "behaviors": [
    {"id": "CTA-BEH-001", "name": "cancel", "happy": true, "error_paths": ["InventoryRollbackException"]}
  ],
  "dependencies": [...],
  "risk_tier": "T1",
  "missing_scenarios": [
    {"id": "CTA-GAP-001", "trigger": "cancel() with inventory rollback failure", "expected": "InventoryRollbackException propagated"}
  ],
  "assertions": [...],
  "fixtures": [...],
  "execution_commands": ["mvn -pl core/broadleaf-framework -Dtest=OrderServiceSpec test"],
  "acceptance_criteria": "All 8 paths in CTA-BEH-001 covered; mutation score ≥ 60%"
}
```

## Handoff 5: contract-inventory.json → contract testing tools

**Source:** `contract-inventory.json` (STANDARD+ profile)
**Consumer:** Pact, Spring Cloud Contract, OpenAPI generators
**Goal:** Auto-generate contract tests from the inventory.

**Translation (out of OpenClaw scope):**

The inventory is structured to be consumable by Pact flow generators. Each contract has request/response/error schemas that can be converted to a Pact file. This is a future enhancement; v1 just emits the inventory.

## Handoff 6: dependency-risk-matrix.json → monitoring / chaos engineering

**Source:** `dependency-risk-matrix.json` (STANDARD+ profile)
**Consumer:** Monitoring systems, chaos engineering platforms (Gremlin, Chaos Toolkit)
**Goal:** Prioritize chaos experiments and synthetic monitoring.

**Translation (out of OpenClaw scope):**

Dependencies with `risk_tier=T1` should be targeted by chaos experiments first. The matrix maps to Gremlin attack types (HTTP → "latency", "error", Database → "connection failure", etc.).

## What does NOT handoff

- **The behavioral coverage matrix** is intermediate, not an output consumed by other workflows. It's documented for the user to read.
- **The state transition matrix** is also intermediate. Useful for human review, not for downstream test gen.
- **The architecture validation backlog** is recommendation-only. Auto-fixing architectural violations is out of scope for the coverage and mutation workflows.
- **The Java/JS playbooks** are human-readable strategy docs, not inputs to other workflows.

## Manual vs auto handoff

v1 handoffs are **manual**. The user reads `handoff-manifest.json`, picks the consumer workflow, and runs it with the mapped inputs. Future versions may support an `AUTO_HANDOFF=true` input that chains the workflows automatically. This is deferred because:

- Cross-workflow state (clone dirs, git state, working tree cleanliness) is hard to get right.
- The user usually wants to review the gap backlog before invoking the coverage workflow.
- A bad auto-handoff could silently generate thousands of low-quality tests.

If you need auto-handoff for a specific project, do it as a wrapper script, not as workflow logic.
