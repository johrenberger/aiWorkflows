import pytest
from collatz_research.accelerated import accelerated_step, two_adic_valuation


def test_two_adic_valuation() -> None:
    assert two_adic_valuation(40) == 3
    assert two_adic_valuation(7) == 0


def test_accelerated_step_uses_odd_domain() -> None:
    assert accelerated_step(3) == 5
    with pytest.raises(ValueError):
        accelerated_step(2)
