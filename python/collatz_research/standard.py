"""Standard (unaccelerated) Collatz map and parity/positivity predicates.

The standard map `C(n) = n/2 if n is even else 3n + 1` is the canonical
Collatz iteration; the accelerated map `T` is defined on the odd domain
by `T(n) = C^{1 + ν₂(3n+1)}(n) = (3n + 1) / 2^{ν₂(3n + 1)}`.

These two implementations are independent and reconciled by the
differential test suite (`tests/test_differential.py`). The Lean
counterpart is `CollatzResearch.Dynamics.standardStep`.
"""

from __future__ import annotations


def standard_step(n: int) -> int:
    """Apply the standard Collatz map C on the positive integer domain.

    C(n) = n / 2  if n is even
    C(n) = 3n + 1 if n is odd
    """
    if n < 1:
        raise ValueError("standard_step is defined here only for positive integers")
    if n % 2 == 0:
        return n // 2
    return 3 * n + 1


def is_positive(n: int) -> bool:
    """`True` iff n is a strictly positive integer."""
    return n > 0


def is_odd(n: int) -> bool:
    """`True` iff n is a positive odd integer.

    Mirrors Mathlib's `Nat.Odd`, which requires `n % 2 = 1` on positive
    inputs (Nat cannot be 0 and odd simultaneously).
    """
    return n > 0 and n % 2 == 1


def is_even(n: int) -> bool:
    """`True` iff n is a positive even integer."""
    return n > 0 and n % 2 == 0
