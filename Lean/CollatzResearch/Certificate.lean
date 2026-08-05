import CollatzResearch.Basic

/-!
# Certificate interface

Certificate parsing is deliberately outside Lean in the initial bootstrap. Lean predicates
here are the stable target for a future verified importer or generated theorem files.
-/

namespace CollatzResearch

structure DescentWitness where
  start : Nat
  steps : Nat
  target : Nat
  deriving Repr, DecidableEq

/-- A witness establishes only a finite, checkable trajectory claim. -/
def DescentWitness.Valid (w : DescentWitness) : Prop :=
  0 < w.start ∧ trajectory w.start w.steps = w.target ∧ w.target < w.start

end CollatzResearch
