import Mathlib
import CollatzResearch.Basic

/-!
# Symbolic affine executor

The accelerated Collatz map `T(n) = (3n + 1) / 2^{ν₂(3n + 1)}` and its
iterations can be represented as affine maps over ℤ. This module:

1. Defines `AffineMap` as a triple `(a, b, k)` representing
   `n ↦ (a * n + b) / 2^k`.
2. Defines composition: `(a₁, b₁, k₁) ∘ (a₂, b₂, k₂) =
   (a₁ * a₂, a₁ * b₂ + b₁ * 2^k₂, k₁ + k₂)`.
3. Proves composition is associative and has identity laws.
4. Defines `BranchWord := List ℕ` (a sequence of two-adic valuations).
5. Defines the affine map induced by a branch word (right-fold compose
   over single-step maps).
6. Defines `appliesTo`: a word applies to `n` iff `n` is positive odd
   and each step's valuation matches `ν₂(3nᵢ + 1)`.

This module makes no convergence, cycle-exclusion, or global descent
claim. It is the symbolic-executor foundation for Story 05 (residue
partitions and certificate schema).

See ADR-0007 for the design decision on the integer (vs. rational)
representation with explicit denominator exponent.
-/

namespace CollatzResearch

/-- An affine map `n ↦ (a * n + b) / 2^k` over `ℤ`.

The divisibility condition `2^k ∣ (a * n + b)` is a precondition on the
input `n`, not a property of the map itself. The `apply` function uses
`Int.ediv` (Euclidean division); the caller is responsible for the
divisibility precondition when applying to integer values. -/
structure AffineMap where
  a : ℤ
  b : ℤ
  k : ℕ

/-- The identity affine map `n � n`. -/
def AffineMap.id : AffineMap := ⟨1, 0, 0⟩

/-- The single-step affine map for a given two-adic valuation `k`:
`n ↦ (3n + 1) / 2^k`. Valid on the positive odd domain when
`k = ν₂(3n + 1)`. The `k ≥ 1` precondition is not enforced at the
type level; it is a documented contract on the caller. -/
def AffineMap.step (k : ℕ) : AffineMap :=
  ⟨3, 1, k⟩

/-- Apply the affine map. Uses `Int.ediv`; the divisibility precondition
is a caller obligation. -/
def AffineMap.apply (m : AffineMap) (n : ℤ) : ℤ :=
  (m.a * n + m.b) / (2 ^ m.k : ℤ)

/-- Compose two affine maps: `(m₁ ∘ m₂).apply n = m₁.apply (m₂.apply n)`. -/
def AffineMap.comp (m₁ m₂ : AffineMap) : AffineMap :=
  { a := m₁.a * m₂.a
    b := m₁.a * m₂.b + m₁.b * (2 ^ m₂.k : ℤ)
    k := m₁.k + m₂.k }

theorem AffineMap.comp_assoc (m₁ m₂ m₃ : AffineMap) :
    (m₁.comp m₂).comp m₃ = m₁.comp (m₂.comp m₃) := by
  cases m₁; cases m₂; cases m₃
  simp only [AffineMap.comp]
  ring

@[simp] theorem AffineMap.comp_id_left (m : AffineMap) :
    AffineMap.id.comp m = m := by
  cases m
  simp only [AffineMap.comp, AffineMap.id]
  ring

@[simp] theorem AffineMap.comp_id_right (m : AffineMap) :
    m.comp AffineMap.id = m := by
  cases m
  simp only [AffineMap.comp, AffineMap.id]
  ring

/-- A branch word: a sequence of two-adic valuations. -/
abbrev BranchWord := List ℕ

/-- The empty branch word. -/
def BranchWord.empty : BranchWord := []

/-- The affine map induced by a branch word: left-fold of
`AffineMap.step` composed with `AffineMap.id`.

The composed map applies the steps in the order they appear in the
list: the first valuation's step runs first, then the second, etc.
The recursion is built in reverse so the composition convention
`m₁.comp m₂` (= "apply m₂ first, then m₁") produces the correct
left-to-right order. -/
@[simp] def BranchWord.toAffine : BranchWord → AffineMap
  | [] => AffineMap.id
  | k :: rest => (BranchWord.toAffine rest).comp (AffineMap.step k)

/-- A branch word applies to input `n` (a positive odd integer) when
each step's valuation matches `ν₂(3nᵢ + 1)`. -/
@[simp] def BranchWord.appliesTo : BranchWord → ℕ → Prop
  | [], n => n > 0 ∧ n % 2 = 1
  | k :: rest, n =>
    n > 0 ∧ n % 2 = 1 ∧
    twoAdicValuation (3 * n + 1) = k ∧
    BranchWord.appliesTo rest (Nat.div (3 * n + 1) (2 ^ k))

end CollatzResearch
