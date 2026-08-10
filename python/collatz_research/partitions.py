"""Partition checker for residue classes.

A partition of ℤ/mℤ is a list of residues that:
- Covers all of ℤ/mℤ (completeness): every `r ∈ [0, m)` is in the partition.
- Has no duplicates (disjointness): `r1 ≠ r2` for any `r1, r2` in the partition.
- All residues are in `[0, m)` (validity).

The `is_partition` function checks all three conditions and raises
`PartitionError` with a stable category on failure.
"""

from __future__ import annotations

from collections.abc import Sequence

# Error categories (stable, uppercase).
ERR_INVALID_RESIDUE = "INVALID_RESIDUE"
ERR_INCOMPLETE = "INCOMPLETE"
ERR_NON_DISJOINT = "NON_DISJOINT"


class PartitionError(Exception):
    """Raised when a residue partition fails validation."""

    def __init__(self, category: str, message: str):
        self.category = category
        self.message = message
        super().__init__(f"{category}: {message}")


def is_partition(m: int, residues: Sequence[int]) -> bool:
    """Check whether `residues` is a valid partition of ℤ/mℤ.

    The checks run in a fixed order:
    1. Modulus validity (m >= 1).
    2. Residue validity (each r in [0, m)).
    3. Disjointness (no duplicates).
    4. Completeness (covers all of [0, m)).

    Raises PartitionError with a stable category if the partition
    is invalid. Returns True if the partition is valid.
    """
    if m < 1:
        raise PartitionError(ERR_INVALID_RESIDUE, f"modulus m = {m} must be >= 1")

    # Validity: all residues in [0, m).
    for r in residues:
        if r < 0 or r >= m:
            raise PartitionError(
                ERR_INVALID_RESIDUE,
                f"residue {r} not in [0, {m})",
            )

    # Disjointness: no duplicates.
    seen: set[int] = set()
    for r in residues:
        if r in seen:
            raise PartitionError(
                ERR_NON_DISJOINT,
                f"residue {r} appears more than once",
            )
        seen.add(r)

    # Completeness: every r in [0, m) is in the partition.
    missing = set(range(m)) - seen
    if missing:
        missing_sorted = sorted(missing)
        raise PartitionError(
            ERR_INCOMPLETE,
            f"missing residues: {missing_sorted}",
        )

    return True
