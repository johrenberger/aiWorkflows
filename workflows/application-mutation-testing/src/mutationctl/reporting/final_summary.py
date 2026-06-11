from __future__ import annotations

from pathlib import Path

from mutationctl.models import FinalSummary

SECTIONS = [
    "Run Context", "Mode", "Targets", "Baseline Mutation Evidence", "Survivor Analysis",
    "Test Hardening", "Focused Test Results", "Mutation Recheck", "Validation Gates",
    "Commit Plan", "Blockers", "Remaining Work",
]


def render_final_summary(store, run_id: str, mode: str, status: str) -> FinalSummary:
    path = store.state_dir / "final_summary.md"
    targets = [item.source_file for item in store.list_targets() if item.selected]
    classifications = store.list_survivor_classifications()
    patches = store.list_patch_apply_results()
    focused = store.list_focused_test_results()
    rechecks = store.list_mutation_recheck_results()
    validation = store.get_latest_validation_summary()
    commits = store.list_commit_plans()
    blockers = store.list_blockers()
    content = ["# Mutationctl Final Summary", ""]
    values = {
        "Run Context": f"- Run: {run_id}\n- Ledger: {store.ledger_path}",
        "Mode": f"- {mode}\n- Mutation execution: fake\n- Real LLM execution: NOT_RUN",
        "Targets": "\n".join(f"- {item}" for item in targets) or "Not available",
        "Baseline Mutation Evidence": "- See ledger Mutation Results section.",
        "Survivor Analysis": f"- Classifications persisted: {len(classifications)}",
        "Test Hardening": f"- Patch applied: {'true' if patches and patches[-1].applied else 'false'}",
        "Focused Test Results": f"- Status: {focused[-1].status if focused else 'NOT_RUN'}",
        "Mutation Recheck": f"- Status: {rechecks[-1].status if rechecks else 'NOT_RUN'}",
        "Validation Gates": f"- Required gates passed: {validation.required_gates_passed if validation else False}",
        "Commit Plan": f"- Commit allowed: {commits[-1].commit_allowed if commits else False}",
        "Blockers": "\n".join(f"- {item.code}: {item.reason}" for item in blockers) or "None",
        "Remaining Work": "- Resolve blockers and remaining survivors shown in the ledger.",
    }
    for section in SECTIONS:
        content.extend([f"## {section}", values[section], ""])
    path.write_text("\n".join(content).rstrip() + "\n", encoding="utf-8")
    summary = FinalSummary(run_id, status, str(path), list(SECTIONS), [str(store.ledger_path)])
    store.record_final_summary(summary)
    return summary
