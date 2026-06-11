from __future__ import annotations

from mutationctl.models import ValidationGateResult, ValidationSummary

GATES = [
    ("MT-VAL-1", "Repository input captured"),
    ("MT-VAL-2", "Repository metadata recorded"),
    ("MT-VAL-3", "Mutation tool detected or blocker documented"),
    ("MT-VAL-4", "Mutation targets selected or exclusion documented"),
    ("MT-VAL-5", "Scoped baseline mutation run completed or blocker documented"),
    ("MT-VAL-6", "Survivors normalized and classified with evidence"),
    ("MT-VAL-7", "Test hardening applied or intentionally skipped"),
    ("MT-VAL-8", "Focused tests pass or blocker documented"),
    ("MT-VAL-9", "Mutation recheck completed or blocker documented"),
    ("MT-VAL-10", "Ledger rendered from structured state"),
    ("MT-VAL-11", "Commit blocked unless explicitly allowed"),
    ("MT-VAL-12", "Commit allowed only when required gates pass"),
]


def evaluate_validation_gates(store, allow_commit: bool = False) -> ValidationSummary:
    blockers = store.list_blockers()
    blocker_codes = {item.code for item in blockers}
    latest_run = store.get_latest_run()
    metadata = store.get_repo_metadata(latest_run.run_id) if latest_run else None
    tool = store.get_latest_tool_detection()
    targets = store.list_targets()
    baselines = store.list_mutation_results()
    survivors = store.list_surviving_mutants()
    classifications = store.list_survivor_classifications()
    patches = store.list_patch_safety_results()
    patch_applies = store.list_patch_apply_results()
    focused = store.list_focused_test_results()
    rechecks = store.list_mutation_recheck_results()

    results = []
    results.append(_gate(1, bool(latest_run and (latest_run.repo_url or latest_run.repo_path)), "Repository input is persisted", [latest_run.run_id] if latest_run else []))
    results.append(_gate(2, bool(metadata and metadata.branch and metadata.commit_sha and metadata.captured_at), "Branch, commit, dirty status, and timestamp are persisted", [metadata.commit_sha] if metadata else []))
    results.append(_with_blocker(3, bool(tool and tool.selected_tool), "Mutation tool evidence exists", [tool.selected_tool] if tool and tool.selected_tool else [], "MUTATION_TOOL_NOT_FOUND", blocker_codes))
    results.append(_gate(4, bool(targets), "Target selection evidence exists", [item.source_file for item in targets]))
    results.append(_with_blocker(5, bool(baselines), "Baseline mutation evidence exists", [" ".join(item.command) for item in baselines], "MUTATION_TOOL_NOT_FOUND", blocker_codes))
    classification_ok = bool(classifications) and all(item.evidence for item in classifications)
    if survivors and not classification_ok:
        results.append(_result(6, "FAIL", "Survivors lack evidence-backed classifications", []))
    else:
        results.append(_gate(6, bool(classifications), "Survivor classifications include evidence", [item.classification_id for item in classifications if item.evidence]))
    patch_ok = bool(patches) and bool(patch_applies) and all(item.accepted for item in patches) and patch_applies[-1].applied
    patch_skipped = "PATCH_INTENTIONALLY_SKIPPED" in blocker_codes
    results.append(_result(7, "PASS" if patch_ok else ("EXCLUDED" if patch_skipped else "NOT_RUN"), "Test hardening evidence exists" if patch_ok else "No applied or intentionally skipped patch evidence", [item.proposal_id for item in patches]))
    focused_ok = bool(focused) and focused[-1].status == "PASS"
    results.append(_with_blocker(8, focused_ok, "Focused tests passed", [" ".join(focused[-1].command)] if focused else [], "FOCUSED_TESTS_FAILED", blocker_codes))
    recheck_ok = bool(rechecks) and rechecks[-1].status in {"PASS", "PARTIAL"}
    results.append(_with_blocker(9, recheck_ok, "Mutation recheck evidence exists", [rechecks[-1].recheck_result_id] if rechecks else [], "MUTATION_RECHECK_TIMEOUT", blocker_codes))
    ledger_ok = store.ledger_path.is_file() and store.ledger_path.stat().st_size > 0
    results.append(_gate(10, ledger_ok, "Ledger artifact exists", [str(store.ledger_path)] if ledger_ok else []))
    results.append(_result(11, "PASS", "Commit permission is explicit; default remains blocked" if not allow_commit else "Commit permission was explicitly enabled", [f"allow_commit={str(allow_commit).lower()}"]))

    preliminary_failures = [item.gate_id for item in results if item.required and item.status in {"FAIL", "NOT_RUN"}]
    commit_allowed = allow_commit and not preliminary_failures
    commit_gate_passes = not allow_commit or not preliminary_failures
    results.append(
        _result(
            12,
            "PASS" if commit_gate_passes else "FAIL",
            (
                "Commit remains blocked by default"
                if not allow_commit
                else "Required gates pass and commit is allowed"
                if commit_allowed
                else "Commit permission is enabled but required validation gates failed"
            ),
            preliminary_failures or [f"allow_commit={allow_commit}"],
        )
    )
    blocking = [item.gate_id for item in results if item.status in {"FAIL", "BLOCKED", "NOT_RUN"}]
    summary = ValidationSummary(
        len(results),
        sum(item.status == "PASS" for item in results),
        sum(item.status == "PARTIAL" for item in results),
        sum(item.status == "BLOCKED" for item in results),
        sum(item.status == "FAIL" for item in results),
        sum(item.status == "NOT_RUN" for item in results),
        not any(item.gate_id != "MT-VAL-12" and item.status in {"FAIL", "NOT_RUN"} for item in results),
        commit_allowed,
        blocking,
        [f"{item.gate_id}:{item.status}" for item in results],
        results,
    )
    store.record_validation_summary(summary)
    return summary


def _gate(number, passed, reason, evidence):
    return _result(number, "PASS" if passed and evidence else "FAIL", reason if passed else f"Missing evidence: {reason}", evidence)


def _with_blocker(number, passed, reason, evidence, blocker_code, blocker_codes):
    if passed:
        return _result(number, "PASS", reason, evidence)
    if blocker_code in blocker_codes:
        return _result(number, "BLOCKED", f"{reason} is blocked with documented evidence", [blocker_code])
    return _result(number, "FAIL", f"Missing evidence: {reason}", [])


def _result(number, status, reason, evidence):
    gate_id, name = GATES[number - 1]
    return ValidationGateResult(gate_id, name, status, reason, list(evidence), True)
