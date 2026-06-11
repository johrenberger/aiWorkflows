from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

from mutationctl.config import load_workflow_config
from mutationctl.coverage.ingest import ingest_coverage
from mutationctl.detection.language import detect_languages
from mutationctl.detection.mutation_tools import detect_mutation_tools
from mutationctl.ledger.renderer import render_ledger
from mutationctl.command_runner import FakeCommandRunner
from mutationctl.command_runner import SubprocessCommandRunner
from mutationctl.git.commit_gate import execute_commit, plan_commit
from mutationctl.git.fake_adapter import FakeGitAdapter
from mutationctl.llm.fake_client import FakeLLMClient
from mutationctl.llm.response_validator import validate_classification_response
from mutationctl.llm.schemas import build_classification_request
from mutationctl.models import Blocker, ChangedFile, CommandResult, GitStatus, RealToolPolicy
from mutationctl.mutation.adapters import execute_baseline
from mutationctl.patches.parser import parse_patch
from mutationctl.patches.safety import validate_patch_safety
from mutationctl.state.store import StateStore
from mutationctl.survivors.classifier import classify_survivor
from mutationctl.targeting.selector import select_targets
from mutationctl.validation.gates import evaluate_validation_gates
from mutationctl.validation.mutation_recheck import run_recheck
from mutationctl.workflow.orchestrator import run_synthetic_workflow
from mutationctl.workflow.real_tool_policy import evaluate_real_mutmut_policy

def build_parser():
    parser = argparse.ArgumentParser(prog="mutationctl", description="Deterministic control plane for mutation testing workflows.")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize workflow state.")
    init_parser.add_argument("--workspace", default=".")

    detect_parser = subparsers.add_parser("detect", help="Detect local language and mutation tool evidence.")
    detect_parser.add_argument("--repo-path", required=True)
    detect_parser.add_argument("--workspace")

    coverage_parser = subparsers.add_parser("ingest-coverage", help="Ingest a local coverage artifact.")
    coverage_parser.add_argument("--repo-path", required=True)
    coverage_parser.add_argument("--coverage-path")
    coverage_parser.add_argument("--workspace")

    target_parser = subparsers.add_parser("select-targets", help="Select bounded deterministic mutation targets.")
    target_parser.add_argument("--repo-path", required=True)
    target_parser.add_argument("--max-target-files", type=int, default=5)
    target_parser.add_argument("--workspace")

    baseline_parser = subparsers.add_parser("run-baseline", help="Record a scoped fake mutation baseline.")
    baseline_parser.add_argument("--repo-path", required=True)
    baseline_parser.add_argument("--target-file")
    baseline_parser.add_argument("--workspace")
    baseline_parser.add_argument("--fake", action="store_true")
    baseline_parser.add_argument("--real-tools", action="store_true")
    baseline_parser.add_argument("--mutmut", action="store_true")
    baseline_parser.add_argument("--timeout-seconds", type=int, default=600)
    baseline_parser.add_argument("--allow-dirty-tree", action="store_true")
    baseline_parser.add_argument("--allow-dependency-install", action="store_true")

    classify_parser = subparsers.add_parser(
        "classify-survivors",
        help="Classify persisted survivors with deterministic rules or an explicit fake client.",
    )
    classify_parser.add_argument("--workspace", required=True)
    classify_mode = classify_parser.add_mutually_exclusive_group(required=True)
    classify_mode.add_argument("--deterministic-only", action="store_true")
    classify_mode.add_argument("--fake-llm", action="store_true")

    patch_parser = subparsers.add_parser("validate-patch", help="Validate patch scope and test safety.")
    patch_parser.add_argument("--workspace", required=True)
    patch_parser.add_argument("--patch", required=True)
    patch_parser.add_argument("--allow-test-changes", action="store_true")
    patch_parser.add_argument("--allow-production-fixes", action="store_true")

    validate_parser = subparsers.add_parser("validate", help="Evaluate and persist MT-VAL validation gates.")
    validate_parser.add_argument("--workspace", required=True)
    validate_parser.add_argument("--strict", action="store_true")
    validate_parser.add_argument("--allow-commit", action="store_true")

    recheck_parser = subparsers.add_parser("recheck", help="Run a fake scoped mutation recheck.")
    recheck_parser.add_argument("--workspace", required=True)
    recheck_parser.add_argument("--fake", action="store_true")
    recheck_parser.add_argument("--fixture")

    commit_plan_parser = subparsers.add_parser("commit-plan", help="Create an evidence-backed branch-safe commit plan.")
    commit_plan_parser.add_argument("--workspace", required=True)
    commit_plan_parser.add_argument("--allow-commit", action="store_true")

    commit_parser = subparsers.add_parser("commit", help="Execute an allowed commit plan through an explicit adapter.")
    commit_parser.add_argument("--workspace", required=True)
    commit_parser.add_argument("--fake", action="store_true")

    run_parser = subparsers.add_parser("run", help="Run the deterministic workflow.")
    run_parser.add_argument("--repo-path", required=True)
    run_parser.add_argument("--workspace")
    run_parser.add_argument("--synthetic", action="store_true")
    run_parser.add_argument("--mode", choices=["report-only","fake-implementation"], default="report-only")
    run_parser.add_argument("--allow-test-changes", action="store_true")
    run_parser.add_argument("--allow-commit", action="store_true")

    for command in [
        "harden-tests",
    ]:
        command_parser = subparsers.add_parser(command, help=f"{command} is scaffolded for a future pass.")
        command_parser.add_argument("--repo")

    render_parser = subparsers.add_parser("render-ledger", help="Render TODO_mutation-testing.md from structured state.")
    render_parser.add_argument("--workspace", default=".")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "init":
        workspace = Path(args.workspace).resolve()
        store = StateStore(workspace)
        store.initialize()
        return 0

    if args.command == "render-ledger":
        workspace = Path(args.workspace).resolve()
        store = StateStore(workspace)
        store.initialize()
        render_ledger(store)
        return 0

    if args.command == "detect":
        repo_path = Path(args.repo_path).resolve()
        store = _optional_store(args.workspace)
        languages = detect_languages(repo_path)
        tools = detect_mutation_tools(repo_path, store=store)
        print(
            json.dumps(
                {
                    "languages": [item.language for item in languages],
                    "selected_tool": tools.selected_tool,
                    "status": tools.status,
                },
                sort_keys=True,
            )
        )
        return 0

    if args.command == "ingest-coverage":
        store = _optional_store(args.workspace)
        result = ingest_coverage(args.repo_path, args.coverage_path, store=store)
        print(json.dumps({"status": result.status, "evidence_path": result.evidence_path, "files": len(result.files)}))
        return 0

    if args.command == "select-targets":
        repo_path = Path(args.repo_path).resolve()
        store = _optional_store(args.workspace)
        languages = detect_languages(repo_path)
        tools = detect_mutation_tools(repo_path)
        language = languages[0].language if languages else "unknown"
        result = select_targets(
            repo_path,
            language,
            tools.selected_tool,
            max_target_files=args.max_target_files,
            store=store,
        )
        print(json.dumps({"status": result.status, "selected": [item.source_file for item in result.selected]}))
        return 0

    if args.command == "run-baseline":
        repo_path = Path(args.repo_path).resolve()
        store = _optional_store(args.workspace or str(repo_path))
        languages = detect_languages(repo_path)
        tools = detect_mutation_tools(repo_path, store=store)
        language = languages[0].language if languages else "unknown"
        targets = select_targets(repo_path, language, tools.selected_tool, max_target_files=1, store=store)
        if not targets.selected:
            print(json.dumps({"status": "BLOCKED", "reason": "No target selected"}))
            return 0
        target = targets.selected[0]
        if args.target_file:
            target.source_file = args.target_file
        if args.real_tools:
            policy=RealToolPolicy(
                allow_real_tools=True,
                allow_mutmut=args.mutmut,
                allow_dependency_install=args.allow_dependency_install,
                timeout_seconds=args.timeout_seconds,
                allow_dirty_tree=args.allow_dirty_tree,
            )
            decision=evaluate_real_mutmut_policy(
                policy,repo_path,[target],shutil.which("mutmut") is not None,_git_dirty(repo_path),
                platform_supported=_fork_supported(),store=store,
            )
            if not decision.allowed:
                print(json.dumps({"status":"BLOCKED","blockers":decision.blockers}))
                return 0
            result=SubprocessCommandRunner().run(decision.command,cwd=repo_path,timeout=policy.timeout_seconds)
            store.record_command(result); store.record_real_tool_result(result)
            print(json.dumps({"status":result.status,"command":decision.command}))
            return 0
        if not args.fake:
            policy=RealToolPolicy()
            decision=evaluate_real_mutmut_policy(policy,repo_path,[target],False,False,store=store)
            print(json.dumps({"status":"BLOCKED","blockers":decision.blockers}))
            return 0
        runner = FakeCommandRunner([CommandResult([], 0, 0.0, "PASS")])
        result = execute_baseline(target, tools.selected_tool, repo_path, runner, store)
        print(json.dumps({"status": result.status if result else "BLOCKED", "target": target.source_file}))
        return 0

    if args.command == "commit-plan":
        store=StateStore(Path(args.workspace).resolve()); store.initialize()
        status=store.get_latest_git_status() or GitStatus("main","unknown",False,[],[],["No Git status persisted; planning remains conservative"])
        plan,gate=plan_commit(store,status,args.allow_commit)
        print(json.dumps({"commit_allowed":plan.commit_allowed,"branch":plan.proposed_branch,"blockers":gate.blockers}))
        return 0

    if args.command == "commit":
        store=StateStore(Path(args.workspace).resolve()); store.initialize()
        plan=store.get_latest_commit_plan()
        if plan is None:
            print(json.dumps({"status":"BLOCKED","reason":"No commit plan exists"}))
            return 0
        if not args.fake:
            print(json.dumps({"status":"BLOCKED","reason":"Only --fake commit execution is implemented"}))
            return 0
        result=execute_commit(plan,FakeGitAdapter(),store)
        print(json.dumps({"status":result.status,"commit_created":result.commit_created,"commit_sha":result.commit_sha}))
        return 0

    if args.command == "classify-survivors":
        store = StateStore(Path(args.workspace).resolve())
        store.initialize()
        survivors = store.list_surviving_mutants()
        classifications = [classify_survivor(survivor, store=store) for survivor in survivors]
        if args.fake_llm:
            packets_by_mutant = {packet.mutant_id: packet for packet in store.list_survivor_packets()}
            accepted = 0
            rejected = 0
            for classification in classifications:
                if not classification.requires_llm_review:
                    continue
                packet = packets_by_mutant.get(classification.mutant_id)
                if packet is None:
                    store.record_blocker(
                        Blocker(
                            "SURVIVOR_PACKET_MISSING",
                            "BLOCKED",
                            "Fake LLM classification requires a persisted survivor packet",
                            classification.mutant_id,
                        )
                    )
                    rejected += 1
                    continue
                request = build_classification_request(
                    packet,
                    request_id=f"llm-{classification.mutant_id}",
                    store=store,
                )
                configured_response = {
                    "schema_version": "1.0",
                    "request_id": request.request_id,
                    "packet_id": request.packet_id,
                    "mutant_id": request.mutant_id,
                    "classification": "Production ambiguity",
                    "confidence": "low",
                    "evidence": list(packet.evidence),
                    "recommended_action": "Review the bounded survivor packet with a human.",
                    "equivalent_candidate": False,
                    "needs_human_review": True,
                    "rationale": "The deterministic classifier found no medium-confidence rule.",
                }
                raw_response = FakeLLMClient(configured_response).classify(request)
                validation = validate_classification_response(request, raw_response, store)
                accepted += int(validation.accepted)
                rejected += int(not validation.accepted)
            print(
                json.dumps(
                    {
                        "status": "PASS" if accepted else "PARTIAL",
                        "deterministic": [item.classification for item in classifications],
                        "fake_llm_accepted": accepted,
                        "fake_llm_rejected": rejected,
                    }
                )
            )
            return 0
        print(
            json.dumps(
                {
                    "status": "PASS" if survivors else "NOT_RUN",
                    "classifications": [item.classification for item in classifications],
                    "llm_review_required": sum(item.requires_llm_review for item in classifications),
                }
            )
        )
        return 0

    if args.command == "validate-patch":
        store = StateStore(Path(args.workspace).resolve()); store.initialize()
        proposal = parse_patch(args.patch)
        result = validate_patch_safety(
            proposal,
            allow_test_changes=args.allow_test_changes,
            allow_production_fixes=args.allow_production_fixes,
            store=store,
        )
        print(json.dumps({"status": result.status, "accepted": result.accepted, "reasons": result.reasons}))
        return 0

    if args.command == "validate":
        store = StateStore(Path(args.workspace).resolve()); store.initialize()
        summary = evaluate_validation_gates(store, allow_commit=args.allow_commit)
        print(json.dumps({
            "required_gates_passed": summary.required_gates_passed,
            "commit_allowed": summary.commit_allowed,
            "blocking_gate_ids": summary.blocking_gate_ids,
        }))
        return 1 if args.strict and not summary.required_gates_passed else 0

    if args.command == "recheck":
        if not args.fake:
            parser.error("Only --fake mutation recheck is supported in this pass")
        if not args.fixture:
            parser.error("--fixture is required with --fake")
        store = StateStore(Path(args.workspace).resolve()); store.initialize()
        fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        runner = FakeCommandRunner([CommandResult([], 0, 0.0, "PASS")])
        result = run_recheck(store, runner, fixture)
        print(json.dumps({
            "status": result.status if result else "BLOCKED",
            "score_delta": result.score_delta if result else None,
            "remaining_survivors": len(result.remaining_survivors) if result else 0,
        }))
        return 0

    if args.command == "run":
        if not args.synthetic:
            parser.error("Only --synthetic workflow execution is supported in this pass")
        workspace=Path(args.workspace).resolve() if args.workspace else Path.cwd()/".mutationctl-synthetic-run"
        fixture_dir=Path(__file__).resolve().parents[2]/"tests"/"fixtures"/"e2e"
        result=run_synthetic_workflow(
            args.repo_path,workspace,args.mode,fixture_dir,
            allow_test_changes=args.allow_test_changes,allow_commit=args.allow_commit,
        )
        print(json.dumps({"run_id":result.run_id,"status":result.status,"ledger_path":result.ledger_path,"final_summary_path":result.final_summary_path}))
        return 0

    print(f"{args.command} is not implemented in this pass.")
    return 0


def _optional_store(workspace: str | None):
    if not workspace:
        return None
    store = StateStore(Path(workspace).resolve())
    store.initialize()
    return store


def _git_dirty(repo_path: Path) -> bool:
    if not (repo_path/".git").exists():
        return False
    completed=subprocess.run(["git","status","--porcelain"],cwd=repo_path,capture_output=True,text=True,check=False)
    return bool(completed.stdout.strip())


def _fork_supported() -> bool:
    if platform.system() != "Windows":
        return True
    return bool(os.getenv("WSL_DISTRO_NAME"))
