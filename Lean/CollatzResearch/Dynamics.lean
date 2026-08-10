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

The blockers are:
- `standardStep_positive`: proving `0 < n / 2` from `n` even and
  `n > 0` requires `0 < 2 * k → 0 < k` (where `n = 2 * k`); `omega`
  does not see this without `Nat.pos_of_mul_pos_right` or similar.
- `acceleratedStep_positive_of_odd`: proving `2^ν₂(3n+1) | 3n+1`
  requires unfolding `(2^k).factorization` through `factorization_pow`
  + `Finsupp.smul_apply` + `Finsupp.single_apply` + `Prime.factorization`
  (for `Prime 2`); the chain is mechanically correct but the rewrite
  unfolds don't quite close under `simp` in this Mathlib build.

Per Codex review feedback, these are tracked for a release-blocking
follow-up (Story 02b / 03b) that completes both positivity proofs in
one pass, then merges them together with the equivalence proofs from
`CollatzResearch.Equivalence`.
-/

namespace CollatzResearch

/-- The standard (unaccelerated) Collatz map: n ↦ n/2 if even, 3n+1 if odd. -/
def standardStep (n : Nat) : Nat :=
  if n % 2 = 0 then n / 2 else 3 * n + 1

/-- Strict positivity on `Nat`. -/
def Positive (n : Nat) : Prop := 0 < n

/-- Standard step preserves positivity on the positive domain.

For the even branch, `n` is positive even, so `n ≥ 2` (since `1` is odd)
and `n / 2 ≥ 1 > 0`. For the odd branch, `3n + 1` is a positive
successor (`Nat.add` with `1` reduces to `Nat.succ`, so `Nat.succ_pos`
applies directly).
-/
theorem standardStep_positive (n : Nat) (h : Positive n) :
    Positive (standardStep n) := by
  -- TODO: closing step needs `0 < 2 * k → 0 < k`. See file header.
  sorry

/-- The accelerated Collatz step `T(n)` preserves positivity on the odd
domain.

The odd precondition is necessary: `T(0) = 1` is well-defined but
`T(n)` for non-positive `n` is not part of the project's contract.
This theorem is the first formal bridge between the accelerated map
(`CollatzResearch.Basic.acceleratedStep`) and the standard map
(`standardStep`) on the odd domain — it is the precondition for
Story 03's one-step equivalence theorem.
-/
theorem acceleratedStep_positive_of_odd (n : Nat) (h_odd : Odd n) :
    Positive (acceleratedStep n) := by
  -- TODO: closing step needs the Finsupp / factorization_pow chain.
  -- See file header.
  sorry

end CollatzResearch
