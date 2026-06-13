"""Tests for the responsibility analyzer (CR 5)."""
from __future__ import annotations

import tempfile
from pathlib import Path

from skill_governance.discovery import (
    DiscoveryConfig,
    discover,
)
from skill_governance.models import ResponsibilityFlag
from skill_governance.responsibility_analyzer import analyze

FIXTURES = Path(__file__).parent / "fixtures"


def _make_skill(tmp_path: Path, name: str, body: str, *, has_outputs: bool = True) -> Path:
    p = tmp_path / "skills" / name
    p.mkdir(parents=True, exist_ok=True)
    outputs = "outputs: {format: json, fields: [x]}" if has_outputs else "outputs: {format: json, fields: []}"
    text = (
        "---\n"
        f"name: {name}\n"
        "artifact_type: skill\n"
        f"purpose: this skill exists to do its single job clearly in suites for {name}.\n"
        "category: test\n"
        "owner: justin\n"
        "version: '1.0'\n"
        "inputs: []\n"
        f"{outputs}\n"
        "dependencies: []\n"
        "intended_consumers: []\n"
        "quality_level: draft\n"
        "last_reviewed: 2026-06-13\n"
        "---\n"
        f"# {name}\n{body}\n"
    )
    f = p / "SKILL.md"
    f.write_text(text)
    return f


def test_single_action_is_coherent():
    """A skill that only validates is coherent and high-scoring."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "validator", "This skill validates input files.")
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        reports = analyze(artifacts, roots=[root])
        r = next(r for r in reports if r.artifact_name == "skills/validator")
        assert r.responsibility_score >= 80
        assert r.flag == ResponsibilityFlag.COHERENT


def test_many_actions_is_over_broad():
    """A skill that does 6+ distinct actions is over-broad and low-scoring."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        body = (
            "This skill analyzes, validates, generates, reports, tests, "
            "and audits everything in the system."
        )
        _make_skill(root, "do_everything", body)
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        reports = analyze(artifacts, roots=[root])
        r = next(r for r in reports if r.artifact_name == "skills/do_everything")
        assert r.flag in (ResponsibilityFlag.OVER_BROAD,)
        assert r.responsibility_score <= 50


def test_no_actions_is_unclear_or_narrow():
    """A skill with no actions is too-narrow or unclear."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "config_holder", "This file just declares some constants.")
        config = DiscoveryConfig(skill_directories=[root], agent_directories=[])
        artifacts = discover(config)
        reports = analyze(artifacts, roots=[root])
        r = next(r for r in reports if r.artifact_name == "skills/config_holder")
        assert r.flag in (ResponsibilityFlag.TOO_NARROW, ResponsibilityFlag.UNCLEAR)
        assert r.responsibility_score < 70


def test_empty_input_yields_no_reports():
    """No artifacts = no reports."""
    assert analyze([]) == []
