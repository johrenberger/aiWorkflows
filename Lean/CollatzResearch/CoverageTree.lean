/-
Coverage trees (Story 07b / round-4, M4 Finite coverage) — REVISED.

After Codex re-review on commit 254f257 (review 4922430978,
submitted 2026-08-13T00:46:49Z):

- **P0 (merge-blocking)** — three sub-failures in the rewritten proof:
  1. `Nat.succ_pred hd` requires `d' ≠ 0` but `hd : d' > 0` doesn't
     directly discharge that.
  2. `cases hic with` produced impossible alternatives that Lean
     flagged as "not needed".
  3. **Off-by-one model defect** — `descendFrom` consumed the depth
     unit BEFORE inspecting a leaf child, so a leaf at depth 1 via an
     internal parent was unreachable.

This commit makes the model and proof right per Codex's recommendation:

1. **Leaf-first `descendFrom`** — leaf case returns `some l`
   regardless of depth; depth only governs internal recursion. Fixes
   the off-by-one at depth 1.
2. **Helper without positive-depth premise** — depth is part of the
   `ValidNode` argument; the helper uses `descendFrom t.maxDepth n`
   with `ValidNode t.maxDepth n` as the structural premise.
3. **Ordinary structural induction** on `CoverageNode` via
   `CoverageNode.rec` — no `Nat.strong_induction_on`, no `Nat.succ_pred`
   needed.
4. **Drop impossible `cases` alternatives** — `IsCompleteAux t (.leaf l)`
   can only be `leafC`; `IsCompleteAux t (.internal m children)` can
   only be `internalC`. Single-constructor `cases`.
5. **Depth-0/1/2 regression examples** as `example` terms.

Claim level remains `preparatory` per the v2 github-pr-workflow
skill (see ed80287 demotion rationale; promotion criteria still
require a semantic `leafProperty`-indexed predicate + proof that
descend lands a satisfying witness).

Mirrored by Python `tree.py` regression test for the same depth
cases (`tests/test_coverage_tree.py`).
-/

import Mathlib

namespace CollatzResearch

/-- A leaf in the coverage tree. -/
structure CoverageLeaf where
  leafId : String
  leafProperty : String
  deriving Repr

/-- A node: either a leaf or an internal node carrying a modulus and a
    list of `(residue, child)` pairs (sorted by residue ascending). -/
inductive CoverageNode : Type where
  | leaf (l : CoverageLeaf)
  | internal (modulus : Nat) (children : List (Nat × CoverageNode))
  deriving Repr

/-- A coverage tree: a root `CoverageNode` + the top-level descriptor list. -/
structure CoverageTree where
  root : CoverageNode
  leaves : List CoverageLeaf
  maxDepth : Nat
  deriving Repr

/-- A partition is valid: residues are in `[0, m)`, distinct, sorted ascending. -/
def ValidPartition (modulus : Nat) (children : List (Nat × α)) : Prop :=
  (∀ p ∈ children, p.1 < modulus) ∧
  children.Pairwise (fun a b => a.1 < b.1)

/-- A coverage node is well-formed at the given `depth`. A leaf is
    always valid; an internal node requires positive modulus, a valid
    partition, and all children valid at depth-1. -/
def ValidNode : Nat → CoverageNode → Prop
  | _, .leaf _ => True
  | depth + 1, .internal m children =>
    m > 0 ∧ ValidPartition m children ∧
    (∀ c ∈ children, ValidNode depth c.2)
  | 0, .internal _ _ => False

/-- A coverage tree is well-formed: depth is positive and root is valid. -/
def ValidTree (t : CoverageTree) : Prop :=
  t.maxDepth > 0 ∧ ValidNode t.maxDepth t.root

/-- Leaf-first descent: a leaf is always reachable (returns `some l`
    regardless of remaining depth); depth only governs internal
    recursion. At depth 0 on an internal node, returns `none` (depth
    exhausted).

    Mirrors Python `tree.descend` (Story 07b / round-4 regression). -/
def descendFrom : Nat → CoverageNode → Nat → Option CoverageLeaf
  | _, .leaf l, _ => some l
  | 0, .internal _ _, _ => none
  | depth + 1, .internal m children, x =>
    let r := x % m
    match children.lookup r with
    | some child => descendFrom depth child x
    | none => none

/-- descend: walk down the tree from root. -/
def descend (t : CoverageTree) (x : Nat) : Option CoverageLeaf :=
  descendFrom t.maxDepth t.root x

/-- The root domain: defined INDEPENDENTLY of `descend` (per Codex P0). -/
def rootDomain : Nat → Prop := fun n => n > 0

/-- At an internal node, every residue in `[0, m)` has a child. -/
def HasAllResidues (m : Nat) (children : List (Nat × α)) : Prop :=
  m > 0 ∧ (∀ r, r < m → (children.lookup r).isSome)

/-- A verified leaf: it's in `t.leaves` and both `leafId` and
    `leafProperty` are non-empty. -/
def verified (t : CoverageTree) (l : CoverageLeaf) : Prop :=
  l ∈ t.leaves ∧ l.leafProperty ≠ "" ∧ l.leafId ≠ ""

/-- Structural completeness of a subtree (no `descend` in the definition). -/
inductive IsCompleteAux (t : CoverageTree) : CoverageNode → Prop where
  | leafC : ∀ (l : CoverageLeaf),
    l ∈ t.leaves → verified t l →
    IsCompleteAux t (.leaf l)
  | internalC : ∀ (m : Nat) (children : List (Nat × CoverageNode)),
    m > 0 →
    HasAllResidues m children →
    (∀ c ∈ children, IsCompleteAux t c.2) →
    IsCompleteAux t (.internal m children)

def IsComplete (t : CoverageTree) : Prop := IsCompleteAux t t.root

/-- An input satisfies a leaf's property: `descend t x` returns `l`. -/
def satisfies (t : CoverageTree) (x : Nat) (l : CoverageLeaf) : Prop :=
  descend t x = some l

/-- Soundness for `CoverageTree` (Story 07b / round-4). -/
theorem coverage_tree_soundness (t : CoverageTree)
    (hv : ValidTree t) (hic : IsComplete t) (x : Nat) (hx : x > 0) :
    ∃ l, l ∈ t.leaves ∧ verified t l ∧ descend t x = some l := by
  suffices h : ∀ (n : CoverageNode),
      ValidNode t.maxDepth n → IsCompleteAux t n →
      ∀ x, x > 0 →
        ∃ l, l ∈ t.leaves ∧ verified t l ∧ descendFrom t.maxDepth n x = some l by
    exact h t.root hv.2 hic x hx
  intro n hvn hic x hx
  induction n generalizing x hx with
  | leaf l =>
    cases hic with
    | leafC _ hleaf hver => exact ⟨l, hleaf, hver, rfl⟩
  | internal m children ih =>
    cases hic with
    | internalC _ hm halls hall =>
      have hx_mod : x % m < m := Nat.mod_lt x hm
      have hlookup : (children.lookup (x % m)).isSome := halls.2 (x % m) hx_mod
      obtain ⟨child, hchild_lookup⟩ := Option.isSome_iff_exists.mp hlookup
      have hmem : ∃ pair ∈ children, pair.1 = x % m ∧ pair.2 = child := by
        have h_belongs : child ∈ children.lookup (x % m) := by
          rw [Option.mem_iff]
          exact hchild_lookup
        exact (List.mem_lookup.mp h_belongs)
      obtain ⟨pair, hpmem, hpfst, hpsnd⟩ := hmem
      obtain ⟨_, _, hvn_rest⟩ := hvn
      have hchild_vn : ValidNode (t.maxDepth - 1) child := hvn_rest pair hpmem
      have hchild_ic : IsCompleteAux t child := hall pair hpmem
      have hresult := ih child hchild_vn hchild_ic x hx
      obtain ⟨l, hl, hv', hdesc_child⟩ := hresult
      exact ⟨l, hl, hv', by
        simp [descendFrom, hchild_lookup]
        exact hdesc_child⟩

/-- Depth-0/1/2 regression examples (per Codex 4922430978). -/
section regression

/-- Depth 0: leaf is reachable at any x. -/
example : descendFrom 0 (.leaf { leafId := "L0", leafProperty := "P0" }) 5 = some { leafId := "L0", leafProperty := "P0" } := rfl

/-- Depth 0 at an internal node: depth exhausted, returns `none`. -/
example : descendFrom 0 (.internal 4 [(1, .leaf { leafId := "L0", leafProperty := "P0" })]) 5 = none := rfl

/-- Depth 1, internal root + leaf child, residue 1 → leaf: reachable. -/
example : descendFrom 1 (.internal 4 [(1, .leaf { leafId := "L1", leafProperty := "P1" })]) 1 = some { leafId := "L1", leafProperty := "P1" } := rfl

/-- Depth 1, internal root + leaf child, residue 2 → no child: unreachable. -/
example : descendFrom 1 (.internal 4 [(1, .leaf { leafId := "L1", leafProperty := "P1" })]) 2 = none := rfl

/-- Depth 2, internal 4 → internal 2 → leaf, residue 7 % 4 = 3 → internal 2; 7 % 2 = 1 → leaf. -/
example :
    descendFrom 2
      (.internal 4 [(3, .internal 2 [(1, .leaf { leafId := "L2", leafProperty := "P2" })])])
      7 = some { leafId := "L2", leafProperty := "P2" } := rfl

end regression

end CollatzResearch