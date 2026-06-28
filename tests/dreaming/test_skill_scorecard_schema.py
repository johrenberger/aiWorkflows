"""Verify skill and workflow scorecards include all required dimensions and recommendation values."""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_SCORE = REPO_ROOT / ".openclaw" / "dreaming" / "skill-usage-scorecard.md"
WORKFLOW_SCORE = REPO_ROOT / ".openclaw" / "dreaming" / "workflow-scorecard.md"

REQUIRED_DIMENSIONS = (
    "activation_precision",
    "contribution_quality",
    "overlap_risk",
    "validation_compatibility",
    "handoff_quality",
    "recovery_contribution",
    "deterministic_replacement_opportunity",
    "minimax_usability",
)

ALLOWED_RECOMMENDATIONS = (
    "keep",
    "revise",
    "add_guardrail",
    "merge",
    "split",
    "deprecation_watch",
    "deprecation_review",
)

EV_RE = re.compile(r"EV-\d{3}")


def _collect_sections(text: str) -> list[tuple[str, str]]:
    """Return list of (section_heading, body) for each ## heading."""
    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_heading: str | None = None
    current_body: list[str] = []
    for line in lines:
        if line.startswith("## ") and not line.startswith("### "):
            if current_heading is not None:
                sections.append((current_heading, current_body))
            current_heading = line[3:].strip()
            current_body = []
        else:
            if current_heading is not None:
                current_body.append(line)
    if current_heading is not None:
        sections.append((current_heading, current_body))
    return [(h, "\n".join(b)) for h, b in sections]


def _scorecard_sections(path: Path) -> list[tuple[str, str]]:
    """Scorecard entries are ## SkillName sections, each containing a markdown table."""
    text = path.read_text(encoding="utf-8")
    return _collect_sections(text)


@pytest.mark.parametrize("path", [SKILL_SCORE, WORKFLOW_SCORE])
def test_scorecard_exists(path: Path) -> None:
    assert path.is_file()


@pytest.mark.parametrize("path", [SKILL_SCORE, WORKFLOW_SCORE])
def test_scorecard_has_at_least_one_entry(path: Path) -> None:
    sections = _scorecard_sections(path)
    # First heading is the title; entries are subsequent ## sections.
    entries = [(h, b) for (h, b) in sections[1:]] if len(sections) > 1 else []
    assert entries, f"{path.name} must contain at least one scorecard entry"


@pytest.mark.parametrize("path", [SKILL_SCORE, WORKFLOW_SCORE])
def test_scorecard_entries_have_required_dimensions(path: Path) -> None:
    sections = _scorecard_sections(path)
    entries = sections[1:] if len(sections) > 1 else []
    problems: list[str] = []
    for name, body in entries:
        for dim in REQUIRED_DIMENSIONS:
            if dim not in body:
                problems.append(f"{name}: missing dimension {dim!r}")
    assert not problems, "Scorecard schema problems:\n" + "\n".join(problems)


@pytest.mark.parametrize("path", [SKILL_SCORE, WORKFLOW_SCORE])
def test_scorecard_entries_have_recommendation(path: Path) -> None:
    sections = _scorecard_sections(path)
    entries = sections[1:] if len(sections) > 1 else []
    problems: list[str] = []
    for name, body in entries:
        m = re.search(r"\*\*Recommendation:\*\*\s*[`]?(\w+)[`]?", body)
        if not m:
            problems.append(f"{name}: missing **Recommendation:**")
            continue
        if m.group(1) not in ALLOWED_RECOMMENDATIONS:
            problems.append(f"{name}: recommendation={m.group(1)!r} not in allowed set")
    assert not problems, "Scorecard recommendation problems:\n" + "\n".join(problems)


def test_no_single_run_deprecation_recommendation() -> None:
    """A scorecard entry must not use deprecation_review or deprecation_watch as its Recommendation value
    unless it references multiple distinct EV-### ids (deprecation requires repeated evidence).
    The word may appear in prose describing the rule itself."""
    recommendation_re = re.compile(r"\*\*Recommendation:\*\*\s*[`]?(\w+)[`]?")
    for path in (SKILL_SCORE, WORKFLOW_SCORE):
        text = path.read_text(encoding="utf-8")
        # Walk the entries and check the Recommendation value if it is a deprecation_* value.
        # We don't need to validate the EV count here — that's `test_evidence_traceability`'s job.
        for m in recommendation_re.finditer(text):
            rec = m.group(1)
            if rec not in {"deprecation_review", "deprecation_watch"}:
                continue
            # If deprecation_* is recommended, the entry's body must reference multiple EV-### ids.
            # Find the enclosing entry by walking backwards to the nearest "## " header.
            start_search = text.rfind("\n## ", 0, m.start())
            entry_text = text[start_search:m.end() + 5000]  # entry body
            evs = set(EV_RE.findall(entry_text))
            if len(evs) < 2:
                pytest.fail(
                    f"{path.name}: Recommendation {rec!r} requires references to >=2 distinct EV-### "
                    f"ids (repeated evidence). Found: {sorted(evs)}"
                )


def test_scores_below_three_have_evidence_and_remediation() -> None:
    """Where a score is <3, the entry must include 'Evidence below 3', 'Observed impact', 'Proposed remediation', 'Validation needed'."""
    for path in (SKILL_SCORE, WORKFLOW_SCORE):
        sections = _scorecard_sections(path)
        entries = sections[1:] if len(sections) > 1 else []
        for name, body in entries:
            # Detect any "| <dim> | 1 |" or "| <dim> | 2 |" rows
            rows = re.findall(r"\|\s*([a-z_]+)\s*\|\s*([12])\s*\|", body)
            if not rows:
                continue
            required_sections = (
                "Evidence below 3",
                "Observed impact",
                "Proposed remediation",
                "Validation needed",
            )
            for sec in required_sections:
                if sec not in body:
                    pytest.fail(
                        f"{path.name} :: {name} has score <3 ({rows}) but missing {sec!r}"
                    )
