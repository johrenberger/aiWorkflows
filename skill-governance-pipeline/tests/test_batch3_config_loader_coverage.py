"""BDD-TDD coverage tests for config_loader.py (Batch 3).

Triggered by application-test-coverage assessment: config_loader.py
was 76% line coverage. Missing lines: 27, 30, 36, 41, 44, 52 — all
the public accessors of GovernanceConfig + the validation in load_config.

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

from pathlib import Path

import pytest

from skill_governance.config_loader import GovernanceConfig, load_config


# ===========================================================================
# SCENARIO 1: GovernanceConfig supports dict-style access (__getitem__)
# ===========================================================================
def test_governance_config_supports_dict_access():
    """config['key'] returns the underlying dict value."""
    cfg = GovernanceConfig({"a": 1, "b": 2})
    assert cfg["a"] == 1
    assert cfg["b"] == 2


# ===========================================================================
# SCENARIO 2: GovernanceConfig.get() supports default value
# ===========================================================================
def test_governance_config_get_returns_default_for_missing_key():
    """cfg.get('missing', default) returns default."""
    cfg = GovernanceConfig({"a": 1})
    assert cfg.get("a") == 1
    assert cfg.get("missing", "fallback") == "fallback"
    assert cfg.get("missing") is None  # no default


# ===========================================================================
# SCENARIO 3: GovernanceConfig.__getattr__ returns None for missing keys
# ===========================================================================
def test_governance_config_attribute_access_returns_none_for_missing():
    """config.missing returns None (not AttributeError) for missing keys."""
    cfg = GovernanceConfig({"a": 1})
    assert cfg.a == 1
    assert cfg.missing is None


# ===========================================================================
# SCENARIO 4: GovernanceConfig.__getattr__ raises AttributeError for dunder
# ===========================================================================
def test_governance_config_attribute_access_raises_for_dunder():
    """Dunder access raises AttributeError (Python requires this)."""
    cfg = GovernanceConfig({"a": 1})
    with pytest.raises(AttributeError):
        cfg.__nonexistent_dunder__


# ===========================================================================
# SCENARIO 5: GovernanceConfig.raw and to_dict() return the underlying dict
# ===========================================================================
def test_governance_config_raw_and_to_dict_return_underlying_dict():
    """cfg.raw is a property; cfg.to_dict() returns the same dict."""
    raw = {"x": 1, "y": "z"}
    cfg = GovernanceConfig(raw)
    assert cfg.raw == raw
    assert cfg.to_dict() == raw
    # Mutating the returned dict mutates the underlying config
    cfg.to_dict()["new"] = True
    assert cfg.raw["new"] is True


# ===========================================================================
# SCENARIO 6: load_config raises ValueError for non-mapping YAML
# ===========================================================================
def test_load_config_raises_for_non_mapping_yaml(tmp_path: Path):
    """A YAML file that's a list (not a mapping) raises ValueError."""
    p = tmp_path / "config.yaml"
    p.write_text("- item1\n- item2\n")
    with pytest.raises(ValueError, match="must be a YAML mapping"):
        load_config(p)
