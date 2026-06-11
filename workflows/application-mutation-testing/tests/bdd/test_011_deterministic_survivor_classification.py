from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mutationctl.models import NormalizedMutant
from mutationctl.ledger.renderer import render_ledger
from mutationctl.state.store import StateStore
from mutationctl.survivors.classifier import classify_survivor


def _fixture_survivors(project_root: Path, name: str) -> list[NormalizedMutant]:
    path = project_root / "tests" / "fixtures" / "survivors" / name
    items = json.loads(path.read_text(encoding="utf-8"))
    for item in items:
        item["evidence"] = ", ".join(item["evidence"])
    return [NormalizedMutant(**item) for item in items]


def test_given_boundary_survivor_when_classified_then_missing_edge_case_returned(project_root: Path) -> None:
    survivor = _fixture_survivors(project_root, "deterministic_survivors.json")[0]
    result = classify_survivor(survivor)
    assert result.classification == "Missing edge case"
    assert result.recommended_action == "Add boundary value test"


def test_given_literal_replacement_survivor_when_classified_then_missing_assertion_returned(
    project_root: Path,
) -> None:
    survivor = _fixture_survivors(project_root, "deterministic_survivors.json")[1]
    result = classify_survivor(survivor)
    assert result.classification == "Missing assertion"
    assert "exact returned value" in result.recommended_action


def test_given_error_path_survivor_when_classified_then_missing_error_path_test_returned(
    project_root: Path,
) -> None:
    survivor = _fixture_survivors(project_root, "deterministic_survivors.json")[2]
    result = classify_survivor(survivor)
    assert result.classification == "Missing error-path test"


def test_given_ambiguous_survivor_when_classified_then_routed_to_llm_review(project_root: Path) -> None:
    survivor = _fixture_survivors(project_root, "ambiguous_survivors.json")[0]
    result = classify_survivor(survivor)
    assert result.classification is None
    assert result.requires_llm_review is True


def test_given_survivor_without_evidence_when_classified_then_classification_is_blocked_or_rejected(
    project_root: Path,
) -> None:
    survivor = _fixture_survivors(project_root, "deterministic_survivors.json")[0]
    survivor.evidence = ""
    result = classify_survivor(survivor)
    assert result.status == "BLOCKED"
    assert result.classification is None


def test_given_deterministic_classification_when_store_supplied_then_it_is_persisted(
    project_root: Path, tmp_path: Path
) -> None:
    store = StateStore(tmp_path)
    store.initialize()
    survivor = _fixture_survivors(project_root, "deterministic_survivors.json")[0]
    classify_survivor(survivor, store=store)
    assert store.list_survivor_classifications()[0].classification == "Missing edge case"


def test_given_workspace_survivor_when_cli_runs_then_deterministic_classification_is_reported(
    project_root: Path, tmp_path: Path
) -> None:
    store = StateStore(tmp_path)
    store.initialize()
    survivor = _fixture_survivors(project_root, "deterministic_survivors.json")[0]
    store.record_surviving_mutant(survivor)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "mutationctl",
            "classify-survivors",
            "--workspace",
            str(tmp_path),
            "--deterministic-only",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "Missing edge case" in completed.stdout


def test_given_persisted_classification_when_ledger_rendered_then_survivor_analysis_is_visible(
    project_root: Path, tmp_path: Path
) -> None:
    store = StateStore(tmp_path)
    store.initialize()
    survivor = _fixture_survivors(project_root, "deterministic_survivors.json")[0]
    classify_survivor(survivor, store=store)
    ledger = render_ledger(store).read_text(encoding="utf-8")
    assert "## Survivor Analysis" in ledger
    assert "Classification: Missing edge case" in ledger
    assert "Real LLM execution: NOT_RUN" in ledger
