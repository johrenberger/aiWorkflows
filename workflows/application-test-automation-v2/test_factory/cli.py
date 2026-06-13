from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path

from .logging_config import configure_logging
from .orchestrator import TestFactoryOrchestrator


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
        sub.add_argument("--module", default=None)
        sub.add_argument("--scope", default=None)
        sub.add_argument("--zero-coverage-only", action="store_true",
                         help="Story 024: when set, restrict queue/workitems/run output to "
                              "files with zero test coverage (line_coverage==0.0 and "
                              "branch_coverage in (None, 0.0)). No effect on branch/commit/"
                              "coverage/score/scan.")
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
        if args.command == "scan":
            result = orchestrator.scan(module=args.module or args.scope)
        elif args.command == "coverage":
            result = [asdict(record) for record in orchestrator.coverage(module=args.module or args.scope)]
        elif args.command == "score":
            result = [asdict(record) for record in orchestrator.score(module=args.module or args.scope)]
        elif args.command == "queue":
            result = orchestrator.queue(module=args.module or args.scope, zero_coverage_only=args.zero_coverage_only)
        elif args.command == "workitems":
            result = [asdict(record) for record in orchestrator.workitems(limit=args.limit, module=args.module or args.scope, zero_coverage_only=args.zero_coverage_only)]
        elif args.command == "validate":
            if not args.work_item_id:
                raise SystemExit("--work-item-id is required for validate")
            result = orchestrator.validate(args.work_item_id)
        elif args.command == "mutate":
            result = orchestrator.mutate(enabled=args.mutation, high_risk_only=args.mutation_high_risk_only or None)
        elif args.command == "report":
            result = orchestrator.report(module=args.module or args.scope)
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
                module=args.module or args.scope,
                generate_coverage=generate_coverage,
                adapter_name=args.adapter,
                zero_coverage_only=args.zero_coverage_only,
            )
        elif args.command == "branch":
            result = orchestrator.branch(args.scope or args.module or "root", allow_dirty=args.allow_dirty)
        elif args.command == "commit":
            result = orchestrator.commit(args.module or "root", allow_dirty=args.allow_dirty)
        elif args.command == "pr-summary":
            result = orchestrator.pr_summary(module=args.module or args.scope)
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
