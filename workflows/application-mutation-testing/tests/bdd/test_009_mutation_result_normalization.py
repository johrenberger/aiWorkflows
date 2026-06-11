from __future__ import annotations

from pathlib import Path

from mutationctl.mutation.normalizer import normalize_mutation_report
from mutationctl.ledger.renderer import render_ledger
from mutationctl.state.store import StateStore


def test_given_mutmut_output_with_survivors_when_normalized_then_surviving_mutants_are_persisted(
    project_root: Path, tmp_path: Path
) -> None:
    report = project_root / "tests" / "fixtures" / "reports" / "mutmut" / "mutmut_survivors_output.txt"
    store = StateStore(tmp_path)
    store.initialize()
    result = normalize_mutation_report("mutmut", report, store)
    assert result.killed == 3
    assert result.survived == 2
    assert len(store.list_surviving_mutants()) == 2
    assert result.mutation_score == 60.0


def test_given_mutmut_output_without_survivors_when_normalized_then_zero_survivors_recorded(
    project_root: Path,
) -> None:
    report = project_root / "tests" / "fixtures" / "reports" / "mutmut" / "mutmut_no_survivors_output.txt"
    result = normalize_mutation_report("mutmut", report)
    assert result.survived == 0
    assert result.mutation_score == 100.0


def test_given_stryker_json_when_normalized_then_common_mutant_statuses_are_used(project_root: Path) -> None:
    report = project_root / "tests" / "fixtures" / "reports" / "stryker" / "stryker-basic.json"
    result = normalize_mutation_report("stryker", report)
    assert {mutant.status for mutant in result.mutants} == {"KILLED", "SURVIVED", "TIMEOUT", "IGNORED"}


def test_given_pit_xml_when_normalized_then_common_mutant_statuses_are_used(project_root: Path) -> None:
    report = project_root / "tests" / "fixtures" / "reports" / "pit" / "pit-mutations.xml"
    result = normalize_mutation_report("pit", report)
    assert {mutant.status for mutant in result.mutants} == {"KILLED", "SURVIVED"}


def test_given_output_without_count_evidence_when_normalized_then_score_is_unavailable(tmp_path: Path) -> None:
    report = tmp_path / "unknown.txt"
    report.write_text("Mutation output unavailable", encoding="utf-8")
    result = normalize_mutation_report("mutmut", report)
    assert result.mutation_score is None


def test_given_normalized_result_when_ledger_rendered_then_score_and_survivors_come_from_state(
    project_root: Path, tmp_path: Path
) -> None:
    report = project_root / "tests" / "fixtures" / "reports" / "mutmut" / "mutmut_survivors_output.txt"
    store = StateStore(tmp_path)
    store.initialize()
    normalize_mutation_report("mutmut", report, store)
    ledger = render_ledger(store).read_text(encoding="utf-8")
    assert "Mutation Score: 60.00%" in ledger
    assert "mutmut-1: src/sample.py:2 conditional_boundary" in ledger
