"""Coverage-tree model and checker (Story 07, M4 Finite coverage).

A `CoverageTree` is a rooted tree whose internal nodes carry a residue
partition (residue list in `[0, m)`, no duplicates; coverage of `[0, m)`
is a tree-level concern, not a partition concern) and one child per
residue class. Leaves carry a `leaf_property` symbol.

Checks (per `check_tree`, ordered):

1. `disjoint` — every internal node's partition is internally consistent
   (residues are non-bool ints in `[0, m)` with no duplicates). Coverage
   of `[0, m)` is `is_complete`'s job, not `is_disjoint`'s.
2. `complete` — every residue class declared in the partition has a child.
3. `acyclic` — depth ≤ `max_depth` and no node is revisited through its
   ancestry (tracked by `id()` along the parent → child path, so distinct
   subtrees with identical shape are not flagged).

Exporters + the Python checker iterate children in sorted-by-residue
order, so round-trips and external checks are deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Stable error categories; uppercase. Mirrors the partitions.py style.
ERR_NOT_COMPLETE = "TREE_NOT_COMPLETE"
ERR_NOT_DISJOINT = "TREE_NOT_DISJOINT"
ERR_HAS_CYCLE = "TREE_HAS_CYCLE"
ERR_INVALID_NODE = "INVALID_NODE"


class CoverageTreeError(Exception):
    """Raised when a coverage tree fails a check."""

    def __init__(self, category: str, message: str):
        self.category = category
        self.message = message
        super().__init__(f"{category}: {message}")


@dataclass(frozen=True)
class CoverageLeaf:
    """A leaf in a coverage tree."""

    leaf_id: str
    leaf_property: str


@dataclass
class CoverageNode:
    """An internal node: residue partition + one child per residue."""

    modulus: int
    partition: tuple[int, ...]
    children: dict[int, CoverageNode | CoverageLeaf] = field(default_factory=dict)


@dataclass
class CoverageTree:
    """Rooted coverage tree with a depth bound."""

    root: CoverageNode
    leaves: tuple[CoverageLeaf, ...]
    max_depth: int
    schema_version: str = "collatz-research/coverage-tree@0.1.0"


# ---- JSONL I/O (deterministic; sorted by residue) ----


def to_dict(tree: CoverageTree) -> dict[str, Any]:
    """Serialize a tree to a JSONL-ready dict, children sorted by residue."""

    def node_d(n: CoverageNode) -> dict[str, Any]:
        return {
            "kind": "internal",
            "modulus": n.modulus,
            "partition": list(n.partition),
            "children": {
                str(r): (
                    {
                        "kind": "leaf",
                        "leaf_id": c.leaf_id,
                        "leaf_property": c.leaf_property,
                    }
                    if isinstance(c, CoverageLeaf)
                    else node_d(c)
                )
                for r, c in sorted(n.children.items())
            },
        }

    return {
        "schema": tree.schema_version,
        "max_depth": tree.max_depth,
        "root": node_d(tree.root),
        "leaves": [
            {"leaf_id": lf.leaf_id, "leaf_property": lf.leaf_property} for lf in tree.leaves
        ],
    }


def from_dict(d: dict[str, Any]) -> CoverageTree:
    """Deserialize a tree from a dict; raises `CoverageTreeError` on shape mismatch."""

    def node_n(n: dict[str, Any]) -> CoverageNode:
        kind = n.get("kind")
        if kind != "internal":
            raise CoverageTreeError(ERR_INVALID_NODE, f"expected internal node, got {kind!r}")
        children: dict[int, CoverageNode | CoverageLeaf] = {}
        for r_str, c_d in n["children"].items():
            r = int(r_str)
            if c_d.get("kind") == "leaf":
                children[r] = CoverageLeaf(
                    leaf_id=c_d["leaf_id"],
                    leaf_property=c_d["leaf_property"],
                )
            else:
                children[r] = node_n(c_d)
        return CoverageNode(
            modulus=n["modulus"],
            partition=tuple(n["partition"]),
            children=children,
        )

    return CoverageTree(
        root=node_n(d["root"]),
        leaves=tuple(
            CoverageLeaf(leaf_id=leaf["leaf_id"], leaf_property=leaf["leaf_property"])
            for leaf in d["leaves"]
        ),
        max_depth=d["max_depth"],
        schema_version=d.get("schema", "collatz-research/coverage-tree@0.1.0"),
    )


# ---- Checkers ----


def _is_disjoint_partition(modulus: int, partition: tuple[int, ...]) -> bool:
    """Partition is internally consistent: residues are non-bool ints in `[0, m)`
    with no duplicates. Does NOT check coverage of `[0, m)` — that's `is_complete`.
    """
    for r in partition:
        if not isinstance(r, int) or isinstance(r, bool):
            return False
        if r < 0 or r >= modulus:
            return False
    return len(set(partition)) == len(partition)


def is_disjoint(tree: CoverageTree) -> bool:
    """`True` iff every internal node's partition is internally consistent."""

    def node_ok(n: CoverageNode) -> bool:
        if not _is_disjoint_partition(n.modulus, n.partition):
            return False
        return all(node_ok(c) if isinstance(c, CoverageNode) else True for c in n.children.values())

    return node_ok(tree.root)


def is_complete(tree: CoverageTree) -> bool:
    """`True` iff every residue class declared in the partition has a child."""

    def node_ok(n: CoverageNode) -> bool:
        if set(n.children.keys()) != set(n.partition):
            return False
        return all(node_ok(c) if isinstance(c, CoverageNode) else True for c in n.children.values())

    return node_ok(tree.root)


def has_no_cycles(tree: CoverageTree) -> bool:
    """`True` iff depth at every node stays within `max_depth` and no node is
    revisited through its parent → child ancestry. The cycle test is tracked
    by Python `id()` along the current descent path, so distinct subtrees
    with identical shape are not flagged (only true ancestry revisits).
    """

    def node_ok(n: CoverageNode, depth: int, path_ids: frozenset[int]) -> bool:
        if depth > tree.max_depth:
            return False
        if id(n) in path_ids:
            return False
        path_ids = path_ids | {id(n)}
        for c in n.children.values():
            if isinstance(c, CoverageNode):
                if not node_ok(c, depth + 1, path_ids):
                    return False
            else:
                # Leaf: must also respect max_depth.
                if depth + 1 > tree.max_depth:
                    return False
        return True

    return node_ok(tree.root, 0, frozenset())


def check_tree(tree: CoverageTree) -> None:
    """Run acyclic → disjoint → complete checks; raise on first failure.

    Cycle detection runs first because a true ancestry revisit would make
    `is_disjoint` and `is_complete` infinite-recurse (Python RecursionError)
    on the loop. Detecting acyclicity up-front turns infinite-recurse into
    a clean category-stable error.
    """
    if not has_no_cycles(tree):
        raise CoverageTreeError(ERR_HAS_CYCLE, "tree revisits a node or exceeds max_depth")
    if not is_disjoint(tree):
        raise CoverageTreeError(ERR_NOT_DISJOINT, "tree has overlapping or out-of-range residues")
    if not is_complete(tree):
        raise CoverageTreeError(ERR_NOT_COMPLETE, "tree is missing children for some residues")


# ---- Determinism ----


def deterministic_children(
    n: CoverageNode,
) -> list[tuple[int, CoverageNode | CoverageLeaf]]:
    """Sorted-by-residue deterministic iteration order."""
    return [(r, n.children[r]) for r in sorted(n.children.keys())]


# ---- Sample demonstrator (depth-2, root uses only odd residues) ----


def sample_tree() -> CoverageTree:
    """Depth-2 demonstrator: modulus 4 root → odd residues (1, 3) →
    modulus 3 each → all residues (1, 2) → 4 leaves total.

    The root partition is intentionally non-covering (only odd residues
    at modulus 4) to demonstrate that partition validity is disjoint-only
    and coverage is a separate tree-level invariant.
    """
    leaves = (
        CoverageLeaf(leaf_id="leaf_1_2", leaf_property="L(1,2)"),
        CoverageLeaf(leaf_id="leaf_2_2", leaf_property="L(2,2)"),
        CoverageLeaf(leaf_id="leaf_4_2", leaf_property="L(4,2)"),
        CoverageLeaf(leaf_id="leaf_5_2", leaf_property="L(5,2)"),
    )
    inner1 = CoverageNode(
        modulus=3,
        partition=(1, 2),
        children={1: leaves[0], 2: leaves[1]},
    )
    inner2 = CoverageNode(
        modulus=3,
        partition=(1, 2),
        children={1: leaves[2], 2: leaves[3]},
    )
    root = CoverageNode(modulus=4, partition=(1, 3), children={1: inner1, 3: inner2})
    return CoverageTree(root=root, leaves=leaves, max_depth=2)
