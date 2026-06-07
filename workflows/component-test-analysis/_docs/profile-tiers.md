# Profile Tiers — Per-Section Mapping

This doc lists the 28 analysis sections and which profile includes them. The mapping matches `workflow.md` Phase 5/6/7/8.

## Sections

| # | Section | LITE | STANDARD | FULL | Phase |
|---:|---|:---:|:---:|:---:|---|
| 1 | Repository Analysis | ✅ | ✅ | ✅ | 3 |
| 2 | Component Boundary Taxonomy | ✅ | ✅ | ✅ | 4 |
| 3 | Dependency Risk Model | partial (internal only) | ✅ | ✅ | 5a / 6a |
| 4 | Component Testing Definition | — | — | ✅ | 8c |
| 5 | Dataset Integrity Analysis | ✅ | ✅ | ✅ | 5b |
| 6 | State Transition Analysis | ✅ | ✅ | ✅ | 5c |
| 7 | Behavioral Coverage Model | ✅ | ✅ | ✅ | 5d |
| 8 | Current Test Analysis | ✅ | ✅ | ✅ | 5e |
| 9 | Test Gap Analysis | ✅ | ✅ | ✅ | 5f |
| 10 | Security-Relevant Component Testing | — | — | ✅ | 8a |
| 11 | Contract Coverage Analysis | — | ✅ | ✅ | 6b |
| 12 | Architecture Validation | — | — | ✅ | 8b |
| 13 | Coverage Strategy | ✅ | ✅ | ✅ | 5g |
| 14 | Test Fidelity Strategy | — | ✅ | ✅ | 6c |
| 15 | Test Architecture Decision Tree | — | ✅ | ✅ | 6d |
| 16 | Java Implementation Playbook | — | — | ✅ | 8d |
| 17 | JavaScript Implementation Playbook | — | — | ✅ | 8e |
| 18 | Mutation Testing Strategy | — | — | ✅ | 8f |
| 19 | Flaky Test Prevention | — | ✅ | ✅ | 6e |
| 20 | Test Data Governance | — | ✅ | ✅ | 6e |
| 21 | Change-Risk Prioritization | — | ✅ | ✅ | 7a |
| 22 | Production Feedback Loop | — | ✅ | ✅ | 7e |
| 23 | Machine-Readable Outputs | ✅ | ✅ | ✅ | 9 |
| 24 | Test Creation Workflow Input Schema | — | — | ✅ | 8g |
| 25 | Test Gap Backlog Format | — | — | ✅ | 8g |
| 26 | Implementation Rollout Plan | ✅ | ✅ | ✅ | 7c |
| 27 | Quality Gates | — | ✅ | ✅ | 7b |
| 28 | Test Pyramid Alignment | — | ✅ | ✅ | 7d |

## Section count per profile

| Profile | Section count | Wall-clock (rough) |
|---|:---:|---|
| LITE | 13 | 10-20 min |
| STANDARD | 22 | 30-60 min |
| FULL | 28 | 2-4 hours |

## LITE profile (13 sections)

The "I need to make a decision tomorrow" profile. Covers:

- **Inventory:** Repository, Components, Datasets
- **Behaviors:** State transitions, Behavioral coverage
- **Current state:** Test analysis
- **Strategy:** Coverage strategy, Rollout plan
- **Outputs:** Machine-readable outputs

Skips: Risk modeling details, Security, Architecture, Java/JS playbooks, Mutation, Fidelity, Decision tree, Quality gates, Risk ranking, Flaky prevention, Data governance, Production feedback loop, Component testing definition, Test creation schema, Gap backlog format.

## STANDARD profile (22 sections, default)

LITE + 9 additional sections. Adds:

- **Risk:** Full dependency risk matrix, Risk priority ranking
- **Contracts:** Contract coverage analysis
- **Practice:** Test fidelity strategy, Decision tree, Flaky prevention, Data governance
- **Gates:** Quality gates, Test pyramid alignment
- **Loop:** Production feedback loop

Skips: Security, Architecture, Java/JS playbooks, Mutation, Component testing definition, Test creation schema, Gap backlog format.

## FULL profile (28 sections)

STANDARD + 6 additional sections. Adds:

- **Security:** Security coverage matrix, OWASP ASVS mapping
- **Architecture:** Architecture validation, ArchUnit/DC rule recommendations
- **Definition:** Component testing definition (specific to this repo)
- **Playbooks:** Java playbook, JavaScript playbook
- **Mutation:** Mutation testing strategy + roadmap
- **Schema:** Test creation input schema, Gap backlog format

## When to pick which

- **LITE:** "I have 30 minutes and need to know what the repo is and where the gaps are." Triage mode.
- **STANDARD:** "I'm planning a quarter and need a backlog + risk ranking + quality gates." Default for new repos.
- **FULL:** "I'm writing the testing strategy doc that will be reviewed by architects and SDETs." Complete audit.

## Profile upgrade

If you start with LITE and need more depth, you can re-run with a higher profile. The artifacts from the lower-tier run are preserved in `OUTPUT_DIR/` and the higher-tier run only adds new files. This is intentional: a LITE-then-FULL run is faster than a single FULL run if the LITE run already answered the early questions, because the higher-tier run can skip re-discovery and focus on the deeper sections.

In practice this means: start with LITE for triage, then re-run with STANDARD or FULL once you know the repo is worth the deeper investment.
