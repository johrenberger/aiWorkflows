from __future__ import annotations

from pathlib import Path

from test_factory.config import load_config


def test_example_config_loads_lists_and_nested_values():
    root = Path(__file__).resolve().parents[1]
    config = load_config(root, root / "test_factory.yaml.example")

    assert "**/*.java" in config.eligible_source_globs
    assert "**/.git/**" in config.excluded_globs
    assert config.mutation.tools["java"] == "pitest"
    assert config.branching.branch_prefix == "test-automation-v2"
