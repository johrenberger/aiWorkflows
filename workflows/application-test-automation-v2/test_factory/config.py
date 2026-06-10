from __future__ import annotations

from dataclasses import is_dataclass
from pathlib import Path
from typing import Any

from .models import BranchingConfig, Config, MutationConfig, ValidationTimeouts


def _coerce_scalar(value: str) -> Any:
    lowered = value.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if value.strip().startswith(("'", '"')) and value.strip().endswith(("'", '"')):
        return value.strip()[1:-1]
    try:
        if "." in value or "e" in lowered:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip()


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[dict[str, Any]] = [{"indent": -1, "container": root, "parent": None, "key": None, "pending": False}]

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()

        while len(stack) > 1 and indent <= int(stack[-1]["indent"]) and not bool(stack[-1]["pending"]):
            stack.pop()

        if bool(stack[-1]["pending"]) and indent > int(stack[-1]["indent"]):
            parent = stack[-1]["parent"]
            key = stack[-1]["key"]
            container = [] if line.startswith("- ") else {}
            parent[key] = container
            stack[-1]["container"] = container
            stack[-1]["pending"] = False

        current = stack[-1]["container"]
        if line.startswith("- "):
            if not isinstance(current, list):
                continue
            current.append(_coerce_scalar(line[2:].strip()))
            continue

        if ":" not in line or not isinstance(current, dict):
            continue

        key, rest = line.split(":", 1)
        key = key.strip()
        rest = rest.strip()
        if rest:
            current[key] = _coerce_scalar(rest)
            continue

        stack.append({"indent": indent, "container": None, "parent": current, "key": key, "pending": True})

    for frame in stack[1:]:
        if bool(frame["pending"]):
            frame["parent"][frame["key"]] = {}

    return root


def _merge_nested_dataclass(target: Any, values: dict[str, Any]) -> Any:
    for key, value in values.items():
        if not hasattr(target, key):
            continue
        current = getattr(target, key)
        if is_dataclass(current) and isinstance(value, dict):
            _merge_nested_dataclass(current, value)
        elif isinstance(current, dict) and isinstance(value, dict):
            current.update(value)
        elif isinstance(current, list) and isinstance(value, list):
            setattr(target, key, list(value))
        else:
            setattr(target, key, value)
    return target


def load_config(repo_root: str | Path, explicit_path: str | Path | None = None) -> Config:
    repo_root = Path(repo_root)
    config_path = Path(explicit_path) if explicit_path else repo_root / "test_factory.yaml"
    config = Config()
    if not config_path.exists():
        return config
    parsed = _parse_simple_yaml(config_path.read_text(encoding="utf-8"))
    return _merge_nested_dataclass(config, parsed)

