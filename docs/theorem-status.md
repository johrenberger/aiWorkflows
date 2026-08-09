# Theorem status

| Identifier | Status | Lean location | Claim scope |
| --- | --- | --- | --- |
| `trajectory_zero` | Checked | `CollatzResearch.Basic` | Definitional base case |
| `trajectory_succ` | Checked | `CollatzResearch.Basic` | One-step unfolding |
| `standardStep_positive` | Pending | `CollatzResearch.Dynamics` | Standard step preserves positivity on positive domain (definition only; proof TODO) |
| `acceleratedStep_positive_of_odd` | Pending | `CollatzResearch.Dynamics` | Accelerated step preserves positivity on odd domain (definition only; proof TODO) |
| Global convergence | Not started | — | No claim |
| Nontrivial cycle exclusion | Not started | — | No claim |

Update this table in the same change as any theorem addition. "Checked" means `lake build` succeeds against pinned dependencies. "Pending" means the definition is in place but the proof is incomplete (tracked as `sorry` in the Lean file).
