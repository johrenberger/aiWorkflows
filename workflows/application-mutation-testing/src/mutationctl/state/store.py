from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from mutationctl.config import config_to_dict
from mutationctl.errors import StateError
from mutationctl.models import (
    Blocker,
    CommandResult,
    CoverageFileSummary,
    CoverageSummary,
    LedgerTask,
    MutationRunResult,
    MutationTarget,
    MutationToolEvidence,
    MutationRecheckPlan,
    MutationRecheckResult,
    PatchApplyResult,
    PatchFileChange,
    PatchProposal,
    PatchRevertResult,
    PatchSafetyResult,
    FocusedTestResult,
    TestWeakeningFinding,
    ValidationGateResult,
    ValidationSummary,
    BranchPlan,
    ChangedFile,
    CommitExecutionResult,
    CommitGateResult,
    CommitPlan,
    FinalSummary,
    GitStatus,
    RealToolExecutionDecision,
    RealToolPolicy,
    WorkflowRunResult,
    LLMClassificationResponse,
    LLMValidationResult,
    NormalizedMutant,
    NormalizedMutationResult,
    RelatedTestReference,
    RepoMetadata,
    RunRecord,
    SourceContext,
    SurvivorClassification,
    SurvivorPacket,
    ToolDetectionResult,
    WorkflowConfig,
)
from mutationctl.state.migrations import apply_migrations


class StateStore:
    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace)
        self.state_dir = self.workspace / ".mutation-workflow"
        self.db_path = self.state_dir / "state.sqlite"
        self.run_json_path = self.state_dir / "run.json"
        self.commands_jsonl_path = self.state_dir / "commands.jsonl"
        self.ledger_path = self.state_dir / "TODO_mutation-testing.md"

    def initialize(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        for directory_name in ["reports", "survivor-packets", "llm-decisions", "patches"]:
            (self.state_dir / directory_name).mkdir(exist_ok=True)

        if not self.run_json_path.exists():
            self.run_json_path.write_text("{}\n", encoding="utf-8")
        if not self.commands_jsonl_path.exists():
            self.commands_jsonl_path.write_text("", encoding="utf-8")
        if not self.ledger_path.exists():
            self.ledger_path.write_text("# Mutation Testing Ledger\n", encoding="utf-8")

        with sqlite3.connect(self.db_path) as connection:
            apply_migrations(connection)

    def create_run(self, config: WorkflowConfig, repo_metadata: RepoMetadata) -> RunRecord:
        self._ensure_initialized()
        record = RunRecord(
            run_id=f"run-{uuid4().hex[:12]}",
            repo_url=config.repo_url,
            repo_path=config.repo_path,
            branch=repo_metadata.branch,
            mode=config.mode,
            status="NOT_RUN",
            created_at=datetime.now(UTC).isoformat(),
            config=config_to_dict(config),
        )

        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO runs (run_id, repo_url, repo_path, branch, mode, status, created_at, config_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.run_id,
                    record.repo_url,
                    record.repo_path,
                    record.branch,
                    record.mode,
                    record.status,
                    record.created_at,
                    json.dumps(record.config, sort_keys=True),
                ),
            )
            connection.execute(
                """
                INSERT OR REPLACE INTO repo_metadata
                (run_id, repo_url, repo_path, branch, commit_sha, is_dirty, captured_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.run_id,
                    repo_metadata.repo_url,
                    repo_metadata.repo_path,
                    repo_metadata.branch,
                    repo_metadata.commit_sha,
                    int(repo_metadata.is_dirty),
                    repo_metadata.captured_at,
                ),
            )
            connection.commit()

        self.run_json_path.write_text(
            json.dumps(
                {
                    "run_id": record.run_id,
                    "repo_url": record.repo_url,
                    "repo_path": record.repo_path,
                    "branch": record.branch,
                    "status": record.status,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return record

    def get_run(self, run_id: str) -> RunRecord | None:
        self._ensure_initialized()
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT run_id, repo_url, repo_path, branch, mode, status, created_at, config_json
                FROM runs WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return RunRecord(
            run_id=row[0],
            repo_url=row[1],
            repo_path=row[2],
            branch=row[3],
            mode=row[4],
            status=row[5],
            created_at=row[6],
            config=json.loads(row[7]),
        )

    def get_latest_run(self) -> RunRecord | None:
        self._ensure_initialized()
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT run_id, repo_url, repo_path, branch, mode, status, created_at, config_json
                FROM runs ORDER BY created_at DESC LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return RunRecord(
            run_id=row[0],
            repo_url=row[1],
            repo_path=row[2],
            branch=row[3],
            mode=row[4],
            status=row[5],
            created_at=row[6],
            config=json.loads(row[7]),
        )

    def get_repo_metadata(self, run_id: str) -> RepoMetadata | None:
        self._ensure_initialized()
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT repo_path, repo_url, branch, commit_sha, is_dirty, captured_at
                FROM repo_metadata WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return RepoMetadata(
            repo_path=row[0],
            repo_url=row[1],
            branch=row[2],
            commit_sha=row[3],
            is_dirty=bool(row[4]),
            captured_at=row[5],
        )

    def record_command(self, result: CommandResult) -> None:
        self._ensure_initialized()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO commands
                (command_json, exit_code, duration_seconds, status, stdout_path, stderr_path, timed_out)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    json.dumps(result.command),
                    result.exit_code,
                    result.duration_seconds,
                    result.status,
                    result.stdout_path,
                    result.stderr_path,
                    int(result.timed_out),
                ),
            )
            connection.commit()
        with self.commands_jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(result), sort_keys=True) + "\n")

    def list_commands(self) -> list[CommandResult]:
        self._ensure_initialized()
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT command_json, exit_code, duration_seconds, status, stdout_path, stderr_path, timed_out
                FROM commands ORDER BY id ASC
                """
            ).fetchall()
        return [
            CommandResult(
                command=json.loads(row[0]),
                exit_code=row[1],
                duration_seconds=row[2],
                status=row[3],
                stdout_path=row[4],
                stderr_path=row[5],
                timed_out=bool(row[6]),
            )
            for row in rows
        ]

    def record_blocker(self, blocker: Blocker) -> None:
        self._ensure_initialized()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO blockers (code, status, reason, evidence)
                VALUES (?, ?, ?, ?)
                """,
                (blocker.code, blocker.status, blocker.reason, blocker.evidence),
            )
            connection.commit()

    def list_blockers(self) -> list[Blocker]:
        self._ensure_initialized()
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                "SELECT code, status, reason, evidence FROM blockers ORDER BY id ASC"
            ).fetchall()
        return [Blocker(code=row[0], status=row[1], reason=row[2], evidence=row[3]) for row in rows]

    def upsert_ledger_task(self, task: LedgerTask) -> None:
        self._ensure_initialized()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO ledger_tasks (task_id, title, status, details)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    title = excluded.title,
                    status = excluded.status,
                    details = excluded.details
                """,
                (task.task_id, task.title, task.status, task.details),
            )
            connection.commit()

    def list_ledger_tasks(self) -> list[LedgerTask]:
        self._ensure_initialized()
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                "SELECT task_id, title, status, details FROM ledger_tasks ORDER BY task_id ASC"
            ).fetchall()
        return [LedgerTask(task_id=row[0], title=row[1], status=row[2], details=row[3]) for row in rows]

    def record_tool_detection(self, result: ToolDetectionResult) -> None:
        self._insert_payload("tool_detection", {"kind": "tool_detection", **asdict(result)})

    def get_latest_tool_detection(self) -> ToolDetectionResult | None:
        payload = self._latest_payload("tool_detection")
        if payload is None:
            return None
        return ToolDetectionResult(
            payload["selected_tool"],
            payload["ecosystem"],
            payload["status"],
            [MutationToolEvidence(**item) for item in payload["evidence"]],
        )

    def record_coverage_summary(self, summary: CoverageSummary) -> None:
        self._insert_payload("coverage_summaries", {"kind": "coverage", **asdict(summary)})

    def get_latest_coverage_summary(self) -> CoverageSummary | None:
        payload = self._latest_payload("coverage_summaries")
        if payload is None:
            return None
        return CoverageSummary(
            payload["source_file"],
            payload["line_coverage"],
            payload["branch_coverage"],
            payload["covered_lines"],
            payload["uncovered_lines"],
            payload["evidence_path"],
            payload["status"],
            [CoverageFileSummary(**item) for item in payload["files"]],
        )

    def record_targets(self, targets: list[MutationTarget]) -> None:
        for target in targets:
            self._insert_payload("targets", {"kind": "target", **asdict(target)})

    def list_targets(self) -> list[MutationTarget]:
        return [MutationTarget(**payload) for payload in self._list_payloads("targets", strip_kind=True)]

    def record_mutation_run(self, result: MutationRunResult) -> None:
        self._insert_payload("mutation_results", {"kind": "baseline", **asdict(result)})

    def list_mutation_results(self) -> list[MutationRunResult]:
        payloads = [
            payload for payload in self._list_payloads("mutation_results") if payload.get("kind") == "baseline"
        ]
        return [MutationRunResult(**{key: value for key, value in payload.items() if key != "kind"}) for payload in payloads]

    def record_normalized_mutation_result(self, result: NormalizedMutationResult) -> None:
        payload = asdict(result)
        payload["mutants"] = []
        self._insert_payload("mutation_results", {"kind": "normalized", **payload})
        for mutant in result.mutants:
            if mutant.status == "SURVIVED":
                self._insert_payload("surviving_mutants", {"kind": "survivor", **asdict(mutant)})

    def get_latest_normalized_mutation_result(self) -> NormalizedMutationResult | None:
        payloads = [
            payload for payload in self._list_payloads("mutation_results") if payload.get("kind") == "normalized"
        ]
        if not payloads:
            return None
        payload = payloads[-1]
        return NormalizedMutationResult(
            payload["tool_name"],
            payload["status"],
            payload["killed"],
            payload["survived"],
            payload["timeout"],
            payload["ignored"],
            payload["mutation_score"],
            payload["evidence_path"],
            [],
        )

    def list_surviving_mutants(self) -> list[NormalizedMutant]:
        return [
            NormalizedMutant(**payload)
            for payload in self._list_payloads("surviving_mutants", strip_kind=True)
        ]

    def record_surviving_mutant(self, mutant: NormalizedMutant) -> None:
        self._insert_payload("surviving_mutants", {"kind": "survivor", **asdict(mutant)})

    def record_survivor_packet(self, packet: SurvivorPacket) -> None:
        self._insert_payload("survivor_packets", {"kind": "packet", **asdict(packet)})
        artifact = self.state_dir / "survivor-packets" / f"{packet.packet_id}.json"
        artifact.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def list_survivor_packets(self) -> list[SurvivorPacket]:
        packets = []
        for payload in self._list_payloads("survivor_packets", strip_kind=True):
            payload["source_context"] = SourceContext(**payload["source_context"])
            payload["related_tests"] = [
                RelatedTestReference(**item) for item in payload["related_tests"]
            ]
            packets.append(SurvivorPacket(**payload))
        return packets

    def record_survivor_classification(self, classification: SurvivorClassification) -> None:
        self._insert_payload(
            "survivor_classifications",
            {"kind": "classification", **asdict(classification)},
        )

    def list_survivor_classifications(self) -> list[SurvivorClassification]:
        return [
            SurvivorClassification(**payload)
            for payload in self._list_payloads("survivor_classifications", strip_kind=True)
        ]

    def record_llm_request(self, request) -> None:
        self._insert_payload("llm_requests", {"kind": "request", **asdict(request)})

    def list_llm_requests(self) -> list[dict]:
        return self._list_payloads("llm_requests", strip_kind=True)

    def record_llm_response(self, response: dict, accepted: bool) -> None:
        self._insert_payload(
            "llm_responses",
            {"kind": "response", "accepted": accepted, "response": response},
        )

    def list_llm_responses(self) -> list[dict]:
        return self._list_payloads("llm_responses", strip_kind=True)

    def record_llm_validation_result(self, result: LLMValidationResult) -> None:
        self._insert_payload(
            "llm_validation_results",
            {"kind": "validation", **asdict(result)},
        )

    def list_llm_validation_results(self) -> list[LLMValidationResult]:
        results = []
        for payload in self._list_payloads("llm_validation_results", strip_kind=True):
            if payload.get("response") is not None:
                payload["response"] = LLMClassificationResponse(**payload["response"])
            results.append(LLMValidationResult(**payload))
        return results

    def record_patch_proposal(self, item: PatchProposal) -> None:
        self._insert_payload("patch_proposals", {"kind": "proposal", **asdict(item)})

    def list_patch_proposals(self) -> list[PatchProposal]:
        values = []
        for payload in self._list_payloads("patch_proposals", strip_kind=True):
            payload["files"] = [PatchFileChange(**item) for item in payload["files"]]
            values.append(PatchProposal(**payload))
        return values

    def record_patch_safety_result(self, item: PatchSafetyResult) -> None:
        self._insert_payload("patch_safety_results", {"kind": "safety", **asdict(item)})
        for finding in item.weakening_findings:
            self._insert_payload("weakening_findings", {"kind": "weakening", **asdict(finding)})

    def list_patch_safety_results(self) -> list[PatchSafetyResult]:
        values = []
        for payload in self._list_payloads("patch_safety_results", strip_kind=True):
            payload["weakening_findings"] = [TestWeakeningFinding(**item) for item in payload["weakening_findings"]]
            values.append(PatchSafetyResult(**payload))
        return values

    def record_patch_apply_result(self, item: PatchApplyResult) -> None:
        self._insert_payload("patch_apply_results", {"kind": "apply", **asdict(item)})

    def list_patch_apply_results(self) -> list[PatchApplyResult]:
        return [PatchApplyResult(**item) for item in self._list_payloads("patch_apply_results", strip_kind=True)]

    def record_patch_revert_result(self, item: PatchRevertResult) -> None:
        self._insert_payload("patch_revert_results", {"kind": "revert", **asdict(item)})

    def record_focused_test_result(self, item: FocusedTestResult) -> None:
        self._insert_payload("focused_test_results", {"kind": "focused", **asdict(item)})

    def list_focused_test_results(self) -> list[FocusedTestResult]:
        return [FocusedTestResult(**item) for item in self._list_payloads("focused_test_results", strip_kind=True)]

    def record_validation_summary(self, summary: ValidationSummary) -> None:
        for gate in summary.gates:
            self._insert_payload("validation_gate_results", {"kind": "gate", **asdict(gate)})
        self._insert_payload("validation_summaries", {"kind": "summary", **asdict(summary)})

    def get_latest_validation_summary(self) -> ValidationSummary | None:
        payload = self._latest_payload("validation_summaries")
        if not payload:
            return None
        payload.pop("kind", None)
        payload["gates"] = [ValidationGateResult(**item) for item in payload["gates"]]
        return ValidationSummary(**payload)

    def record_recheck_baseline(self, baseline: dict) -> None:
        self._insert_payload("mutation_results", {"kind": "recheck_baseline", **baseline})

    def get_recheck_baseline(self) -> dict | None:
        items = [item for item in self._list_payloads("mutation_results") if item.get("kind") == "recheck_baseline"]
        if not items:
            return None
        value = dict(items[-1]); value.pop("kind", None)
        return value

    def record_mutation_recheck_plan(self, item: MutationRecheckPlan) -> None:
        self._insert_payload("mutation_recheck_plans", {"kind": "plan", **asdict(item)})

    def record_mutation_recheck_result(self, item: MutationRecheckResult) -> None:
        payload = asdict(item); payload["remaining_survivors"] = []
        self._insert_payload("mutation_recheck_results", {"kind": "recheck", **payload})
        for survivor in item.remaining_survivors:
            self._insert_payload("remaining_survivors", {"kind": "remaining", **asdict(survivor)})

    def list_mutation_recheck_results(self) -> list[MutationRecheckResult]:
        values = []
        for payload in self._list_payloads("mutation_recheck_results", strip_kind=True):
            payload["remaining_survivors"] = []
            values.append(MutationRecheckResult(**payload))
        return values

    def list_remaining_survivors(self) -> list[NormalizedMutant]:
        return [NormalizedMutant(**item) for item in self._list_payloads("remaining_survivors", strip_kind=True)]

    def record_git_status(self, item: GitStatus) -> None:
        self._insert_payload("git_status", {"kind":"git_status", **asdict(item)})

    def get_latest_git_status(self) -> GitStatus | None:
        payload=self._latest_payload("git_status")
        if not payload: return None
        payload.pop("kind",None); payload["changed_files"]=[ChangedFile(**item) for item in payload["changed_files"]]
        return GitStatus(**payload)

    def record_branch_plan(self, item: BranchPlan) -> None:
        self._insert_payload("branch_plans", {"kind":"branch", **asdict(item)})

    def record_commit_plan(self, item: CommitPlan) -> None:
        self._insert_payload("commit_plans", {"kind":"commit_plan", **asdict(item)})

    def list_commit_plans(self) -> list[CommitPlan]:
        return [CommitPlan(**item) for item in self._list_payloads("commit_plans",strip_kind=True)]

    def get_latest_commit_plan(self) -> CommitPlan | None:
        items=self.list_commit_plans()
        return items[-1] if items else None

    def record_commit_gate_result(self, item: CommitGateResult) -> None:
        self._insert_payload("commit_gate_results", {"kind":"commit_gate", **asdict(item)})

    def record_commit_execution_result(self, item: CommitExecutionResult) -> None:
        self._insert_payload("commit_execution_results", {"kind":"commit_execution", **asdict(item)})

    def list_commit_execution_results(self) -> list[CommitExecutionResult]:
        return [CommitExecutionResult(**item) for item in self._list_payloads("commit_execution_results",strip_kind=True)]

    def record_workflow_run_result(self, item: WorkflowRunResult) -> None:
        payload=asdict(item); payload["validation_summary"]={}; payload["commit_plan"]={}
        self._insert_payload("workflow_run_results", {"kind":"workflow_run", **payload})

    def record_final_summary(self, item: FinalSummary) -> None:
        self._insert_payload("final_summaries", {"kind":"final_summary", **asdict(item)})

    def record_real_tool_policy(self, item: RealToolPolicy) -> None:
        self._insert_payload("real_tool_policies", {"kind":"real_policy", **asdict(item)})

    def record_real_tool_decision(self, item: RealToolExecutionDecision) -> None:
        self._insert_payload("real_tool_decisions", {"kind":"real_decision", **asdict(item)})

    def record_real_tool_result(self, item: CommandResult) -> None:
        self._insert_payload("real_tool_results", {"kind":"real_result", **asdict(item)})

    def get_latest_real_tool_decision(self) -> RealToolExecutionDecision | None:
        payload=self._latest_payload("real_tool_decisions")
        if not payload: return None
        payload.pop("kind",None); return RealToolExecutionDecision(**payload)

    def seed_complete_validation_evidence(self) -> None:
        from mutationctl.models import (
            FocusedTestResult, MutationRunResult, MutationTarget, MutationToolEvidence,
            RepoMetadata, SurvivorClassification, ToolDetectionResult, WorkflowConfig,
        )
        config = WorkflowConfig(repo_path=str(self.workspace))
        metadata = RepoMetadata(str(self.workspace), None, "main", "abc1234", False, datetime.now(UTC).isoformat())
        self.create_run(config, metadata)
        self.record_tool_detection(ToolDetectionResult("mutmut", "python", "PASS", [MutationToolEvidence("mutmut","python",True,False,None,["pyproject.toml"],["pyproject.toml"])]))
        self.record_targets([MutationTarget("src/sample.py","python",80,"PASS","selected",80,50,100,True)])
        self.record_mutation_run(MutationRunResult("mutmut","src/sample.py",["mutmut","run"],0,"PASS",1,None,None,[]))
        self.record_survivor_classification(SurvivorClassification("c1","m1","src/sample.py",2,"conditional_boundary","Missing edge case","high",["fixture"],"Add boundary test",False,False,"deterministic"))
        self.record_patch_safety_result(PatchSafetyResult("p1","PASS",True,[],[],[],False,["tests/test_sample.py"]))
        self.record_patch_apply_result(PatchApplyResult("p1","PASS",True,["tests/test_sample.py"],None,["tests/test_sample.py"],{}))
        self.record_focused_test_result(FocusedTestResult(["pytest"],0,"PASS",1,None,None,["pytest passed"]))
        self.record_mutation_recheck_result(MutationRecheckResult("src/sample.py","b1","r1",["mutmut"],"PASS",3,2,60,4,1,80,20,[],["fixture"]))

    def _insert_payload(self, table: str, payload: dict) -> None:
        self._ensure_initialized()
        allowed_tables = {
            "tool_detection",
            "coverage_summaries",
            "targets",
            "mutation_results",
            "surviving_mutants",
            "survivor_packets",
            "survivor_classifications",
            "llm_requests",
            "llm_responses",
            "llm_validation_results",
            "patch_proposals", "patch_safety_results", "patch_apply_results", "patch_revert_results",
            "weakening_findings", "focused_test_results", "validation_gate_results", "validation_summaries",
            "mutation_recheck_plans", "mutation_recheck_results", "remaining_survivors",
            "git_status", "branch_plans", "commit_plans", "commit_gate_results",
            "commit_execution_results", "workflow_run_results", "final_summaries",
            "real_tool_policies", "real_tool_decisions", "real_tool_results",
        }
        if table not in allowed_tables:
            raise StateError(f"Unsupported payload table: {table}")
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                f"INSERT INTO {table} (payload_json) VALUES (?)",
                (json.dumps(payload, sort_keys=True),),
            )
            connection.commit()

    def _list_payloads(self, table: str, strip_kind: bool = False) -> list[dict]:
        self._ensure_initialized()
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(f"SELECT payload_json FROM {table} ORDER BY id ASC").fetchall()
        payloads = [json.loads(row[0]) for row in rows]
        if strip_kind:
            for payload in payloads:
                payload.pop("kind", None)
        return payloads

    def _latest_payload(self, table: str) -> dict | None:
        payloads = self._list_payloads(table)
        return payloads[-1] if payloads else None

    def _ensure_initialized(self) -> None:
        if not self.db_path.exists():
            raise StateError(f"State store is not initialized at {self.state_dir}")
