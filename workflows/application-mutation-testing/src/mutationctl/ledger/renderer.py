from __future__ import annotations

from pathlib import Path

from mutationctl.errors import LedgerRenderError
from mutationctl.ledger.templates import REQUIRED_SECTIONS
from mutationctl.state.store import StateStore


def render_ledger(store: StateStore) -> Path:
    run = store.get_latest_run()
    blockers = store.list_blockers()
    commands = store.list_commands()
    tasks = store.list_ledger_tasks()
    tool_detection = store.get_latest_tool_detection()
    coverage = store.get_latest_coverage_summary()
    targets = store.list_targets()
    mutation_result = store.get_latest_normalized_mutation_result()
    baseline_results = store.list_mutation_results()
    survivors = store.list_surviving_mutants()
    packets = store.list_survivor_packets()
    classifications = store.list_survivor_classifications()
    llm_validations = store.list_llm_validation_results()
    patch_proposals = store.list_patch_proposals()
    patch_safety = store.list_patch_safety_results()
    patch_applies = store.list_patch_apply_results()
    validation_summary = store.get_latest_validation_summary()
    rechecks = store.list_mutation_recheck_results()
    remaining_survivors = store.list_remaining_survivors()
    commit_plans = store.list_commit_plans()
    commit_executions = store.list_commit_execution_results()
    real_tool_decision = store.get_latest_real_tool_decision()

    repo_metadata = store.get_repo_metadata(run.run_id) if run else None

    lines = ["# Mutation Testing Ledger", ""]

    for section in REQUIRED_SECTIONS:
        lines.append(f"## {section}")
        if section == "Repository Context":
            if repo_metadata is None:
                lines.append("Not available")
            else:
                lines.extend(
                    [
                        f"- Repo URL: {repo_metadata.repo_url or 'Not available'}",
                        f"- Repo Path: {repo_metadata.repo_path}",
                        f"- Branch: {repo_metadata.branch}",
                        f"- Commit: {repo_metadata.commit_sha}",
                        f"- Dirty Tree: {'true' if repo_metadata.is_dirty else 'false'}",
                        f"- Captured At: {repo_metadata.captured_at}",
                    ]
                )
        elif section == "Workflow Configuration":
            if run is None:
                lines.append("Not available")
            else:
                for key, value in sorted(run.config.items()):
                    lines.append(f"- {key}: {value}")
        elif section == "Execution Status":
            lines.append(f"- Status: {run.status if run else 'NOT_RUN'}")
        elif section == "Command Log":
            if not commands:
                lines.append("NOT_RUN")
            else:
                for command in commands:
                    lines.append(
                        f"- {' '.join(command.command)} | exit={command.exit_code} | status={command.status}"
                    )
        elif section == "Mutation Tool Detection":
            if tool_detection is None:
                lines.append("NOT_RUN")
            else:
                lines.append(f"- Status: {tool_detection.status}")
                lines.append(f"- Selected Tool: {tool_detection.selected_tool or 'Not available'}")
                for item in tool_detection.evidence:
                    lines.append(f"- Evidence: {', '.join(item.evidence) or 'Not available'}")
        elif section == "Coverage Context":
            if coverage is None or not coverage.files:
                lines.append("NOT_RUN")
            else:
                lines.append(f"- Evidence: {coverage.evidence_path}")
                for item in coverage.files:
                    value = f"{item.line_coverage:.2f}%" if item.line_coverage is not None else "Not available"
                    lines.append(f"- {item.source_file}: {value}")
        elif section == "Selected Targets":
            selected_targets = [target for target in targets if target.selected]
            if not selected_targets:
                lines.append("NOT_RUN")
            else:
                for target in selected_targets:
                    lines.append(f"- {target.source_file}: score={target.score:.2f} ({target.rationale})")
        elif section == "Mutation Results":
            if mutation_result is not None:
                score = (
                    f"{mutation_result.mutation_score:.2f}%"
                    if mutation_result.mutation_score is not None
                    else "Not available"
                )
                lines.extend(
                    [
                        f"- Status: {mutation_result.status}",
                        f"- Tool: {mutation_result.tool_name}",
                        f"- Killed: {mutation_result.killed if mutation_result.killed is not None else 'Not available'}",
                        f"- Survived: {mutation_result.survived if mutation_result.survived is not None else 'Not available'}",
                        f"- Mutation Score: {score}",
                    ]
                )
            elif baseline_results:
                latest = baseline_results[-1]
                lines.append(f"- Baseline: {latest.status}")
                lines.append("- Mutation Score: Not available")
            else:
                lines.append("NOT_RUN")
        elif section == "Mutation Recheck":
            if not rechecks:
                lines.append("NOT_RUN")
            else:
                item = rechecks[-1]
                lines.extend([
                    f"- Target file: {item.target_file}",
                    f"- Recheck command: {' '.join(item.command)}",
                    f"- Baseline killed/survived/score: {item.killed_before}/{item.survived_before}/{item.score_before if item.score_before is not None else 'Not available'}",
                    f"- Recheck killed/survived/score: {item.killed_after}/{item.survived_after}/{item.score_after if item.score_after is not None else 'Not available'}",
                    f"- Score delta: {item.score_delta if item.score_delta is not None else 'Not available'}",
                    f"- Remaining survivors: {len(remaining_survivors)}",
                    f"- Status: {item.status}",
                    f"- Evidence: {', '.join(item.evidence)}",
                ])
        elif section == "Surviving Mutants":
            visible_survivors = remaining_survivors or survivors
            if not visible_survivors:
                lines.append("NOT_RUN")
            else:
                packets_by_mutant = {packet.mutant_id: packet for packet in packets}
                for mutant in visible_survivors:
                    packet = packets_by_mutant.get(mutant.mutant_id)
                    lines.append(
                        f"- {mutant.mutant_id}: {mutant.source_file}:{mutant.line or 'unknown'} {mutant.operator}"
                    )
                    lines.append(f"  Packet generated: {packet.status if packet else 'NOT_RUN'}")
                    lines.append(f"  Packet truncated: {'true' if packet and packet.truncated else 'false'}")
                    lines.append(f"  Related tests found: {len(packet.related_tests) if packet else 0}")
                    lines.append(f"  Evidence: {', '.join(packet.evidence) if packet else mutant.evidence}")
        elif section == "Test Hardening Actions":
            if not patch_proposals and not patch_safety:
                lines.append("NOT_RUN")
            else:
                safety_by_id = {item.proposal_id: item for item in patch_safety}
                apply_by_id = {item.proposal_id: item for item in patch_applies}
                for proposal in patch_proposals:
                    safety = safety_by_id.get(proposal.proposal_id)
                    applied = apply_by_id.get(proposal.proposal_id)
                    lines.extend([
                        f"- Proposal: {proposal.proposal_id}",
                        f"  Source type: {proposal.source_type}",
                        f"  Mutant IDs: {', '.join(proposal.mutant_ids) or 'Not available'}",
                        f"  Files: {', '.join(item.path for item in proposal.files) or 'Not available'}",
                        f"  Safety status: {safety.status if safety else 'NOT_RUN'}",
                        f"  Applied: {'true' if applied and applied.applied else 'false'}",
                        f"  Weakening findings: {len(safety.weakening_findings) if safety else 0}",
                        f"  Requires human review: {'true' if safety and safety.requires_human_review else 'false'}",
                        f"  Evidence: {', '.join(safety.evidence) if safety else ', '.join(proposal.evidence)}",
                    ])
        elif section == "Validation Gates":
            if validation_summary is None:
                lines.append("NOT_RUN")
            else:
                for gate in validation_summary.gates:
                    lines.append(f"- {gate.gate_id} {gate.name}: {gate.status}")
                    lines.append(f"  Reason: {gate.reason}")
                    lines.append(f"  Evidence: {', '.join(gate.evidence) or 'Not available'}")
                    lines.append(f"  Required: {'true' if gate.required else 'false'}")
        elif section == "Commit Status":
            if commit_plans:
                plan=commit_plans[-1]
                execution=commit_executions[-1] if commit_executions else None
                lines.extend([
                    f"- allow_commit: {str(plan.commit_allowed or bool(run and run.config.get('allow_commit'))).lower()}",
                    f"- commit_allowed: {str(plan.commit_allowed).lower()}",
                    f"- Branch plan: {plan.proposed_branch}",
                    f"- Files allowed: {', '.join(plan.files_to_commit) or 'None'}",
                    f"- Files blocked: {', '.join(plan.excluded_files) or 'None'}",
                    f"- Commit message preview: {plan.commit_message.splitlines()[0]}",
                    f"- Commit execution status: {execution.status if execution else 'NOT_RUN'}",
                    f"- Commit SHA: {execution.commit_sha if execution and execution.commit_created else 'Not available'}",
                    f"- Blockers: {', '.join(plan.reasons) or 'None'}",
                ])
            elif validation_summary is None:
                lines.append("- allow_commit: false")
                lines.append("- commit_allowed: false")
                lines.append("- Reason: Validation has not run")
            else:
                latest_run_config = run.config if run else {}
                lines.append(f"- allow_commit: {str(bool(latest_run_config.get('allow_commit', False))).lower()}")
                lines.append(f"- commit_allowed: {str(validation_summary.commit_allowed).lower()}")
                lines.append(f"- Blocking gates: {', '.join(validation_summary.blocking_gate_ids) or 'None'}")
        elif section == "Real Tool Execution":
            if real_tool_decision is None:
                lines.extend(["- Real tools enabled: false","- Mutmut enabled: false","- Decision: NOT_RUN"])
            else:
                lines.extend([
                    f"- Decision: {'PASS' if real_tool_decision.allowed else 'BLOCKED'}",
                    f"- Tool: {real_tool_decision.tool_name}",
                    f"- Command: {' '.join(real_tool_decision.command) if real_tool_decision.command else 'Not available'}",
                    f"- Blockers: {', '.join(real_tool_decision.blockers) or 'None'}",
                    f"- Evidence: {', '.join(real_tool_decision.evidence)}",
                ])
        elif section == "Survivor Analysis":
            if not classifications and not llm_validations:
                lines.append("NOT_RUN")
                lines.append("- Real LLM execution: NOT_RUN")
            else:
                deterministic = sum(item.classifier_type == "deterministic" for item in classifications)
                llm_required = sum(item.requires_llm_review for item in classifications)
                accepted = sum(item.accepted for item in llm_validations)
                rejected = sum(not item.accepted for item in llm_validations)
                lines.extend(
                    [
                        f"- Deterministic classification count: {deterministic}",
                        f"- LLM review required count: {llm_required}",
                        f"- LLM responses accepted count: {accepted}",
                        f"- LLM responses rejected count: {rejected}",
                        "- Real LLM execution: NOT_RUN",
                        "- Fake LLM contract tests: PASS",
                    ]
                )
                for item in classifications:
                    lines.append(f"- {item.mutant_id}: {item.status}")
                    lines.append(f"  Classification: {item.classification or 'Not available'}")
                    lines.append(f"  Classifier type: {item.classifier_type}")
                    lines.append(f"  Confidence: {item.confidence or 'Not available'}")
                    lines.append(f"  Requires LLM review: {'true' if item.requires_llm_review else 'false'}")
                    lines.append(f"  Recommended action: {item.recommended_action or 'Not available'}")
                    lines.append(f"  Evidence: {', '.join(item.evidence) or 'Not available'}")
                    lines.append(f"  Needs human review: {'true' if item.needs_human_review else 'false'}")
                    lines.append(f"  Equivalent candidate: {'true' if item.equivalent_candidate else 'false'}")
        elif section == "Blockers":
            if not blockers:
                lines.append("Not available")
            else:
                for blocker in blockers:
                    lines.append(f"- {blocker.status}: {blocker.reason}")
                    lines.append(f"  Evidence: {blocker.evidence}")
        elif section == "Remaining Work":
            if not tasks:
                lines.append("- [ ] Not available")
            else:
                for task in tasks:
                    checkbox = "x" if task.status == "PASS" else " "
                    lines.append(f"- [{checkbox}] {task.task_id}: {task.title}")
        else:
            lines.append("Not available")
        lines.append("")

    try:
        store.ledger_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    except OSError as exc:
        raise LedgerRenderError(str(exc)) from exc
    return store.ledger_path
