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

/-- A valid local-descent witness has the declared trajectory endpoint. -/
theorem DescentWitness.Valid.ends_at (w : DescentWitness) (h : w.Valid) :
    trajectory w.start w.steps = w.target :=
  h.2.1

/-- A valid local-descent witness is a strict descent for its declared start. -/
theorem DescentWitness.Valid.strict_descent (w : DescentWitness) (h : w.Valid) :
    w.target < w.start :=
  h.2.2

/-- Checker soundness for local-descent witnesses.

This theorem is generic over the witness; finite test enumeration is not used
as a substitute for the quantified statement.
-/
theorem DescentWitness.Valid.sound (w : DescentWitness) (h : w.Valid) :
    trajectory w.start w.steps = w.target ∧ w.target < w.start :=
  ⟨h.ends_at, h.strict_descent⟩

end CollatzResearch
