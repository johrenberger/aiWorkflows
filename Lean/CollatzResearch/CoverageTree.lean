/-
Coverage trees (Story 07b / round-4, M4 Finite coverage) — REVISED.

After Codex re-review on commit a3f7127 (review 4922482533,
submitted 2026-08-13T00:57:51Z) + CI run 31657397630:

- **P0 (merge-blocking):** the proof used
  `induction depth using Nat.rec generalizing n with` — but `n` is not
  in scope at the induction site, so the parser raised
  `unknown identifier 'n'` at line 140.
  Codex's recommendation: use induction on an explicit `d : Nat` with
  the helper shape `∀ d n, ValidNode d n → IsCompleteAux t n → ...
  descendFrom d n ...`; base `d = 0` eliminates internal nodes via
  `ValidNode` (since `ValidNode 0 (.internal _) = False`); successor
  internal case invokes IH at `d` using child validity from
  `ValidNode (d+1)`.

- **P1 (parser):** `section regression` keyword wasn't being parsed
  correctly in this Lean version. Once the theorem is rewritten to a
  complete syntactic proof, the `section` issue resolves; the
  examples are now placed outside any `section` wrapper.

This commit applies Codex's full recommendation:

1. **Helper without `depth > 0` precondition.** Drops the positive-
   depth premise; the base case (`d = 0`) eliminates internal nodes
   via `ValidNode 0 (.internal _) = False` and the leaf case uses
   `descendFrom 0 (.leaf l) _ = some l` directly.
2. **Dropped `generalizing n` from `Nat.rec`.** The motive is implicit;
   `n` is introduced inside each case via `intro n hvn hic x hx`.
3. **`cases n` (not `induction n`) on `CoverageNode`.** Plain
   pattern matching avoids the nested-inductive elimination issue.
4. **`False.elim hvn` in the base-case internal branch.** The
   contradiction `ValidNode 0 (.internal _) = False` discharges the
   goal via ex falso.
5. **Removed `section regression` wrapper.** The regression examples
   stand alone in the namespace.

Claim level remains `preparatory` per the v2 github-pr-workflow
skill (see ed80287 demotion rationale; promotion criteria still
require a semantic leafProperty-indexed predicate + proof that
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
  suffices h : ∀ (depth : Nat),
      ∀ (n : CoverageNode), ValidNode depth n → IsCompleteAux t n →
      ∀ x, x > 0 →
        ∃ l, l ∈ t.leaves ∧ verified t l ∧ descendFrom depth n x = some l by
    exact h t.maxDepth t.root hv.2 hic x hx
  intro depth
  induction depth using Nat.rec with
  | zero =>
    intro n hvn hic x hx
    cases n with
    | leaf l =>
      cases hic with
      | leafC _ hleaf hver => exact ⟨l, hleaf, hver, rfl⟩
    | internal m children =>
      exact False.elim hvn
  | succ depth' ih =>
    intro n hvn hic x hx
    cases n with
    | leaf l =>
      cases hic with
      | leafC _ hleaf hver => exact ⟨l, hleaf, hver, rfl⟩
    | internal m children =>
      cases hic with
      | internalC _ _ hm halls hall =>
        have hx_mod : x % m < m := Nat.mod_lt x hm
        have hlookup : (children.lookup (x % m)).isSome := halls.2 (x % m) hx_mod
        obtain ⟨child, hchild_lookup⟩ := Option.isSome_iff_exists.mp hlookup
        obtain ⟨before, after, hchildren, _⟩ :=
          List.lookup_eq_some_iff.mp hchild_lookup
        have hpair_mem : (x % m, child) ∈ children := by
          rw [hchildren]
          simp
        obtain ⟨_, _, hvn_rest⟩ := hvn
        have hchild_vn : ValidNode depth' child := by
          exact hvn_rest (x % m, child) hpair_mem
        have hchild_ic : IsCompleteAux t child := by
          exact hall (x % m, child) hpair_mem
        have hresult := ih child hchild_vn hchild_ic x hx
        obtain ⟨l, hl, hv', hdesc_child⟩ := hresult
        refine ⟨l, hl, hv', ?_⟩
        simpa [descendFrom, hchild_lookup] using hdesc_child
  done

/-- Depth-0/1/2 regression examples (per Codex 4922430978). -/

/-- Depth 0: leaf is reachable at any x. -/
example : descendFrom 0 (.leaf { leafId := "L0", leafProperty := "P0" }) 5 = some { leafId := "L0", leafProperty := "P0" } := rfl

/-- Depth 0 at an internal node: depth exhausted, returns `none`. -/
example : descendFrom 0 (.internal 4 [(1, .leaf { leafId := "L0", leafProperty := "P0" })]) 5 = none := rfl

/-- Depth 1, internal root + leaf child, residue 1 → leaf: reachable. -/
example : descendFrom 1 (.internal 4 [(1, .leaf { leafId := "L1", leafProperty := "P1" })]) 1 = some { leafId := "L1", leafProperty := "P1" } := rfl

/-- Depth 1, internal root + leaf child, residue 2 → no child: unreachable. -/
example : descendFrom 1 (.internal 4 [(1, .leaf { leafId := "L1", leafProperty := "P1" })]) 2 = none := rfl

/-- Depth 2, internal 4 → internal 2 → leaf; 7 % 4 = 3, 7 % 2 = 1. -/
example :
    descendFrom 2
      (.internal 4 [(3, .internal 2 [(1, .leaf { leafId := "L2", leafProperty := "P2" })])])
      7 = some { leafId := "L2", leafProperty := "P2" } := rfl

end CollatzResearch
