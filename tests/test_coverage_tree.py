"""TDD tests for the coverage-tree model + checker (Story 07).

Mutation tests corrupt each field of `sample_tree()` and assert that
`check_tree` raises with the matching stable category. Plus round-trip
JSONL serialization, deterministic-ordering, and the cycle policy.
"""

from __future__ import annotations

import copy
import json

import pytest

from collatz_research.tree import (
    CoverageLeaf,
    CoverageNode,
    CoverageTree,
    CoverageTreeError,
    ERR_HAS_CYCLE,
    ERR_NOT_COMPLETE,
    ERR_NOT_DISJOINT,
    check_tree,
    deterministic_children,
    from_dict,
    has_no_cycles,
    is_complete,
    is_disjoint,
    sample_tree,
    to_dict,
)


# ---- Happy path ----


def test_sample_tree_passes_all_checks():
    tree = sample_tree()
    assert is_complete(tree)
    assert is_disjoint(tree)
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
    reversed_children = {
        r: tree.root.children[r] for r in reversed(list(tree.root.children))
    }
    reverse_node = CoverageNode(
        modulus=tree.root.modulus,
        partition=tree.root.partition,
        children=reversed_children,
    )
    seen = [r for r, _ in deterministic_children(reverse_node)]
    assert seen == sorted(tree.root.children.keys())


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


# ---- Completeness mutations ----


def test_mutation_missing_residue_fails_completeness():
    """Drop residue 1 from children; partition still says (1, 3)."""
    bad = _mut(lambda root: root.children.pop(1))
    assert is_disjoint(bad)  # partition still valid
    assert not is_complete(bad)  # missing child
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_NOT_COMPLETE


def test_mutation_extra_residue_in_children_fails_completeness():
    """Add a child at residue 2 not in the partition (1, 3)."""
    bad = _mut(lambda root: root.children.__setitem__(2, root.children[1]))
    assert not is_complete(bad)
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(bad)
    assert exc.value.category == ERR_NOT_COMPLETE


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
    # Route residue 1 of inner1 (a leaf) back to the root.
    inner1 = tree.root.children[1]
    inner1.children[1] = tree.root
    assert not has_no_cycles(tree)
    with pytest.raises(CoverageTreeError) as exc:
        check_tree(tree)
    assert exc.value.category == ERR_HAS_CYCLE


# ---- Distinct subtrees with identical shape must NOT be flagged ----


def test_identical_shape_subtrees_are_not_a_cycle():
    """Two sibling CoverageNodes with identical (modulus, partition) shape are
    fine — only ancestry revisits count as cycles. `has_no_cycles` should
    return True for sample_tree (which has precisely this structure).
    """
    tree = sample_tree()
    assert has_no_cycles(tree)
