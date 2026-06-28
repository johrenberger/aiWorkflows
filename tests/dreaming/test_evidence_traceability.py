"""Verify every recommendation, lesson, and pattern references an EV-### evidence ID."""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DREAMING_DIR = REPO_ROOT / ".openclaw" / "dreaming"

EV_RE = re.compile(r"EV-\d{3}")
L_RE = re.compile(r"L-\d{3}")
RS_RE = re.compile(r"RS-\d{3}")
PI_RE = re.compile(r"PI-\d{3}")
P_RE = re.compile(r"P-[A-Z]{2}-\d{3}")


def _evidence_index_ids() -> set[str]:
    text = (DREAMING_DIR / "evidence-index.md").read_text(encoding="utf-8")
    return set(EV_RE.findall(text))


@pytest.fixture(scope="module")
def evidence_index_ids() -> set[str]:
    return _evidence_index_ids()


def test_evidence_index_has_ids() -> None:
    ids = _evidence_index_ids()
    assert ids, "evidence-index.md must contain at least one EV-### id"


@pytest.mark.parametrize(
    "rel_path",
    [
        "lessons-learned.md",
        "failure-patterns.md",
        "success-patterns.md",
        "inefficiency-patterns.md",
        "regression-scenarios.md",
        "proposed-improvements.md",
    ],
)
def test_artifact_references_evidence(rel_path: str, evidence_index_ids: set[str]) -> None:
    path = DREAMING_DIR / rel_path
    text = path.read_text(encoding="utf-8")
    found = set(EV_RE.findall(text))
    assert found, f"{rel_path} must reference at least one EV-### id"
    unknown = found - evidence_index_ids
    assert not unknown, (
        f"{rel_path} references unknown evidence ids {unknown}; add them to evidence-index.md"
    )


def test_lessons_have_l_ids_and_ev_refs(evidence_index_ids: set[str]) -> None:
    path = DREAMING_DIR / "lessons-learned.md"
    text = path.read_text(encoding="utf-8")
    lesson_headers = re.findall(r"^## (L-\d{3})\b", text, re.MULTILINE)
    assert lesson_headers, "lessons-learned.md must have ## L-### headers"
    # Each lesson must contain an EV-### reference and that EV must exist in the index.
    for lid in lesson_headers:
        # Find the section body (between this header and the next ## L- or end of file).
        pattern = rf"## {re.escape(lid)}\b(.*?)(?=\n## L-|\Z)"
        m = re.search(pattern, text, re.DOTALL)
        assert m, f"Lesson {lid} not parseable"
        body = m.group(1)
        evs = set(EV_RE.findall(body))
        assert evs, f"Lesson {lid} missing EV-### reference"
        unknown = evs - evidence_index_ids
        assert not unknown, f"Lesson {lid} references unknown evidence {unknown}"


def test_proposed_improvements_have_pi_ids_and_ev_refs(evidence_index_ids: set[str]) -> None:
    path = DREAMING_DIR / "proposed-improvements.md"
    text = path.read_text(encoding="utf-8")
    pi_headers = re.findall(r"^## (PI-\d{3})\b", text, re.MULTILINE)
    assert pi_headers, "proposed-improvements.md must have ## PI-### headers"
    for pid in pi_headers:
        pattern = rf"## {re.escape(pid)}\b(.*?)(?=\n## PI-|\Z)"
        m = re.search(pattern, text, re.DOTALL)
        assert m, f"Improvement {pid} not parseable"
        body = m.group(1)
        evs = set(EV_RE.findall(body))
        assert evs, f"Improvement {pid} missing EV-### reference"
        unknown = evs - evidence_index_ids
        assert not unknown, f"Improvement {pid} references unknown evidence {unknown}"


def test_scenarios_have_rs_ids_and_ev_refs(evidence_index_ids: set[str]) -> None:
    path = DREAMING_DIR / "regression-scenarios.md"
    text = path.read_text(encoding="utf-8")
    rs_headers = re.findall(r"^## (RS-\d{3})\b", text, re.MULTILINE)
    assert rs_headers, "regression-scenarios.md must have ## RS-### headers"
    for rid in rs_headers:
        pattern = rf"## {re.escape(rid)}\b(.*?)(?=\n## RS-|\Z)"
        m = re.search(pattern, text, re.DOTALL)
        assert m, f"Scenario {rid} not parseable"
        body = m.group(1)
        evs = set(EV_RE.findall(body))
        assert evs, f"Scenario {rid} missing EV-### reference"
        unknown = evs - evidence_index_ids
        assert not unknown, f"Scenario {rid} references unknown evidence {unknown}"
