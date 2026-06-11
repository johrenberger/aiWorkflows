def has_evidence(items) -> bool:
    return bool(items) and all(bool(getattr(item, "evidence", None)) for item in items)
