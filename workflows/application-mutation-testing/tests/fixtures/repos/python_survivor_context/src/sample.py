def is_large(value: int) -> bool:
    return value > 10


def label(value: int) -> str:
    if value > 10:
        return "large"
    return "small"


def divide(numerator: int, denominator: int) -> float:
    if denominator == 0:
        raise ValueError("denominator cannot be zero")
    return numerator / denominator
