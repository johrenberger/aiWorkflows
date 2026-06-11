from src.sample import divide, is_large, label


def test_is_large_returns_true_for_large_value():
    assert is_large(11) is True


def test_label_returns_large_for_large_value():
    assert label(11) == "large"


def test_divide_returns_quotient():
    assert divide(10, 2) == 5
