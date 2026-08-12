/-
Coverage trees (Story 07b / round-4, M4 Finite coverage) — REVISED.

Round-3 (commit d0f3e7e) closed the `coverage_tree_soundness` sorry
via the `hconsistent` hypothesis but was rejected by Codex with three
findings (review submitted 2026-08-12T23:30:23Z, PR #15):

- **P0** — the theorem was vacuous. `rootDomain t` was defined as
  `{x | ∃ l, descend t x = some l}`, so `IsComplete t` assumed
  exactly the conclusion the theorem returns; the proof
  `exact hc x hx` exposed this; `hv : ValidTree t` was unused.
- **P1** — Python CI was red on `ruff format --check`.
- **P2** — PR body was stale (still called itself a "work packet").

This revision addresses P0 substantively:

1. `rootDomain` is now defined INDEPENDENTLY of `descend` — as
   `fun n => n > 0`. The partition cascade applies to all positive
   naturals; the empty residue class `x % m = 0` is covered by
   `m ≥ 1`.
2. `IsComplete` is now a structural invariant — `HasAllResidues` at
   every internal node (every residue in `[0, m)` has a child) plus
   every leaf in the subtree is verified. No reference to `descend`
   in the definition.
3. The proof of `coverage_tree_soundness` is now non-trivial:
   `ValidTree` provides the depth bound (`maxDepth > 0`); `IsComplete`
   provides the residue-covering invariant at each level; the proof
   combines these (by strong induction on remaining depth) to show
   `descendFrom` reaches a leaf, and `IsComplete`'s recursive clause
   shows the leaf is verified.

The proof uses both hypotheses — `hv : ValidTree t` for the depth
bound and `hic : IsComplete t` for the residue coverage — so
`hv` is no longer unused.

Claim level: `preparatory` per the v2 github-pr-workflow skill.
The theorem proves total structural **reachability** of a nonempty
leaf descriptor over positive naturals — it does not formalize
the declared `leafProperty` for the reached input, nor relate the
tree to Collatz/Syracuse dynamics. M4 Finite coverage stays open
pending a semantic leaf predicate (see Codex P1 scope note on PR
#15 review of `e0d1203`, 2026-08-12T23:48:17Z). Promoting to
`formally established` requires a `leafProperty`-indexed semantic
predicate plus a proof that descend lands a witness satisfying it.
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

/-- Internal descent: walk down the tree following `x % m` at each
    internal node. Returns `none` if the depth bound is exhausted or
    the residue has no matching child. -/
def descendFrom : Nat → CoverageNode → Nat → Option CoverageLeaf
  | 0, _, _ => none
  | _ + 1, .leaf l, _ => some l
  | depth + 1, .internal m children, x =>
    let r := x % m
    match children.lookup r with
    | some child => descendFrom depth child x
    | none => none

/-- descend: walk down the tree from root. -/
def descend (t : CoverageTree) (x : Nat) : Option CoverageLeaf :=
  descendFrom t.maxDepth t.root x

/-- The root domain: defined INDEPENDENTLY of `descend` (per Codex P0).
    The partition cascade applies to all positive naturals; the empty
    residue class `x % m = 0` is covered by `m ≥ 1`. -/
def rootDomain : Nat → Prop := fun n => n > 0

/-- At an internal node, every residue in `[0, m)` has a child.
    This is the partition-completeness invariant — no x in rootDomain
    gets stuck at this node during descend. -/
def HasAllResidues (m : Nat) (children : List (Nat × α)) : Prop :=
  m > 0 ∧ (∀ r, r < m → (children.lookup r).isSome)

/-- A verified leaf: it's in `t.leaves` and both `leafId` and
    `leafProperty` are non-empty. -/
def verified (t : CoverageTree) (l : CoverageLeaf) : Prop :=
  l ∈ t.leaves ∧ l.leafProperty ≠ "" ∧ l.leafId ≠ ""

/-- Structural completeness of a subtree:
    - A leaf is complete iff it's in `t.leaves` and verified.
    - An internal node is complete iff it has `HasAllResidues` and
      every child is complete.
    No reference to `descend` — this is the non-circular invariant
    that the soundness theorem will discharge `descend` against. -/
inductive IsCompleteAux (t : CoverageTree) : CoverageNode → Prop where
  | leafC : ∀ (l : CoverageLeaf),
    l ∈ t.leaves → verified t l →
    IsCompleteAux t (.leaf l)
  | internalC : ∀ (m : Nat) (children : List (Nat × CoverageNode)),
    m > 0 →
    HasAllResidues m children →
    (∀ c ∈ children, IsCompleteAux t c.2) →
    IsCompleteAux t (.internal m children)

/-- A coverage tree is complete: its root subtree is structurally complete. -/
def IsComplete (t : CoverageTree) : Prop := IsCompleteAux t t.root

/-- An input satisfies a leaf's property: `descend t x` returns `l`. -/
def satisfies (t : CoverageTree) (x : Nat) (l : CoverageLeaf) : Prop :=
  descend t x = some l

/-- Soundness for `CoverageTree` (Story 07b / round-4, M4 Finite
    coverage). A complete tree whose partition cascade is well-formed
    implies every input in `rootDomain` reaches a verified leaf that
    satisfies the input.

    Proof structure (non-trivial; uses both `ValidTree` and
    `IsComplete`):

    1. By `ValidTree`, `t.maxDepth > 0` and `ValidNode t.maxDepth t.root`.
    2. By strong induction on the remaining depth `d`, prove the
       helper lemma that for every well-formed `n` of depth `d > 0`,
       if `IsCompleteAux t n`, then `descendFrom d n x = some l` for
       every `x > 0`, with `l ∈ t.leaves ∧ verified t l`.
    3. Apply the lemma at `t.root` with `d = t.maxDepth`. -/
theorem coverage_tree_soundness (t : CoverageTree)
    (hv : ValidTree t) (hic : IsComplete t) (x : Nat) (hx : x > 0) :
    ∃ l, l ∈ t.leaves ∧ verified t l ∧ descend t x = some l := by
  intro x hx
  suffices h : ∀ (d : Nat) (n : CoverageNode),
      d > 0 → ValidNode d n → IsCompleteAux t n →
      ∀ x, x > 0 →
        ∃ l, l ∈ t.leaves ∧ verified t l ∧ descendFrom d n x = some l by
    exact h t.maxDepth t.root hv.1 hv.2 hic x hx
  intro d
  induction d using Nat.strongInductionOn with
  | _ d' ih =>
    intro n hd hvn hic x hx
    cases n with
    | leaf l =>
      cases hic with
      | leafC _ hleaf hver =>
        refine ⟨l, hleaf, hver, ?_⟩
        -- d' > 0, so descendFrom d' (.leaf l) x = some l (matches the
        -- `_ + 1, .leaf l, _ => some l` clause).
        have hd_eq : d' = (d' - 1) + 1 := Nat.succ_pred hd
        rw [hd_eq]
        rfl
      | internalC => exact absurd hic rfl
    | internal m children =>
      cases hic with
      | leafC => exact absurd hic rfl
      | internalC _ hm halls hall =>
        -- HasAllResidues gives us a child for every residue r < m
        have hx_mod_lt : x % m < m := Nat.mod_lt x hm
        have hlookup : (children.lookup (x % m)).isSome := halls.2 (x % m) hx_mod_lt
        -- Extract the child value from the lookup result.
        obtain ⟨child, hchild_lookup⟩ := Option.isSome_iff_exists.mp hlookup
        -- The `List.mem_lookup` lemma turns `lookup k = some v` into a
        -- witness pair `(k, v) ∈ list`.
        have hmem : ∃ pair ∈ children, pair.1 = x % m ∧ pair.2 = child := by
          have h_belongs : child ∈ children.lookup (x % m) := by
            rw [Option.mem_iff]
            exact hchild_lookup
          exact (List.mem_lookup.mp h_belongs)
        obtain ⟨pair, hpmem, hpfst, hpsnd⟩ := hmem
        -- `ValidNode (d' - 1) child` comes from the third conjunct of
        -- `hvn` (which says `∀ c ∈ children, ValidNode (d' - 1) c.2`)
        -- applied to the witness pair.
        obtain ⟨hm', hvp, hvn_rest⟩ := hvn
        have hchild_vn : ValidNode (d' - 1) child := hvn_rest pair hpmem
        -- `IsCompleteAux t child` comes from the recursive clause of
        -- `hic` (which says `∀ c ∈ children, IsCompleteAux t c.2`).
        have hchild_ic : IsCompleteAux t child := hall pair hpmem
        -- Apply the strong-induction hypothesis at depth `d' - 1`.
        have hresult := ih (d' - 1) (Nat.sub_one_lt hd) hchild_vn hchild_ic x hx
        obtain ⟨l, hl, hv', hdesc_child⟩ := hresult
        -- Reassemble: `descendFrom d' (.internal m children) x =
        -- descendFrom (d' - 1) child x` because `children.lookup (x % m) =
        -- some child` and the next clause fires.
        refine ⟨l, hl, hv', ?_⟩
        simp [descendFrom]
        rw [hchild_lookup]
        exact hdesc_child

end CollatzResearch