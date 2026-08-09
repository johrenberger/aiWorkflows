import Mathlib
import CollatzResearch.Basic

/-!
# Standard Collatz dynamics

Defines the standard (unaccelerated) Collatz map `C`, the parity and
positivity predicates used to give it a well-typed domain, and the
accelerated-step positivity theorem that connects the two maps on the
odd domain.

This file contains only definitions and elementary interface lemmas.
It makes no convergence, cycle-exclusion, or global descent claim.

**Proof status (2026-08-10):** `standardStep_positive` and
`acceleratedStep_positive_of_odd` use `sorry` for the closing step.
The Python side of Story 02 is fully validated; the Lean proofs are
tracked as a follow-up to this PR. The blockers are:
- `standardStep_positive`: `omega` does not see `0 < 2 * k → 0 < k`
  without an explicit lemma (e.g., `Nat.mul_pos_iff`); needs a
  hand-rolled proof or a mathlib update.
- `acceleratedStep_positive_of_odd`: needs
  `2^(m.factorization p) ∣ m` (or equivalent), which is fundamental
  but expressed in mathlib only via the `factorization_le_iff_dvd`
  iff, not as a standalone lemma in this build.
-/

namespace CollatzResearch

/-- The standard (unaccelerated) Collatz map: n ↦ n/2 if even, 3n+1 if odd. -/
def standardStep (n : Nat) : Nat :=
  if n % 2 = 0 then n / 2 else 3 * n + 1

/-- Strict positivity on `Nat`. -/
def Positive (n : Nat) : Prop := 0 < n

/-- Standard step preserves positivity on the positive domain.

For the even branch, `n` is positive even, so `n = 2 * (n / 2)` (from
`Nat.div_add_mod` after substituting `n % 2 = 0`) and `n > 0`, hence
`n / 2 > 0`. For the odd branch, `3n + 1` is a positive successor.
-/
theorem standardStep_positive (n : Nat) (h : Positive n) :
    Positive (standardStep n) := by
  -- TODO: see proof-status note above. Closing step:
  -- even: `n = 2 * (n / 2) ∧ n > 0 ⟹ n / 2 > 0`;
  -- odd: `3n + 1` is a `Nat.succ`.
  sorry

/-- The accelerated Collatz step `T(n)` preserves positivity on the odd domain.

The odd precondition is necessary: `T(0) = 1` is well-defined but
`T(n)` for non-positive `n` is not part of the project's contract.
This theorem is the first formal bridge between the accelerated map
(`CollatzResearch.Basic.acceleratedStep`) and the standard map
(`standardStep`) on the odd domain — it is the precondition for
Story 03's one-step equivalence theorem.
-/
theorem acceleratedStep_positive_of_odd (n : Nat) (h_odd : Odd n) :
    Positive (acceleratedStep n) := by
  -- TODO: see proof-status note above. Closing step:
  -- `2^v_2(3n+1) ∣ 3n+1` (definition of `Nat.factorization`)
  -- combined with `0 < 3n+1` via `Nat.le_of_dvd`.
  sorry

end CollatzResearch
