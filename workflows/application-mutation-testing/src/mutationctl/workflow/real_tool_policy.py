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


def evaluate_real_pit_policy(
    policy: RealToolPolicy,
    repo_path: str | Path,
    selected_targets,
    executable_found: bool,
    dirty: bool,
    store=None,
) -> RealToolExecutionDecision:
    """Safety gate for running the real PIT mutation tool against a
    Java repo. Mirrors `evaluate_real_mutmut_policy` but for PIT:
      - PIT must be explicitly enabled (`allow_pit=True`)
      - The build tool (`mvn`) must be findable when
        `require_existing_tool` is set
      - The repository must be local and absolute
      - The selection must be bounded (1-5 targets)
      - The timeout must be positive
      - The working tree must be clean (unless `allow_dirty_tree`)

    PIT runs via `mvn org.pitest:pitest-maven:mutationCoverage`, so
    platform support is OS-agnostic (no fork-capable requirement
    like mutmut). Java itself is a `mvn`-side concern; the policy
    doesn't preflight it.

    The command is scoped to the selected target via
    `-DtargetClasses=<ClassName>`. We extract the class name from
    the source file path: `src/main/java/com/foo/Bar.java` →
    `com.foo.Bar`. If the path doesn't have a `.java` extension,
    we fall back to the basename without extension.
    """
    root = Path(repo_path)
    reasons = []
    blockers = []
    if not policy.allow_real_tools:
        blockers.append("real tools are disabled")
    if not policy.allow_pit:
        blockers.append("PIT is not explicitly enabled")
    if policy.require_existing_tool and not executable_found:
        blockers.append("mvn executable was not found")
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
    target = selected_targets[0] if selected_targets else None
    command: list[str] = []
    if target:
        # Translate path → FQCN. We strip leading `src/main/java/`
        # and the trailing `.java` and convert `/` to `.`.
        src = target.source_file
        for prefix in ("src/main/java/", "src/test/java/", "src/main/kotlin/", "src/test/kotlin/"):
            if src.startswith(prefix):
                src = src[len(prefix):]
                break
        if src.endswith(".java"):
            fqcn = src[:-5].replace("/", ".")
        elif src.endswith(".kt"):
            fqcn = src[:-3].replace("/", ".")
        else:
            # Fallback: use the basename without extension
            fqcn = Path(src).stem
        # PIT's mutationCoverage goal doesn't run the test-compile
        # phase on its own — it needs the classes on disk. We chain
        # `test-compile` (NOT `test`, which would run all tests) so
        # the project is built but we don't double-execute tests.
        #
        # Maven's lifecycle runs ALL phases up to and including the
        # named goal, so `mvn test-compile` already includes
        # `process-test-resources` (which copies src/test/resources/*
        # to target/test-classes/). We do NOT chain it explicitly —
        # the user shouldn't have to.
        #
        # If the user needs a fresh test pass before mutating (e.g.
        # fixtures change between runs), they can add `test` to the
        # front of the command — this re-runs the entire test suite
        # (2-5x slowdown) so use it only when you trust the test
        # results are stale. Do NOT add `verify` — that runs
        # `integration-test` which PIT can't mutate.
        command = [
            "mvn",
            "test-compile",
            "org.pitest:pitest-maven:mutationCoverage",
            f"-DtargetClasses={fqcn}",
        ]
    reasons.append("PIT is invoked via Maven, no fork requirement")
    reasons.append("Dependency installation is not performed by mutationctl")
    reasons.append(
        "Test resources are processed by Maven's lifecycle "
        "(process-test-resources is included in test-compile); "
        "user need not chain it explicitly"
    )
    if target:
        reasons.append(f"Scoped selected target: {target.source_file}")
    reasons.extend(blockers)
    decision = RealToolExecutionDecision(
        not blockers,
        "pit",
        command,
        reasons,
        blockers,
        [str(root), f"timeout={policy.timeout_seconds}", f"executable_found={executable_found}"],
    )
    if store:
        store.record_real_tool_policy(policy)
        store.record_real_tool_decision(decision)
    return decision
