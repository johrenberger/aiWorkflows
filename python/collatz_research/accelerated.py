"""Reference arithmetic for candidate generation; not a proof implementation."""


def two_adic_valuation(value: int) -> int:
    """Return v_2(value) for a positive integer."""
    if value <= 0:
        raise ValueError("two_adic_valuation is defined here only for positive integers")
    exponent = 0
    while value % 2 == 0:
        value //= 2
        exponent += 1
    return exponent


def accelerated_step(odd_positive: int) -> int:
    """Apply (3n + 1) / 2^v2(3n + 1) on the positive odd domain."""
    if odd_positive <= 0 or odd_positive % 2 == 0:
        raise ValueError("accelerated_step requires a positive odd integer")
    successor = 3 * odd_positive + 1
    return successor >> two_adic_valuation(successor)
