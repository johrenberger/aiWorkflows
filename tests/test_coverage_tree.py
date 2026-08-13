"""TDD tests for the coverage-tree model + checker (Story 07).

Mutation tests corrupt each field of `sample_tree()` and assert that
`check_tree` raises with the matching stable category. Plus round-trip
JSONL serialization, deterministic-ordering, leaves-consistency,
fail-closed `from_dict` (Codex P2), and the cycle policy.
"""

from __future__ import annotations

import copy
import json

import pytest
from collatz_research.tree import (
    ERR_HAS_CYCLE,
    ERR_INVALID_NODE,
    ERR_LEAF_ID_EMPTY,
    ERR_LEAVES_MISMATCH,
    ERR_NOT_CHILD_TOTAL,
    ERR_NOT_DISJOINT,
    EXPECTED_SCHEMA,
    CoverageLeaf,
    CoverageNode,
    CoverageTree,
    CoverageTreeError,
    check_tree,
    descend,
    deterministic_children,
    from_dict,
    has_child_for_each_declared_residue,
    has_no_cycles,
    is_disjoint,
    leaf_id_non_empty,
    lean_interval,
    leaves_consistent,
    reachable_leaves,
    sample_tree,
    sat,
    to_dict,
    well_formed,
)

# ---- Happy path ----


def test_sample_tree_passes_all_checks():
    tree = sample_tree()
    assert has_child_for_each_declared_residue(tree)
    assert is_disjoint(tree)
    assert leaves_consistent(tree)
    assert has_no_cycles(tree)
    assert leaf_id_non_empty(tree)
    # check_tree raises only on failure; no exception == pass.
    check_tree(tree)


def test_sample_tree_round_trips_through_dict():
    tree = sample_tree()
    d = to_dict(tree)
    # JSON-serializable (one object per JSONL line).
    text = json.dumps(d)
    loaded = json.loads(text)
    tree2 = from_dict(loaded)
    assert to_dict(tree2) == d
    check_tree(tree2)


def test_deterministic_children_order_is_sorted_by_residue():
    tree = sample_tree()
    reversed_children = {r: tree.root.children[r] for r in reversed(list(tree.root.children))}
    reverse_node = CoverageNode(
        modulus=tree.root.modulus,
        partition=tree.root.partition,
        children=reversed_children,
    )
    seen = [r for r, _ in deterministic_children(reverse_node)]
    assert seen == sorted(tree.root.children.keys())


def test_reachable_leaves_match_top_level_leaves():
    """The set of leaves reachable from `root` is exactly `tree.leaves`."""
    tree = sample_tree()
    reachable = set(reachable_leaves(tree.root))
    top = set(tree.leaves)
    assert reachable == top
    assert reachable  # non-empty


# ---- Helpers ----


def _mut(root_mutator, *, max_depth=None) -> CoverageTree:
    """Clone `sample_tree()` and apply a mutator to the root node."""
    base = sample_tree()
    mutated = copy.deepcopy(base)
    root_mutator(mutated.root)
    if max_depth is not None:
        mutated.max_depth = max_depth
    return mutated


# ---- Disjointness mutations ----


def test_mutation_partition_geq_modulus_fails_disjointness():
    """Root partition (1, 4) at modulus 4 — residue 4 is out of `[0, 4)`."""
    bad = _mut(lambda root: setattr(root, "partition", (1, 4)))
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_NOT_DISJOINT


def test_mutation_partition_with_negative_residue_fails_disjointness():
    bad = _mut(lambda root: setattr(root, "partition", (1, -3)))
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_NOT_DISJOINT


def test_mutation_invalid_modulus_fails_disjointness():
    """Modulus 0 violates the `m >= 1` invariant."""
    bad = _mut(lambda root: setattr(root, "modulus", 0))
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_NOT_DISJOINT


def test_mutation_duplicate_residue_fails_disjointness():
    """Partition with a duplicate residue is not internally consistent."""
    bad = _mut(lambda root: setattr(root, "partition", (1, 1)))
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_NOT_DISJOINT


# ---- Child-totality mutations (Codex P1 naming; NOT full `[0, m)` coverage) ----


def test_dropped_residue_breaks_leaves_consistency():
    """Drop residue 1 from children; the leaves under residue 1 become
    unreachable. `leaves_consistent` fires (before child-totality)
    because removing a child necessarily disconnects its subtree from
    root. The test demonstrates that `check_tree`'s order — acyclic
    → leaves-consistent → disjoint → child-total — surfaces the
    structural-reachability issue first.
    """
    bad = _mut(lambda root: root.children.pop(1))
    assert is_disjoint(bad)
    assert not leaves_consistent(bad)
    assert not has_child_for_each_declared_residue(bad)
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_LEAVES_MISMATCH


def test_mutation_extra_residue_in_children_fails_child_totality():
    """Add a child at residue 2 not in the partition (1, 3)."""
    bad = _mut(lambda root: root.children.__setitem__(2, root.children[1]))
    assert not has_child_for_each_declared_residue(bad)
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_NOT_CHILD_TOTAL


# ---- Leaves-consistency mutations (Coex P1.1) ----


def test_mutation_missing_leaf_in_top_level_fails_leaves_consistency():
    """tree.leaves drops a reachable leaf — leaves_consistent fails."""
    bad = _mut(lambda root: None)
    bad.leaves = bad.leaves[:-1]
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_LEAVES_MISMATCH


def test_mutation_extra_leaf_in_top_level_fails_leaves_consistency():
    """tree.leaves contains a leaf not reachable from root."""
    bad = _mut(lambda root: None)
    extra = CoverageLeaf(leaf_id="extra_unreachable", leaf_property="X")
    bad.leaves = bad.leaves + (extra,)
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_LEAVES_MISMATCH


def test_mutation_duplicate_leaf_id_in_top_level_fails_leaves_consistency():
    """Two top-level leaves with the same leaf_id."""
    bad = _mut(lambda root: None)
    dup = CoverageLeaf(leaf_id=bad.leaves[0].leaf_id, leaf_property="DifferentFromTheFirst")
    bad.leaves = bad.leaves + (dup,)
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_LEAVES_MISMATCH


def test_mutation_unreachable_leaf_in_top_level_fails_leaves_consistency():
    """Repoint inner1.children[1] so leaves[2] is no longer reachable;
    tree.leaves still lists leaves[2]."""
    bad = _mut(lambda root: None)
    inner1 = bad.root.children[1]
    inner1.children[1] = inner1.children[2]  # leaves[1] shadows itself
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_LEAVES_MISMATCH


# ---- Leaf-id mutations (Story 07b / round-4; mirrors Lean's `verified` predicate) ----


def test_happy_path_leaf_id_non_empty():
    """`sample_tree` has all non-empty leaf_ids; the helper returns True.

    Mirrors the `hconsistent` hypothesis in the Lean
    `coverage_tree_soundness` proof body — every leaf in
    `t.leaves` must have non-empty `leafId`.
    """
    tree = sample_tree()
    assert leaf_id_non_empty(tree)


def test_mutation_empty_leaf_id_fails_leaf_id_non_empty():
    """An existing reachable leaf has its `leaf_id` mutated to the
    empty string. The structural checks (`acyclic`,
    `leaves_consistent`, `disjoint`, `child-total`) all pass; the new
    `leaf_id_non_empty` check is the first to fail. Mirrors the
    `hconsistent` hypothesis in the Lean
    `coverage_tree_soundness` proof body — without a non-empty
    `leafId`, the `verified` predicate cannot be discharged.
    """
    tree = sample_tree()
    inner1 = tree.root.children[1]
    reachable_leaf = inner1.children[1]  # leaves[0]
    mutated_leaf = CoverageLeaf(leaf_id="", leaf_property=reachable_leaf.leaf_property)
    inner1.children[1] = mutated_leaf
    tree.leaves = (mutated_leaf,) + tree.leaves[1:]
    # structural checks still pass
    assert has_no_cycles(tree)
    assert leaves_consistent(tree)
    assert is_disjoint(tree)
    assert has_child_for_each_declared_residue(tree)
    # leaf_id_non_empty fails
    assert not leaf_id_non_empty(tree)
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(tree)
    assert exc.value.category == ERR_LEAF_ID_EMPTY


# ---- Cycle mutations ----


def test_mutation_depth_overflow_fails_cycle_check():
    """max_depth=1 forces leaves at depth 2 (via internal nodes) to be flagged."""
    bad = _mut(lambda root: None, max_depth=1)
    assert not has_no_cycles(bad)
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_HAS_CYCLE


def test_mutation_structural_cycle_fails_cycle_check():
    """A node whose child points back to an ancestor creates a true cycle."""
    tree = copy.deepcopy(sample_tree())
    inner1 = tree.root.children[1]
    inner1.children[1] = tree.root
    assert not has_no_cycles(tree)
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(tree)
    assert exc.value.category == ERR_HAS_CYCLE


# ---- Distinct subtrees with identical shape must NOT be flagged ----


def test_identical_shape_subtrees_are_not_a_cycle():
    """Two sibling CoverageNodes with identical (modulus, partition) shape
    are fine — only ancestry revisits count as cycles.
    """
    tree = sample_tree()
    assert has_no_cycles(tree)


# ---- Fail-closed `from_dict` (Codex P2) ----


def _good_dict() -> dict:
    return to_dict(sample_tree())


def test_from_dict_rejects_non_dict_input():
    with pytest.raises(CoverageTreeError) as exc:
        from_dict("not a dict")  # type: ignore[arg-type]
    assert exc.value.category == ERR_INVALID_NODE


def test_from_dict_rejects_wrong_schema_version():
    bad = _good_dict()
    bad["schema"] = "collatz-research/coverage-tree@0.2.0"
    with pytest.raises(CoverageTreeError) as exc:
        from_dict(bad)
    assert exc.value.category == ERR_INVALID_NODE
    assert EXPECTED_SCHEMA in str(exc.value)


def test_from_dict_rejects_missing_required_top_level_field():
    bad = _good_dict()
    del bad["leaves"]
    with pytest.raises(CoverageTreeError) as exc:
        from_dict(bad)
    assert exc.value.category == ERR_INVALID_NODE


def test_from_dict_rejects_non_int_modulus():
    bad = _good_dict()
    bad["root"]["modulus"] = "not an int"
    with pytest.raises(CoverageTreeError) as exc:
        from_dict(bad)
    assert exc.value.category == ERR_INVALID_NODE


def test_from_dict_rejects_non_int_residue_key():
    bad = _good_dict()
    # Replace one numeric residue key with a non-numeric one.
    new_children = {}
    for k, v in bad["root"]["children"].items():
        new_children[k] = v
    new_children["not_an_int"] = new_children.pop(list(new_children.keys())[0])
    bad["root"]["children"] = new_children
    with pytest.raises(CoverageTreeError) as exc:
        from_dict(bad)
    assert exc.value.category == ERR_INVALID_NODE


def test_from_dict_rejects_non_str_leaf_field():
    bad = _good_dict()
    # Leaf nodes are at depth 2: bad["root"]["children"]["1"]["children"]["1"].
    # Mutating `leaf_id` to a non-string value should fail at parse time.
    bad["root"]["children"]["1"]["children"]["1"]["leaf_id"] = 42
    with pytest.raises(CoverageTreeError) as exc:
        from_dict(bad)
    assert exc.value.category == ERR_INVALID_NODE


# ---- Descend regression: depth-0 / depth-1 / depth-2 (Story 07b / round-4) ----
# Mirrors the Lean `descendFrom` examples in
# Lean/CollatzResearch/CoverageTree.lean. Leaf-first semantics: a leaf is
# reachable regardless of remaining depth; depth-0 internal returns None.


def test_descend_depth_0_leaf_reachable():
    """Depth 0 at a leaf: leaf is reachable at any x (depth unused)."""
    leaf = CoverageLeaf(leaf_id="L0", leaf_property="P0")
    tree = CoverageTree(root=leaf, leaves=(leaf,), max_depth=0)
    assert descend(tree, 5) == leaf
    assert descend(tree, 0) == leaf
    assert descend(tree, 999) == leaf


def test_descend_depth_0_internal_returns_none():
    """Depth 0 at an internal node: depth exhausted, returns None."""
    leaf = CoverageLeaf(leaf_id="L0", leaf_property="P0")
    inner = CoverageNode(modulus=4, partition=(1,), children={1: leaf})
    tree = CoverageTree(root=inner, leaves=(leaf,), max_depth=0)
    assert descend(tree, 5) is None
    assert descend(tree, 1) is None


def test_descend_depth_1_internal_to_leaf_reachable():
    """Depth 1, internal root + leaf child, residue 1 -> leaf: reachable."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="P1")
    inner = CoverageNode(modulus=4, partition=(1,), children={1: leaf})
    tree = CoverageTree(root=inner, leaves=(leaf,), max_depth=1)
    assert descend(tree, 1) == leaf
    assert descend(tree, 5) == leaf  # 5 % 4 = 1


def test_descend_depth_1_no_child_for_residue():
    """Depth 1, internal root + leaf child, residue 2 has no child: unreachable."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="P1")
    inner = CoverageNode(modulus=4, partition=(1,), children={1: leaf})
    tree = CoverageTree(root=inner, leaves=(leaf,), max_depth=1)
    assert descend(tree, 2) is None
    assert descend(tree, 6) is None  # 6 % 4 = 2


def test_descend_depth_2_internal_to_internal_to_leaf():
    """Depth 2, internal 4 -> internal 2 -> leaf; 7 % 4 = 3, 7 % 2 = 1."""
    leaf = CoverageLeaf(leaf_id="L2", leaf_property="P2")
    inner2 = CoverageNode(modulus=2, partition=(1,), children={1: leaf})
    inner1 = CoverageNode(modulus=4, partition=(3,), children={3: inner2})
    tree = CoverageTree(root=inner1, leaves=(leaf,), max_depth=2)
    assert descend(tree, 7) == leaf
    assert descend(tree, 3) == leaf  # 3 % 4 = 3


def test_descend_depth_2_depth_exhausted_at_second_internal():
    """Depth 1 (one unit), but tree has two internal levels: second internal returns None.

    With max_depth=1, the tree descends internal 4 -> internal 2 with
    depth 0, so the second internal returns None.
    """
    leaf = CoverageLeaf(leaf_id="L2", leaf_property="P2")
    inner2 = CoverageNode(modulus=2, partition=(1,), children={1: leaf})
    inner1 = CoverageNode(modulus=4, partition=(3,), children={3: inner2})
    tree = CoverageTree(root=inner1, leaves=(leaf,), max_depth=1)
    # 7 % 4 = 3 -> inner2; descend from depth 0 internal = None
    assert descend(tree, 7) is None


# ---- 07c-1 semantic leafProperty tests (mirrors Lean) ----
# Each leaf declares a `(period, lo, hi)` tuple via its `leaf_property`
# string `"<period>:<lo>-<hi>"`. The semantic predicate `Sat` and the
# static property `WellFormed` are Python mirrors of the Lean
# definitions in `CoverageTree.lean`.


def test_lean_interval_happy():
    """Parses '<period>:<lo>-<hi>' into (period, lo, hi)."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="3:0-2")
    assert lean_interval(leaf) == (3, 0, 2)


def test_lean_interval_garbage_returns_none():
    """Malformed leaves return None (no separator)."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="garbage")
    assert lean_interval(leaf) is None


def test_lean_interval_no_colon_returns_none():
    """Missing colon returns None."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="3-0-2")
    assert lean_interval(leaf) is None


def test_lean_interval_no_dash_returns_none():
    """Missing dash in range returns None."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="3:02")
    assert lean_interval(leaf) is None


def test_lean_interval_invalid_nats():
    """Non-numeric parts return None."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="abc:def-ghi")
    assert lean_interval(leaf) is None


def test_lean_interval_zero_period_parses():
    """`0:0-2` parses as `(0, 0, 2)` (not well-formed, but parseable)."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="0:0-2")
    assert lean_interval(leaf) == (0, 0, 2)


def test_sat_in_interval():
    """x is in interval iff x % period in [lo, hi]."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="3:1-2")
    assert sat(leaf, 1)  # 1 % 3 = 1 in [1, 2]
    assert sat(leaf, 2)  # 2 % 3 = 2 in [1, 2]
    assert sat(leaf, 4)  # 4 % 3 = 1 in [1, 2]
    assert sat(leaf, 5)  # 5 % 3 = 2 in [1, 2]
    assert not sat(leaf, 0)  # 0 % 3 = 0 NOT in [1, 2]
    assert not sat(leaf, 3)  # 3 % 3 = 0 NOT in [1, 2]


def test_sat_garbage_returns_false():
    """Unparseable leaves return False."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="garbage")
    assert not sat(leaf, 0)
    assert not sat(leaf, 5)


def test_well_formed_happy():
    """Valid interval (period > 0, lo <= hi) is well-formed."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="3:0-2")
    assert well_formed(leaf)


def test_well_formed_zero_period():
    """period = 0 is not well-formed (parses but ill-formed)."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="0:0-2")
    assert not well_formed(leaf)


def test_well_formed_inverted_range():
    """lo > hi is not well-formed."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="3:5-2")
    assert not well_formed(leaf)


def test_well_formed_garbage_returns_false():
    """Unparseable leaves are not well-formed."""
    leaf = CoverageLeaf(leaf_id="L1", leaf_property="garbage")
    assert not well_formed(leaf)
