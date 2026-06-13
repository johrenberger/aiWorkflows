"""Story 019, open 2: ledger rendering must surface the v2:// evidence
prefix so reviewers can tell at a glance which coverage files came
from v2 (test-factory) vs internal sources.

Tests-first: this test should FAIL on master because the current
ledger rendering only prints the top-level evidence path and
per-file coverage % — it does not surface the per-file
``v2://`` evidence prefix that the v2 parser emits.
"""
from __future__ import annotations

from pathlib import Path

from mutationctl.config import load_workflow_config
from mutationctl.ledger.renderer import render_ledger
from mutationctl.models import CoverageFileSummary, CoverageSummary, RepoMetadata
from mutationctl.state.store import StateStore


def _seed_store_with_v2_coverage(tmp_path: Path) -> StateStore:
    store = StateStore(tmp_path)
    store.initialize()
    config = load_workflow_config({"repo": "https://github.com/example/project"})
    repo_metadata = RepoMetadata(
        repo_path=str(tmp_path),
        repo_url="https://github.com/example/project",
        branch="main",
        commit_sha="abc1234",
        is_dirty=False,
        captured_at="2026-06-13T12:00:00+00:00",
    )
    store.create_run(config, repo_metadata)
    # v2-sourced coverage: top-level evidence_path is the v2 artifact
    # (in-repo default location); per-file evidence_path carries the
    # v2:// lineage prefix.
    summary = CoverageSummary(
        source_file=None,
        line_coverage=None,
        branch_coverage=None,
        covered_lines=[],
        uncovered_lines=[],
        evidence_path="analysis-artifacts/risk_scores.json",
        status="PASS",
        files=[
            CoverageFileSummary(
                source_file="src/from_v2.py",
                line_coverage=85.0,
                branch_coverage=None,
                covered_lines=[],
                uncovered_lines=[],
                evidence_path="v2://src/risk_scores.json",
                status="PASS",
                complexity=12.0,
            ),
        ],
    )
    store.record_coverage_summary(summary)
    return store


def test_given_v2_sourced_coverage_when_ledger_rendered_then_v2_prefix_appears_in_coverage_section(
    tmp_path: Path,
) -> None:
    """Spike open 2: the per-file evidence_path prefix ``v2://`` must
    appear in the ledger's ``Coverage Context`` section, so reviewers
    can identify which files were sourced from v2 vs internal sources.

    Fails today: the ledger only renders ``{path}: {coverage}%`` per
    file, dropping the evidence_path. The test asserts the prefix
    appears in the ledger text.
    """
    store = _seed_store_with_v2_coverage(tmp_path)
    ledger_text = render_ledger(store).read_text(encoding="utf-8")

    # Find the Coverage Context section and assert it mentions v2://
    coverage_section = _extract_section(ledger_text, "Coverage Context")
    assert any(token in coverage_section for token in ("v2://", "(v2)", "source: v2")), (
        f"Ledger's Coverage Context section should surface a v2 "
        f"lineage marker; got:\n{coverage_section}"
    )


def test_given_v2_sourced_coverage_when_ledger_rendered_then_v2_source_label_appears(
    tmp_path: Path,
) -> None:
    """Open 2 (companion): a human-readable label like ``(v2)`` or
    ``source: v2 (test-factory)`` should appear next to v2-sourced
    files. Acceptable forms: ``v2://``, ``(v2)``, ``source: v2``."""
    store = _seed_store_with_v2_coverage(tmp_path)
    ledger_text = render_ledger(store).read_text(encoding="utf-8")
    coverage_section = _extract_section(ledger_text, "Coverage Context")
    assert any(token in coverage_section for token in ("v2://", "(v2)", "source: v2")), (
        f"Ledger should mark v2-sourced files with one of: v2://, (v2), "
        f"source: v2. Got:\n{coverage_section}"
    )


def _extract_section(ledger_text: str, section_name: str) -> str:
    """Return the text of ``## {section_name}`` up to the next ``## ``
    header. If the section is missing, return the empty string.
    """
    lines = ledger_text.splitlines()
    out: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith(f"## {section_name}"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            out.append(line)
    return "\n".join(out)
