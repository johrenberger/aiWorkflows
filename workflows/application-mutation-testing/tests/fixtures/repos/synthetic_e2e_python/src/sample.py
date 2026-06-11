def is_large(value: int) -> bool:
    return value > 10


def label(value: int) -> str:
    if value > 10:
        return "large"
    return "small"
