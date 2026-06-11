from __future__ import annotations

from uuid import uuid4

from mutationctl.models import Blocker, MutationRecheckPlan, MutationRecheckResult, NormalizedMutant
from mutationctl.mutation.adapters import ADAPTERS
from mutationctl.models import MutationTarget


def plan_recheck(baseline: dict) -> MutationRecheckPlan:
    tool = baseline["tool_name"]
    target_file = baseline["target_file"]
    target = MutationTarget(target_file, _language(tool), 0, "PASS", "baseline scope", 0, 0, 0, True)
    command = ADAPTERS[tool]().build_command(target, ".").command
    baseline_command = baseline["command"].split() if isinstance(baseline["command"], str) else baseline["command"]
    return MutationRecheckPlan(target_file, baseline_command, command, tool, target_file, ["baseline mutation result"])


def run_recheck(store, runner, recheck_fixture: dict):
    baseline = store.get_recheck_baseline()
    if baseline is None:
        store.record_blocker(Blocker("MUTATION_RECHECK_BASELINE_MISSING", "BLOCKED", "Mutation recheck requires baseline evidence", "mutation_results"))
        return None
    plan = plan_recheck(baseline)
    store.record_mutation_recheck_plan(plan)
    command_result = runner.run(plan.recheck_command, cwd=store.workspace, timeout=1800)
    command_result.command = plan.recheck_command
    store.record_command(command_result)
    if command_result.timed_out:
        status = "BLOCKED"
        store.record_blocker(Blocker("MUTATION_RECHECK_TIMEOUT", "BLOCKED", "Mutation recheck timed out", plan.target_file))
    else:
        improved = recheck_fixture.get("survived", 0) < baseline.get("survived", 0)
        status = "PASS" if improved else "PARTIAL"
    before = baseline.get("score")
    after = recheck_fixture.get("score")
    delta = round(after - before, 2) if before is not None and after is not None else None
    survivors = [_mutant(item) for item in recheck_fixture.get("survivors", [])]
    result = MutationRecheckResult(
        plan.target_file, "baseline", f"recheck-{uuid4().hex[:10]}", plan.recheck_command, status,
        baseline.get("killed"), baseline.get("survived"), before,
        recheck_fixture.get("killed"), recheck_fixture.get("survived"), after, delta, survivors,
        ["baseline mutation result", " ".join(plan.recheck_command), *[item.evidence for item in survivors]],
    )
    store.record_mutation_recheck_result(result)
    if store.get_latest_validation_summary() is not None:
        from mutationctl.validation.gates import evaluate_validation_gates

        latest_run = store.get_latest_run()
        allow_commit = bool(latest_run and latest_run.config.get("allow_commit", False))
        evaluate_validation_gates(store, allow_commit=allow_commit)
    return result


def _mutant(item):
    raw = dict(item)
    evidence = raw.get("evidence", [])
    raw["evidence"] = ", ".join(evidence) if isinstance(evidence, list) else evidence
    return NormalizedMutant(**raw)


def _language(tool):
    return {"mutmut": "python", "stryker": "javascript", "pit": "java"}[tool]
