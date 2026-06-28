"""Verify regression scenarios use BDD-style Given/When/Then and include required fields."""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_PATH = REPO_ROOT / ".openclaw" / "dreaming" / "regression-scenarios.md"

SEVERITIES = {"blocker", "warning", "informational"}
OWNERS = {"MiniMax", "deterministic_tool", "human"}

SCENARIO_HEADER_RE = re.compile(r"^## (RS-\d{3})\b", re.MULTILINE)


def test_scenarios_file_exists() -> None:
    assert SCENARIOS_PATH.is_file()


def _parse_scenarios() -> list[dict[str, str]]:
    text = SCENARIOS_PATH.read_text(encoding="utf-8")
    headers = list(SCENARIO_HEADER_RE.finditer(text))
    sections: list[dict[str, str]] = []
    for i, m in enumerate(headers):
        start = m.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[start:end]
        sections.append({"id": m.group(1), "body": body})
    return sections


def test_at_least_one_scenario() -> None:
    sections = _parse_scenarios()
    assert sections, "regression-scenarios.md must contain at least one ## RS-### scenario"


def test_scenarios_have_required_fields() -> None:
    """Each scenario must include: Given, When, Then, severity, pass/fail criteria, owner, evidence reference."""
    sections = _parse_scenarios()
    missing_summary: list[str] = []
    for sec in sections:
        body = sec["body"]
        problems: list[str] = []
        if "**Given**" not in body:
            problems.append("missing **Given**")
        if "**When**" not in body:
            problems.append("missing **When**")
        if "**Then**" not in body:
            problems.append("missing **Then**")
        if "**Severity:**" not in body:
            problems.append("missing **Severity:**")
        if "**Pass / fail criteria:**" not in body:
            problems.append("missing **Pass / fail criteria:**")
        if "**Owner:**" not in body:
            problems.append("missing **Owner:**")
        if "**Evidence reference:**" not in body:
            problems.append("**Evidence reference:** not at top of section")
        if "**Validation method:**" not in body:
            problems.append("missing **Validation method:**")
        if problems:
            missing_summary.append(f"{sec['id']}: " + "; ".join(problems))
    assert not missing_summary, "Scenario quality problems:\n" + "\n".join(missing_summary)


def test_scenarios_severity_in_allowed_set() -> None:
    sections = _parse_scenarios()
    bad: list[str] = []
    for sec in sections:
        m = re.search(r"\*\*Severity:\*\*\s*(\S+)", sec["body"])
        if m and m.group(1) not in SEVERITIES:
            bad.append(f"{sec['id']}: severity={m.group(1)!r} not in {SEVERITIES}")
    assert not bad, "Bad severities:\n" + "\n".join(bad)


def test_scenarios_owner_in_allowed_set() -> None:
    sections = _parse_scenarios()
    bad: list[str] = []
    for sec in sections:
        m = re.search(r"\*\*Owner:\*\*\s*(\S+)", sec["body"])
        if m and m.group(1) not in OWNERS:
            bad.append(f"{sec['id']}: owner={m.group(1)!r} not in {OWNERS}")
    assert not bad, "Bad owners:\n" + "\n".join(bad)


def test_scenario_ids_unique() -> None:
    sections = _parse_scenarios()
    ids = [s["id"] for s in sections]
    assert len(ids) == len(set(ids)), f"Duplicate scenario IDs: {ids}"
