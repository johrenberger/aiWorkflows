import Mathlib
import CollatzResearch.Basic
import CollatzResearch.Dynamics

/-!
# Standard ↔ Accelerated Collatz equivalence

Bridges the two maps:

- The **standard map** `C` from `CollatzResearch.Dynamics.standardStep`:
  `C(n) = n / 2` if `n` is even, `3n + 1` if `n` is odd.
- The **accelerated map** `T` from `CollatzResearch.Basic.acceleratedStep`:
  `T(n) = (3n + 1) / 2^{ν₂(3n + 1)}`, defined on the odd domain.

The forward theorem states that one accelerated step on an odd input
is equivalent to `1 + ν₂(3n + 1)` standard steps. The reverse theorem
states that an accelerated trajectory reaching `1` corresponds to a
(finite) standard trajectory also reaching `1`.

Both theorems make no global convergence, cycle-exclusion, or
termination claim — they are local equivalences on the odd domain.
-/

namespace CollatzResearch

/-- Iteration of the standard map. -/
def standardTrajectory (n : Nat) : Nat → Nat
  | 0 => n
  | steps + 1 => standardStep (standardTrajectory n steps)

@[simp] theorem standardTrajectory_zero (n : Nat) : standardTrajectory n 0 = n := rfl

@[simp] theorem standardTrajectory_succ (n steps : Nat) :
    standardTrajectory n (steps + 1) = standardStep (standardTrajectory n steps) := by
  rfl

/-- One accelerated step on the odd domain corresponds to
`1 + ν₂(3n + 1)` standard steps.

This is the formal bridge between the accelerated map `T`
(`CollatzResearch.Basic.acceleratedStep`) and the standard map `C`
(`CollatzResearch.Dynamics.standardStep`) on the odd domain.

**Proof sketch.** By induction on `k = ν₂(3n + 1)`.
- Base case `k = 1`: `3n + 1 = 2 * m` with `m` odd, so `C(n) = 3n + 1 = 2m`,
  `C²(n) = m = T(n) = (3n + 1) / 2¹`.
- Inductive case `k = m + 1`: `3n + 1 = 2^{m+1} * p` for odd `p`. By the
  inductive hypothesis on `k' = m`, `C^{1+m}(n) = 2 * p`. Then
  `C^{2+m}(n) = C(2 * p) = p = T(n)`.

The key observation is that each standard step `C` divides by 2 until
the value is odd, and the count of standard steps required to reach
the odd part is exactly `1 + ν₂(3n + 1)`.
-/
theorem acceleratedStep_equiv_standardStep (n : Nat) (h : Odd n) :
    standardTrajectory n (1 + (3 * n + 1).factorization 2) = acceleratedStep n := by
  -- TODO: complete the proof. The induction on (3n+1).factorization 2
  -- requires a lemma that `2^(n.factorization p) ∣ n` (the same blocker
  -- as `acceleratedStep_positive_of_odd` in Story 02).
  sorry

/-- If an accelerated trajectory reaches `1`, the corresponding standard
trajectory also reaches `1`.

Forward direction of the standard ↔ accelerated equivalence at
trajectory level: a finite accelerated witness to convergence lifts
to a finite standard witness.

**Proof sketch.** Induction on the accelerated-trajectory length `m`.
- Base case `m = 0`: `trajectory n 0 = n = 1`, so `n = 1` and
  `standardTrajectory 1 0 = 1`.
- Inductive case `m = k + 1`: from `trajectory n (k+1) = 1` and the
  inductive hypothesis on `k`, there exists `m''` with
  `standardTrajectory (trajectory n k) m'' = 1`. By
  `acceleratedStep_equiv_standardStep` (which establishes that
  `T(trajectory n k)` equals `standardTrajectory (trajectory n k) (1 + k₂)`),
  set `m' = m'' + 1 + k₂` and use `standardTrajectory_succ` to chain.
-/
theorem acceleratedTrajectory_reaches_one_implies_standard (n m : Nat)
    (h : trajectory n m = 1) : ∃ m', standardTrajectory n m' = 1 := by
  -- TODO: complete the proof. Depends on `acceleratedStep_equiv_standardStep`
  -- (the forward equivalence) plus induction on the accelerated length.
  sorry

end CollatzResearch
