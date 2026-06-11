from __future__ import annotations

from pathlib import Path

from mutationctl.models import RealToolExecutionDecision, RealToolPolicy


def evaluate_real_mutmut_policy(
    policy: RealToolPolicy,
    repo_path: str | Path,
    selected_targets,
    executable_found: bool,
    dirty: bool,
    platform_supported: bool = True,
    store=None,
) -> RealToolExecutionDecision:
    root = Path(repo_path)
    reasons = []
    blockers = []
    if not policy.allow_real_tools:
        blockers.append("real tools are disabled")
    if not policy.allow_mutmut:
        blockers.append("mutmut is not explicitly enabled")
    if policy.require_existing_tool and not executable_found:
        blockers.append("mutmut executable was not found")
    if policy.require_clean_tree and dirty and not policy.allow_dirty_tree:
        blockers.append("working tree is dirty")
    if not root.is_absolute():
        blockers.append("repository path must be local and absolute")
    if not selected_targets:
        blockers.append("no bounded mutation target is selected")
    if len(selected_targets) > 5:
        blockers.append("selected target count exceeds the safety cap")
    if policy.timeout_seconds <= 0:
        blockers.append("timeout must be positive")
    if not platform_supported:
        blockers.append("mutmut requires a fork-capable environment such as WSL on Windows")
    target = selected_targets[0] if selected_targets else None
    # Mutmut 3+ accepts a positional module/function wildcard for scoped runs.
    scope = target.source_file.removesuffix(".py").replace("/", ".").replace("\\", ".") + "*" if target else ""
    command = ["mutmut", "run", scope] if target else []
    reasons.append("Dependency installation is not performed by mutationctl")
    if target:
        reasons.append(f"Scoped selected target: {target.source_file}")
    reasons.extend(blockers)
    decision = RealToolExecutionDecision(
        not blockers,
        "mutmut",
        command,
        reasons,
        blockers,
        [str(root), f"timeout={policy.timeout_seconds}", f"executable_found={executable_found}"],
    )
    if store:
        store.record_real_tool_policy(policy)
        store.record_real_tool_decision(decision)
    return decision
