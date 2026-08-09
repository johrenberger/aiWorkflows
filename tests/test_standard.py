import pytest
from collatz_research.standard import is_even, is_odd, is_positive, standard_step


def test_standard_step_odd() -> None:
    assert standard_step(1) == 4
    assert standard_step(3) == 10
    assert standard_step(5) == 16
    assert standard_step(7) == 22


def test_standard_step_even() -> None:
    assert standard_step(2) == 1
    assert standard_step(4) == 2
    assert standard_step(8) == 4
    assert standard_step(16) == 8


def test_standard_step_rejects_non_positive() -> None:
    with pytest.raises(ValueError):
        standard_step(0)
    with pytest.raises(ValueError):
        standard_step(-1)


def test_predicates() -> None:
    assert is_positive(1) and is_positive(7)
    assert not is_positive(0) and not is_positive(-3)

    assert is_odd(1) and is_odd(7)
    assert not is_odd(2) and not is_odd(0) and not is_odd(-3)

    assert is_even(2) and is_even(8)
    assert not is_even(1) and not is_even(0) and not is_even(-3)
