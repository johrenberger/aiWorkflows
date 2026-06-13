from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

from .logging_config import configure_logging
from .orchestrator import TestFactoryOrchestrator

# Story 023: sentinel value for --module/--scope that means
# "no module filter" (ingest the whole repo). For filter-style
# subcommands (scan, coverage, score, queue, workitems, report,
# run, pr-summary) this is equivalent to omitting --module
# entirely. For target-style subcommands (branch, commit) the
# sentinel is rejected because "auto" is not a valid module name.
MODULE_AUTO = "auto"

# Subcommands that take --module/--scope as a *filter* (None
# means "no filter"). Other subcommands take --module as a
# *target* (a concrete module name is required) and reject the
# sentinel.
_FILTER_STYLE_SUBCOMMANDS = frozenset({
    "scan", "coverage", "score", "queue", "workitems",
    "report", "run", "pr-summary",
})

_TARGET_STYLE_SUBCOMMANDS = frozenset({"branch", "commit"})


def _resolve_module_arg(value: str | None) -> str | None:
    """Map a `--module`/`--scope` value to the orchestrator's
    expected form. The MODULE_AUTO sentinel becomes None (no
    filter); other values pass through unchanged.
    """
    if value is None:
        return None
    if value == MODULE_AUTO:
        return None
    return value


def _filter_module_arg(args: argparse.Namespace) -> str | None:
    """Combine `--module` and `--scope` for filter-style
    subcommands. Either may carry the MODULE_AUTO sentinel;
    the first non-sentinel value wins (and "auto" means None).
    """
    return _resolve_module_arg(args.module) or _resolve_module_arg(args.scope)


def _reject_auto_for_target(args: argparse.Namespace) -> None:
    """For subcommands that take `--module` as a target (branch,
    commit), reject the MODULE_AUTO sentinel with a clear error.
    """
    if args.module == MODULE_AUTO or args.scope == MODULE_AUTO:
        print(
            f"error: --module {MODULE_AUTO!r} is not valid for the "
            f"{args.command!r} subcommand. Specify a concrete module name.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="test-factory")
    parser.add_argument("--config", default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("scan", "coverage", "score", "queue", "workitems", "validate", "mutate", "report", "run", "branch", "commit", "pr-summary"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--repo", required=True)
        sub.add_argument("--out", default="analysis-artifacts")
        sub.add_argument("--limit", type=int, default=None)
        sub.add_argument("--work-item-id", default=None)
        sub.add_argument("--module", default=None,
                         help=("Maven module name to filter by (or '" + MODULE_AUTO +
                               "' for no filter on filter-style subcommands). "
                               "For branch/commit, must be a concrete module name."))
        sub.add_argument("--scope", default=None,
                         help=("Alias for --module (e.g. '" + MODULE_AUTO +
                               "' for no filter). Kept for backward compat."))
        sub.add_argument("--zero-coverage-only", action="store_true",
                         help="Story 024: when set, restrict queue/workitems/run output to "
                              "files with zero test coverage (line_coverage==0.0 and "
                              "branch_coverage in (None, 0.0)). No effect on branch/commit/"
                              "coverage/score/scan.")
        sub.add_argument("--unmeasurable-only", action="store_true",
                         help="Story 031: when set, restrict queue/workitems/run output to "
                              "files whose coverage could not be measured (e.g. generated "
                              "code, aspect-oriented Java, custom JaCoCo filters). These "
                              "need a build-side fix, not new tests. No effect on "
                              "branch/commit/coverage/score/scan.")
        sub.add_argument("--allow-dirty", action="store_true")
        sub.add_argument("--mutation", action="store_true")
        sub.add_argument("--mutation-high-risk-only", action="store_true")
        # Story 020: coverage generation is now ON by default for `test-factory run`.
        # `--generate-coverage` is kept for explicit-opt-in (backward compat with
        # scripts/CI that pass it). `--no-generate-coverage` is the new opt-out.
        # The two are mutually exclusive — the `add_mutually_exclusive_group()`
        # below makes argparse reject both. Generation mutates the target repo
        # (writes coverage.json/xml) and adds 5-30 min per run, so the opt-out
        # exists for fast / read-only smoke runs.
        gen = sub.add_mutually_exclusive_group()
        gen.add_argument("--generate-coverage", action="store_true",
                         help="(run only) Force-enable coverage generation (the default "
                              "since story 020). Kept for explicit-opt-in in CI scripts. "
                              "Mutates the target repo (writes coverage.json/xml).")
        gen.add_argument("--no-generate-coverage", action="store_true",
                         help="(run only) Skip coverage generation even though it's on by "
                              "default. Use for fast / read-only smoke runs. The resulting "
                              "risk_scores.json will have line_coverage=0.0 everywhere "
                              "(see story 019 for that fall-back's downstream effect).")
        sub.add_argument("--coverage-out", default=None,
                         help="(run only, story 025) When set with --generate-coverage, "
                              "the freshly-written reports are copied to this directory. "
                              "The target repo is still mutated by the build tool, but the "
                              "user gets a clean copy under their chosen dir. Defaults to "
                              "the target repo (legacy behavior).")
        sub.add_argument("--adapter", default=None,
                         choices=("python_pytest", "java_junit", "js_jest_vitest"),
                         help="Force a specific adapter for coverage_generation. "
                              "Defaults to the adapter with the highest detect() confidence. "
                              "Useful when the target repo's primary language is ambiguous or "
                              "the auto-detector picks the wrong adapter (Bug surfaced 2026-06-11 "
                              "when running v2 against its own workspace: Python-only repo but a "
                              "stray .java test file from a prior Broadleaf run made java_junit "
                              "tie on confidence).")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    orchestrator = TestFactoryOrchestrator(args.repo, args.out, config_path=args.config)
    try:
        if args.command in _TARGET_STYLE_SUBCOMMANDS:
            _reject_auto_for_target(args)
        # Filter-style subcommands: pass the resolved (None for
        # "auto") module value to the orchestrator.
        module = _filter_module_arg(args) if args.command in _FILTER_STYLE_SUBCOMMANDS else None
        if args.command == "scan":
            result = orchestrator.scan(module=module)
        elif args.command == "coverage":
            result = [asdict(record) for record in orchestrator.coverage(module=module)]
        elif args.command == "score":
            result = [asdict(record) for record in orchestrator.score(module=module)]
        elif args.command == "queue":
            result = orchestrator.queue(
                module=module,
                zero_coverage_only=args.zero_coverage_only,
                unmeasurable_only=args.unmeasurable_only,
            )
        elif args.command == "workitems":
            result = [asdict(record) for record in orchestrator.workitems(
                limit=args.limit,
                module=module,
                zero_coverage_only=args.zero_coverage_only,
                unmeasurable_only=args.unmeasurable_only,
            )]
        elif args.command == "validate":
            if not args.work_item_id:
                raise SystemExit("--work-item-id is required for validate")
            result = orchestrator.validate(args.work_item_id)
        elif args.command == "mutate":
            result = orchestrator.mutate(enabled=args.mutation, high_risk_only=args.mutation_high_risk_only or None)
        elif args.command == "report":
            result = orchestrator.report(module=module)
        elif args.command == "run":
            # Story 020: coverage generation is ON by default. The CLI flag
            # is `--no-generate-coverage` (opt-out), not `--generate-coverage`
            # (opt-in). `--generate-coverage` is still accepted for explicit
            # opt-in (backward compat). argparse already rejected the case
            # where both are set, so we just compute the effective value:
            # generate iff not (no_generate_coverage is True).
            generate_coverage = not args.no_generate_coverage
            result = orchestrator.run(
                limit=args.limit,
                mutation=args.mutation,
                mutation_high_risk_only=args.mutation_high_risk_only or None,
                module=module,
                generate_coverage=generate_coverage,
                adapter_name=args.adapter,
                zero_coverage_only=args.zero_coverage_only,
                unmeasurable_only=args.unmeasurable_only,
                coverage_out_dir=args.coverage_out,
            )
        elif args.command == "branch":
            result = orchestrator.branch(args.scope or args.module or "root", allow_dirty=args.allow_dirty)
        elif args.command == "commit":
            result = orchestrator.commit(args.module or "root", allow_dirty=args.allow_dirty)
        elif args.command == "pr-summary":
            result = orchestrator.pr_summary(module=module)
        else:
            result = {}
        if isinstance(result, str):
            print(result)
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    finally:
        orchestrator.close()


if __name__ == "__main__":
    raise SystemExit(main())
