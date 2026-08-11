import CollatzResearch.Basic
import CollatzResearch.Importer

/-!
# Certificate interface

Certificate parsing is deliberately outside Lean in the initial bootstrap. Lean predicates
here are the stable target for a future verified importer or generated theorem files.

**Proof status (2026-08-11, Story 06 — re-scoped as preparatory):**

This module provides only the **structural witness infrastructure** for
local-descent certificates. It does **not** establish the formal
acceptance-to-`Valid` bridge that would relate the Python `check_certificate`
execution / parsed JSON to a Lean witness satisfying `Valid`. That bridge is
the subject of Story 06b.

Per the PR #10 Codex review (P0): the previous `DescentWitness.Valid.sound`
projection was a re-extraction of `h.ends_at` and `h.strict_descent`, not a
soundness theorem relating the Python checker to `Valid`. The re-scope
deletes that projection and confines Story 06 to structural lemmas; Story 06b
will supply the JSONL→witness→`Valid` bridge (and the Lean-internal
decidability mirror `DescentWitness.checkCertificate` if useful).

Concrete contents:

- Structural witness predicates and interface lemmas: complete.
- `Valid` requires odd-positive start (P1 from PR #10 Codex review): matches
  Python's `accelerated_step`, which rejects even or non-positive inputs.
- `acceleratedStep_odd_of_odd` states odd-preservation for one accelerated step;
  admitted via `sorry` because the underlying chain through
  `Nat.factorization_div` / `Nat.factorization_pow` is the same Mathlib work
  blocking `Dynamics.lean::acceleratedStep_positive_of_odd`. Tracked as part of
  the Story 02c/03c Mathlib workstream, not Story 06b.
- `DescentWitness.trajectory_odd` is the consequence along the full trajectory
  (induction on `steps` using `acceleratedStep_odd_of_odd`).
- **1 `sorry` admitted** in `acceleratedStep_odd_of_odd` (propagating through
  `trajectory_odd`). The release-relevant Lean modules carry 7 `sorry` total:
  4 in `Dynamics.lean` + `Equivalence.lean` (Story 02b/03b), 2 in `Affine.lean`
  (Story 04), and 1 in this file (odd-preservation; same Mathlib blocker as
  `Dynamics.lean`).
-/

namespace CollatzResearch

structure DescentWitness where
  start : Nat
  steps : Nat
  target : Nat
  deriving Repr, DecidableEq

/-- A witness establishes a finite, checkable trajectory claim on the odd-positive
domain enforced by Python's `accelerated_step` (which rejects even or non-positive
inputs).

The four conjuncts, in order:
1. `0 < start` — positivity (a precondition for the integer arithmetic).
2. `Odd start` — odd-domain (matches Python's `accelerated_step` precondition).
3. `trajectory start steps = target` — declared endpoint matches the canonical
   accelerated trajectory from `start` of length `steps`.
4. `target < start` — strict descent (the witness claims a finite descent). -/
def DescentWitness.Valid (w : DescentWitness) : Prop :=
  0 < w.start ∧ Odd w.start ∧ trajectory w.start w.steps = w.target ∧ w.target < w.start

/-- A valid witness has the declared trajectory endpoint. -/
theorem DescentWitness.Valid.ends_at (w : DescentWitness) (h : w.Valid) :
    trajectory w.start w.steps = w.target :=
  h.2.2.1

/-- A valid witness is a strict descent for its declared start. -/
theorem DescentWitness.Valid.strict_descent (w : DescentWitness) (h : w.Valid) :
    w.target < w.start :=
  h.2.2.2

/-- A valid witness has a positive, odd start (matching Python's `accelerated_step`). -/
theorem DescentWitness.Valid.start_pos_odd (w : DescentWitness) (h : w.Valid) :
    0 < w.start ∧ Odd w.start :=
  ⟨h.1, h.2.1⟩

/-- `acceleratedStep` preserves oddness on the odd domain.

For odd `n`, `3n+1` is even, so `v2(3n+1) ≥ 1`. The quotient
`(3n+1)/2^v2(3n+1)` is the maximal odd divisor of `3n+1`, hence odd.

Admitted via `sorry`: the factorization chain through `Nat.factorization_div`
and `Nat.factorization_pow` is the same Mathlib work blocking
`Dynamics.lean::acceleratedStep_positive_of_odd`. Tracked as part of the
Story 02c/03c Mathlib workstream.
-/
theorem acceleratedStep_odd_of_odd (n : Nat) (h : Odd n) :
    Odd (acceleratedStep n) := by
  sorry

/-- Oddness is preserved along the trajectory (induction on `steps`). -/
theorem DescentWitness.trajectory_odd (start k : Nat) (h : Odd start) :
    Odd (trajectory start k) := by
  induction k with
  | zero => exact h
  | succ k ih => exact acceleratedStep_odd_of_odd _ ih

/-- The `LeanAccepts` predicate: the Lean-side mirror of "the Python checker
accepted this certificate". This is what `check_certificate_sound` ranges
over.

**Stub status.** For now the predicate is defined as `DescentWitness.Valid`
itself (the trivial case). The real implementation will incorporate the
parser result (from `Importer.lean`) + a recomputed SHA-256 digest
(`Digest.lean`, FFI target TBD) + a recomputed trajectory
(`CollatzResearch.Basic.trajectory`). The bridge theorem will then
prove `LeanAccepts w → w.Valid` non-trivially — reconstructing `Valid`
from the imported fields **independently** (the anti-circularity
property called out in `PLAN.md` Story 06b's risk section). -/
def LeanAccepts (w : DescentWitness) : Prop :=
  DescentWitness.Valid w

/-- The formal acceptance-to-`Valid` bridge (Story 06b acceptance criterion 4).

`LeanAccepts w` (from `Importer.lean`) is the Lean-side mirror of "the
Python checker accepted this certificate". It is the predicate the
bridge theorem ranges over. The full predicate will incorporate:
  (a) the JSONL parser result (the imported `DescentWitness`),
  (b) the recomputed SHA-256 digest over the canonical proof-bearing
      fields (matching `python/collatz_research/canonical.py`),
  (c) the recomputed accelerated trajectory via
      `CollatzResearch.Basic.trajectory`,
combined with the structural constraints encoded in `Valid`.

`check_certificate_sound` is the formal statement that acceptance
implies the structural `Valid` predicate. This is what the PR #10
Codex review (P0) carved out from the original `Valid.sound`
projection: the new theorem is *generic* over `w : DescentWitness`
(no test-enumeration discharge) and is the *bridge* between the
Python checker's accept/reject decision and the Lean `Valid`
predicate.

**Current status (Story 06b step 1.4):** the theorem shape is correct
(quantified over all `w : DescentWitness`, statement matches the
P0 carve-out). The proof is currently `intro h; exact h` because
`LeanAccepts` is currently defined as `DescentWitness.Valid` itself
(a placeholder; see `Importer.lean`). Once `LeanAccepts` is expanded
to incorporate the parser result + recomputed digest + recomputed
trajectory, the proof must reconstruct `Valid` from those imported
fields **independently** — the anti-circularity property called out
in `PLAN.md` Story 06b's risk section. Specifically, the proof
cannot use `Valid` to discharge `LeanAccepts`; it must build `Valid`
from the imported fields without circular reference. That is the
substantive work that closes the M3 "formally established" claim
language. -/
theorem check_certificate_sound (w : DescentWitness) : LeanAccepts w → w.Valid := by
  intro h
  exact h

end CollatzResearch
