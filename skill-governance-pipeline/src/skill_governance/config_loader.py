"""Configuration loader.

Reads a YAML config file and returns a typed dict-like object.
The current implementation uses plain dicts for simplicity;
later phases may switch to a Pydantic model if the schema
grows.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class GovernanceConfig:
    """Lightweight wrapper around the loaded YAML config.

    Supports both dict-style (`config["foo"]`) and
    attribute-style (`config.foo`) access. Attribute access
    falls back to None when the key is missing.
    """

    def __init__(self, raw: dict[str, Any]) -> None:
        self._raw = raw

    def __getitem__(self, key: str) -> Any:
        return self._raw[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._raw.get(key, default)

    def __getattr__(self, name: str) -> Any:
        # __getattr__ is only called when the normal lookup fails,
        # so it doesn't interfere with methods defined here.
        if name.startswith("_"):
            raise AttributeError(name)
        return self._raw.get(name)

    @property
    def raw(self) -> dict[str, Any]:
        return self._raw

    def to_dict(self) -> dict[str, Any]:
        return self._raw


def load_config(path: Path) -> GovernanceConfig:
    """Load a YAML config from disk."""
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"Config at {path} must be a YAML mapping, got {type(raw).__name__}")
    return GovernanceConfig(raw)
