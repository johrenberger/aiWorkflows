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
    ERR_LEAVES_MISMATCH,
    ERR_NOT_CHILD_TOTAL,
    ERR_NOT_DISJOINT,
    EXPECTED_SCHEMA,
    CoverageLeaf,
    CoverageNode,
    CoverageTree,
    CoverageTreeError,
    check_tree,
    deterministic_children,
    from_dict,
    has_child_for_each_declared_residue,
    has_no_cycles,
    is_disjoint,
    leaves_consistent,
    reachable_leaves,
    sample_tree,
    to_dict,
)

# ---- Happy path ----


def test_sample_tree_passes_all_checks():
    tree = sample_tree()
    assert has_child_for_each_declared_residue(tree)
    assert is_disjoint(tree)
    assert leaves_consistent(tree)
    assert has_no_cycles(tree)
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
