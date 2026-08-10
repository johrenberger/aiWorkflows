# Theorem status

| Identifier | Status | Lean location | Claim scope |
| --- | --- | --- | --- |
| `trajectory_zero` | Checked | `CollatzResearch.Basic` | Definitional base case |
| `trajectory_succ` | Checked | `CollatzResearch.Basic` | One-step unfolding |
| `standardStep_positive` | Pending | `CollatzResearch.Dynamics` | Standard step preserves positivity on positive domain (definition only; proof TODO) |
| `acceleratedStep_positive_of_odd` | Pending | `CollatzResearch.Dynamics` | Accelerated step preserves positivity on odd domain (definition only; proof TODO) |
| `standardTrajectory_zero` | Checked | `CollatzResearch.Equivalence` | Definitional base case |
| `standardTrajectory_succ` | Checked | `CollatzResearch.Equivalence` | One-step unfolding |
| `acceleratedStep_equiv_standardStep` | Pending | `CollatzResearch.Equivalence` | One accelerated step on odd domain = 1 + ν₂(3n+1) standard steps (definition only; proof TODO) |
| `acceleratedTrajectory_reaches_one_implies_standard` | Pending | `CollatzResearch.Equivalence` | Accelerated trajectory reaching 1 lifts to a finite standard trajectory reaching 1 (definition only; proof TODO) |
| Global convergence | Not started | — | No claim |
| Nontrivial cycle exclusion | Not started | — | No claim |

Update this table in the same change as any theorem addition. "Checked" means `lake build` succeeds against pinned dependencies. "Pending" means the definition is in place but the proof is incomplete (tracked as `sorry` in the Lean file).
