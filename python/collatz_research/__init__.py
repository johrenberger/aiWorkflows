"""Untrusted tools for exploring accelerated Collatz dynamics."""

from .accelerated import accelerated_step, two_adic_valuation
from .affine import AffineMap, BranchWord
from .standard import is_even, is_odd, is_positive, standard_step, standard_trajectory

__all__ = [
    "accelerated_step",
    "AffineMap",
    "BranchWord",
    "is_even",
    "is_odd",
    "is_positive",
    "standard_step",
    "standard_trajectory",
    "two_adic_valuation",
]
