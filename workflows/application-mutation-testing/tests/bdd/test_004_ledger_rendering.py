from __future__ import annotations

from pathlib import Path

from mutationctl.config import load_workflow_config
from mutationctl.ledger.renderer import render_ledger
from mutationctl.models import Blocker, LedgerTask, RepoMetadata
from mutationctl.state.store import StateStore


def test_given_state_with_metadata_when_ledger_rendered_then_required_sections_exist(tmp_path: Path) -> None:
    store = _seed_store(tmp_path)

    ledger_path = render_ledger(store)
    ledger_text = ledger_path.read_text(encoding="utf-8")

    for section in [
        "# Mutation Testing Ledger",
        "## Repository Context",
        "## Workflow Configuration",
        "## Execution Status",
        "## Command Log",
        "## Mutation Tool Detection",
        "## Coverage Context",
        "## Selected Targets",
        "## Mutation Results",
        "## Surviving Mutants",
        "## Test Hardening Actions",
        "## Validation Gates",
        "## Blockers",
        "## Files Changed",
        "## Commit Status",
        "## Remaining Work",
    ]:
        assert section in ledger_text


def test_given_no_mutation_results_when_ledger_rendered_then_score_is_not_invented(tmp_path: Path) -> None:
    store = _seed_store(tmp_path)

    ledger_text = render_ledger(store).read_text(encoding="utf-8")

    assert "Mutation score:" not in ledger_text
    assert "NOT_RUN" in ledger_text


def test_given_blocker_when_ledger_rendered_then_reason_and_evidence_are_included(tmp_path: Path) -> None:
    store = _seed_store(tmp_path)
    store.record_blocker(
        Blocker(
            code="INVALID_REPO",
            status="BLOCKED",
            reason="Repository URL must target GitHub",
            evidence="https://example.com/not-github/project",
        )
    )

    ledger_text = render_ledger(store).read_text(encoding="utf-8")

    assert "Repository URL must target GitHub" in ledger_text
    assert "https://example.com/not-github/project" in ledger_text


def test_given_existing_ledger_tasks_when_rendered_twice_then_task_ids_are_stable(tmp_path: Path) -> None:
    store = _seed_store(tmp_path)
    store.upsert_ledger_task(LedgerTask(task_id="LEDGER-001", title="Inspect blockers", status="NOT_RUN"))

    first_render = render_ledger(store).read_text(encoding="utf-8")
    second_render = render_ledger(store).read_text(encoding="utf-8")

    assert "- [ ] LEDGER-001: Inspect blockers" in first_render
    assert "- [ ] LEDGER-001: Inspect blockers" in second_render


def _seed_store(tmp_path: Path) -> StateStore:
    store = StateStore(tmp_path)
    store.initialize()
    config = load_workflow_config({"repo": "https://github.com/example/project"})
    repo_metadata = RepoMetadata(
        repo_path=str(tmp_path),
        repo_url="https://github.com/example/project",
        branch="main",
        commit_sha="abc1234",
        is_dirty=False,
        captured_at="2026-06-10T12:00:00+00:00",
    )
    store.create_run(config, repo_metadata)
    return store
