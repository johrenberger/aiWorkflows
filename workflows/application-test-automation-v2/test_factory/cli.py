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
        sub.add_argument("--allow-dirty", action="store_true")
        sub.add_argument("--mutation", action="store_true")
        sub.add_argument("--mutation-high-risk-only", action="store_true")
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
            result = orchestrator.queue(module=args.module or args.scope)
        elif args.command == "workitems":
            result = [asdict(record) for record in orchestrator.workitems(limit=args.limit, module=args.module or args.scope)]
        elif args.command == "validate":
            if not args.work_item_id:
                raise SystemExit("--work-item-id is required for validate")
            result = orchestrator.validate(args.work_item_id)
        elif args.command == "mutate":
            result = orchestrator.mutate(enabled=args.mutation, high_risk_only=args.mutation_high_risk_only or None)
        elif args.command == "report":
            result = orchestrator.report(module=args.module or args.scope)
        elif args.command == "run":
            result = orchestrator.run(
                limit=args.limit,
                mutation=args.mutation,
                mutation_high_risk_only=args.mutation_high_risk_only or None,
                module=args.module or args.scope,
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
