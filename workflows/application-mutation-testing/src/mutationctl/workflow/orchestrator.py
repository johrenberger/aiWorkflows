from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from mutationctl.command_runner import FakeCommandRunner
from mutationctl.config import WorkflowConfig
from mutationctl.coverage.ingest import ingest_coverage
from mutationctl.detection.language import detect_languages
from mutationctl.detection.mutation_tools import detect_mutation_tools
from mutationctl.git.commit_gate import plan_commit
from mutationctl.ledger.renderer import render_ledger
from mutationctl.models import (
    ChangedFile, CommandResult, FocusedTestCommand, GitStatus, MutationRunResult,
    NormalizedMutant, NormalizedMutationResult, RepoMetadata, WorkflowRunResult,
)
from mutationctl.patches.apply import apply_patch_proposal
from mutationctl.patches.parser import parse_patch
from mutationctl.patches.safety import validate_patch_safety
from mutationctl.reporting.final_summary import render_final_summary
from mutationctl.state.store import StateStore
from mutationctl.survivors.classifier import classify_survivor
from mutationctl.survivors.packet_builder import build_survivor_packet
from mutationctl.targeting.selector import select_targets
from mutationctl.validation.focused_tests import run_focused_tests
from mutationctl.validation.gates import evaluate_validation_gates
from mutationctl.validation.mutation_recheck import run_recheck
from mutationctl.workflow.synthetic import prepare_synthetic_repo


def run_synthetic_workflow(
    repo_path: str | Path,
    workspace: str | Path,
    mode: str,
    fixture_dir: str | Path,
    allow_test_changes: bool = False,
    allow_commit: bool = False,
) -> WorkflowRunResult:
    store = StateStore(workspace); store.initialize()
    repo = prepare_synthetic_repo(repo_path, workspace)
    fixture_root = Path(fixture_dir)
    phases = []
    config = WorkflowConfig(repo_path=str(repo), mode="report", allow_test_changes=allow_test_changes, allow_commit=allow_commit)
    metadata = RepoMetadata(str(repo), None, "synthetic/main", "synthetic-sha", False, datetime.now(UTC).isoformat())
    run = store.create_run(config, metadata); phases.append("intake")
    languages = detect_languages(repo)
    tools = detect_mutation_tools(repo, store=store); phases.append("detection")
    ingest_coverage(repo, store=store); phases.append("coverage")
    language = languages[0].language
    targets = select_targets(repo, language, tools.selected_tool, max_target_files=1, store=store); phases.append("targeting")
    baseline = json.loads((fixture_root / "fake_mutation_baseline.json").read_text(encoding="utf-8"))
    store.record_mutation_run(MutationRunResult("mutmut", baseline["target_file"], baseline["command"].split(), 0, "PASS", 0.0, None, None, ["fake_mutation_baseline.json"]))
    mutants = [_mutant(item) for item in baseline["survivors"]]
    normalized = NormalizedMutationResult("mutmut","PASS",baseline["killed"],baseline["survived"],baseline["timeout"],0,baseline["score"],str(fixture_root/"fake_mutation_baseline.json"),mutants)
    store.record_normalized_mutation_result(normalized)
    store.record_recheck_baseline(baseline); phases.append("baseline")
    for mutant in mutants:
        build_survivor_packet(mutant, repo, store=store)
        classify_survivor(mutant, store=store)
    phases.append("survivor-analysis")

    if mode == "fake-implementation":
        proposal = parse_patch(fixture_root / "fake_patch.patch")
        safety = validate_patch_safety(proposal, allow_test_changes=allow_test_changes, store=store)
        apply_patch_proposal(proposal, safety, repo, store=store)
        run_focused_tests(FocusedTestCommand(["python","-m","pytest","tests/test_sample.py"],str(repo),60), FakeCommandRunner([CommandResult([],0,0.1,"PASS")]), store)
        recheck = json.loads((fixture_root / "fake_recheck_improved.json").read_text(encoding="utf-8"))
        run_recheck(store, FakeCommandRunner([CommandResult([],0,0.2,"PASS")]), recheck)
        phases.extend(["test-hardening","focused-tests","recheck"])
    else:
        from mutationctl.models import Blocker
        store.record_blocker(Blocker("PATCH_INTENTIONALLY_SKIPPED","EXCLUDED","Report-only mode does not apply patches",mode))

    render_ledger(store)
    validation = evaluate_validation_gates(store, allow_commit=allow_commit); phases.append("validation")
    changed = [ChangedFile("tests/test_sample.py","modified",True,"synthetic test hardening")] if mode == "fake-implementation" else []
    git_status = GitStatus("main","synthetic-sha",bool(changed),changed,[],["synthetic git status"])
    commit_plan, _ = plan_commit(store, git_status, allow_commit, repo_slug="synthetic-e2e-python")
    render_ledger(store)
    status = "PASS" if mode == "fake-implementation" and validation.required_gates_passed else "PARTIAL"
    final = render_final_summary(store, run.run_id, mode, status)
    result = WorkflowRunResult(run.run_id,status,phases,[],str(store.ledger_path),final.path,validation,commit_plan,[str(repo)])
    store.record_workflow_run_result(result)
    return result


def _mutant(item):
    raw = dict(item)
    raw["evidence"] = ", ".join(raw.get("evidence", []))
    return NormalizedMutant(**raw)
