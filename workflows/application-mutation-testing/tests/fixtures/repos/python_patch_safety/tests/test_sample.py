from src.sample import is_large


def test_is_large_returns_true_for_large_value():
    assert is_large(11) is True
