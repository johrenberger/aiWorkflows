from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable


SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS files (
  path TEXT PRIMARY KEY,
  language TEXT NOT NULL,
  module TEXT NOT NULL,
  size INTEGER NOT NULL,
  sha256 TEXT NOT NULL DEFAULT '',
  is_test INTEGER NOT NULL DEFAULT 0,
  is_generated INTEGER NOT NULL DEFAULT 0,
  is_excluded INTEGER NOT NULL DEFAULT 0,
  exclusion_reason TEXT NOT NULL DEFAULT '',
  evidence TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS modules (
  module TEXT PRIMARY KEY,
  language TEXT NOT NULL,
  source_count INTEGER NOT NULL DEFAULT 0,
  test_count INTEGER NOT NULL DEFAULT 0,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS coverage (
  path TEXT PRIMARY KEY,
  line_coverage REAL NOT NULL DEFAULT 0,
  branch_coverage REAL,
  uncovered_lines TEXT NOT NULL DEFAULT '[]',
  uncovered_branches TEXT NOT NULL DEFAULT '[]',
  report_ref TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS risk_scores (
  path TEXT PRIMARY KEY,
  module TEXT NOT NULL,
  line_coverage REAL NOT NULL DEFAULT 0,
  branch_coverage REAL,
  complexity REAL NOT NULL DEFAULT 0,
  churn REAL NOT NULL DEFAULT 0,
  public_api_exposure REAL NOT NULL DEFAULT 0,
  dependency_fan_in REAL NOT NULL DEFAULT 0,
  defect_history REAL NOT NULL DEFAULT 0,
  data_or_security_sensitivity REAL NOT NULL DEFAULT 0,
  coverage_gap REAL NOT NULL DEFAULT 0,
  risk_score REAL NOT NULL DEFAULT 0,
  missing_evidence TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS source_test_map (
  source_path TEXT PRIMARY KEY,
  candidate_tests TEXT NOT NULL DEFAULT '[]',
  candidate_paths TEXT NOT NULL DEFAULT '[]',
  supporting_files TEXT NOT NULL DEFAULT '[]',
  recommended_test_type TEXT NOT NULL DEFAULT 'unit',
  conventions_summary TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS work_items (
  work_item_id TEXT PRIMARY KEY,
  source_path TEXT NOT NULL,
  language TEXT NOT NULL,
  module TEXT NOT NULL,
  current_line_coverage REAL NOT NULL DEFAULT 0,
  current_branch_coverage REAL,
  uncovered_lines TEXT NOT NULL DEFAULT '[]',
  uncovered_branches TEXT NOT NULL DEFAULT '[]',
  risk_score REAL NOT NULL DEFAULT 0,
  risk_factors TEXT NOT NULL DEFAULT '{}',
  existing_test_files TEXT NOT NULL DEFAULT '[]',
  recommended_test_type TEXT NOT NULL DEFAULT 'unit',
  supporting_files TEXT NOT NULL DEFAULT '[]',
  conventions_summary TEXT NOT NULL DEFAULT '',
  validation_command TEXT NOT NULL DEFAULT '',
  acceptance_criteria TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'pending',
  priority REAL NOT NULL DEFAULT 0,
  content_path TEXT NOT NULL DEFAULT '',
  validated_files TEXT NOT NULL DEFAULT '[]',
  validation_repo_sha TEXT NOT NULL DEFAULT '',
  validation_reason TEXT NOT NULL DEFAULT '',
  validation_report_path TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS validation_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  work_item_id TEXT NOT NULL,
  command TEXT NOT NULL,
  exit_code INTEGER NOT NULL,
  stdout TEXT NOT NULL DEFAULT '',
  stderr TEXT NOT NULL DEFAULT '',
  timeout_seconds INTEGER NOT NULL DEFAULT 0,
  artifact_path TEXT NOT NULL DEFAULT '',
  phase TEXT NOT NULL DEFAULT 'targeted',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exceptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL,
  reason TEXT NOT NULL,
  rule TEXT NOT NULL,
  adapter_language TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mutation_candidates (
  path TEXT PRIMARY KEY,
  module TEXT NOT NULL,
  score REAL NOT NULL DEFAULT 0,
  evidence TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS mutation_results (
  path TEXT PRIMARY KEY,
  module TEXT NOT NULL,
  tool TEXT NOT NULL DEFAULT '',
  command TEXT NOT NULL DEFAULT '',
  exit_code INTEGER NOT NULL DEFAULT 0,
  stdout TEXT NOT NULL DEFAULT '',
  stderr TEXT NOT NULL DEFAULT '',
  score REAL NOT NULL DEFAULT 0,
  report_ref TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS branch_runs (
  branch_name TEXT PRIMARY KEY,
  module TEXT NOT NULL,
  created INTEGER NOT NULL DEFAULT 0,
  dirty INTEGER NOT NULL DEFAULT 0,
  sha TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS commits (
  module TEXT PRIMARY KEY,
  message TEXT NOT NULL,
  sha TEXT NOT NULL DEFAULT '',
  files TEXT NOT NULL DEFAULT '[]'
);
"""

WORK_ITEM_EXTRA_COLUMNS = (
    ("validated_files", "TEXT NOT NULL DEFAULT '[]'"),
    ("validation_repo_sha", "TEXT NOT NULL DEFAULT ''"),
    ("validation_reason", "TEXT NOT NULL DEFAULT ''"),
    ("validation_report_path", "TEXT NOT NULL DEFAULT ''"),
)


def _json(value: Any) -> str:
    if value is None:
        return "null"
    return json.dumps(value, sort_keys=True)


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


class Storage:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self._migrate()
        self.conn.commit()

    def _migrate(self) -> None:
        existing_columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(work_items)")}
        for column, ddl in WORK_ITEM_EXTRA_COLUMNS:
            if column not in existing_columns:
                self.conn.execute(f"ALTER TABLE work_items ADD COLUMN {column} {ddl}")
        # Migrate source_test_map (PR #27 - Bug #7 fix)
        stm_columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(source_test_map)")}
        if "candidate_paths" not in stm_columns:
            self.conn.execute("ALTER TABLE source_test_map ADD COLUMN candidate_paths TEXT NOT NULL DEFAULT '[]'")

    def close(self) -> None:
        self.conn.close()

    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        cur = self.conn.execute(sql, tuple(params))
        self.conn.commit()
        return cur

    def executemany(self, sql: str, params: Iterable[Iterable[Any]]) -> sqlite3.Cursor:
        cur = self.conn.executemany(sql, params)
        self.conn.commit()
        return cur

    def upsert_file(self, record: Any) -> None:
        data = _to_jsonable(record)
        self.execute(
            """
            INSERT INTO files(path, language, module, size, sha256, is_test, is_generated, is_excluded, exclusion_reason, evidence)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(path) DO UPDATE SET
              language=excluded.language,
              module=excluded.module,
              size=excluded.size,
              sha256=excluded.sha256,
              is_test=excluded.is_test,
              is_generated=excluded.is_generated,
              is_excluded=excluded.is_excluded,
              exclusion_reason=excluded.exclusion_reason,
              evidence=excluded.evidence
            """,
            (
                data["path"],
                data["language"],
                data["module"],
                data["size"],
                data.get("sha256", ""),
                int(bool(data.get("is_test", False))),
                int(bool(data.get("is_generated", False))),
                int(bool(data.get("is_excluded", False))),
                data.get("exclusion_reason", ""),
                _json(data.get("evidence", {})),
            ),
        )

    def upsert_module(self, module: str, language: str, source_count: int, test_count: int, metadata: dict[str, Any] | None = None) -> None:
        self.execute(
            """
            INSERT INTO modules(module, language, source_count, test_count, metadata)
            VALUES(?,?,?,?,?)
            ON CONFLICT(module) DO UPDATE SET
              language=excluded.language,
              source_count=excluded.source_count,
              test_count=excluded.test_count,
              metadata=excluded.metadata
            """,
            (module, language, source_count, test_count, _json(metadata or {})),
        )

    def upsert_coverage(self, record: Any) -> None:
        data = _to_jsonable(record)
        self.execute(
            """
            INSERT INTO coverage(path, line_coverage, branch_coverage, uncovered_lines, uncovered_branches, report_ref)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(path) DO UPDATE SET
              line_coverage=excluded.line_coverage,
              branch_coverage=excluded.branch_coverage,
              uncovered_lines=excluded.uncovered_lines,
              uncovered_branches=excluded.uncovered_branches,
              report_ref=excluded.report_ref
            """,
            (
                data["path"],
                float(data.get("line_coverage", 0)),
                data.get("branch_coverage"),
                _json(data.get("uncovered_lines", [])),
                _json(data.get("uncovered_branches", [])),
                data.get("report_ref", ""),
            ),
        )

    def upsert_risk_score(self, record: Any) -> None:
        data = _to_jsonable(record)
        self.execute(
            """
            INSERT INTO risk_scores(path, module, line_coverage, branch_coverage, complexity, churn, public_api_exposure, dependency_fan_in, defect_history, data_or_security_sensitivity, coverage_gap, risk_score, missing_evidence)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(path) DO UPDATE SET
              module=excluded.module,
              line_coverage=excluded.line_coverage,
              branch_coverage=excluded.branch_coverage,
              complexity=excluded.complexity,
              churn=excluded.churn,
              public_api_exposure=excluded.public_api_exposure,
              dependency_fan_in=excluded.dependency_fan_in,
              defect_history=excluded.defect_history,
              data_or_security_sensitivity=excluded.data_or_security_sensitivity,
              coverage_gap=excluded.coverage_gap,
              risk_score=excluded.risk_score,
              missing_evidence=excluded.missing_evidence
            """,
            (
                data["path"],
                data["module"],
                float(data.get("line_coverage", 0)),
                data.get("branch_coverage"),
                float(data.get("complexity", 0)),
                float(data.get("churn", 0)),
                float(data.get("public_api_exposure", 0)),
                float(data.get("dependency_fan_in", 0)),
                float(data.get("defect_history", 0)),
                float(data.get("data_or_security_sensitivity", 0)),
                float(data.get("coverage_gap", 0)),
                float(data.get("risk_score", 0)),
                _json(data.get("missing_evidence", [])),
            ),
        )

    def upsert_source_test_map(self, record: Any) -> None:
        data = _to_jsonable(record)
        self.execute(
            """
            INSERT INTO source_test_map(source_path, candidate_tests, candidate_paths, supporting_files, recommended_test_type, conventions_summary)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(source_path) DO UPDATE SET
              candidate_tests=excluded.candidate_tests,
              candidate_paths=excluded.candidate_paths,
              supporting_files=excluded.supporting_files,
              recommended_test_type=excluded.recommended_test_type,
              conventions_summary=excluded.conventions_summary
            """,
            (
                data["source_path"],
                _json(data.get("candidate_tests", [])),
                _json(data.get("candidate_paths", [])),
                _json(data.get("supporting_files", [])),
                data.get("recommended_test_type", "unit"),
                data.get("conventions_summary", ""),
            ),
        )

    def upsert_work_item(self, record: Any) -> None:
        data = _to_jsonable(record)
        existing = self.get_work_item(data["work_item_id"])
        status = data.get("status", "pending")
        validated_files = data.get("validated_files", [])
        validation_repo_sha = data.get("validation_repo_sha", "")
        validation_reason = data.get("validation_reason", "")
        validation_report_path = data.get("validation_report_path", "")
        if existing is not None:
            if status == "pending":
                status = existing["status"]
            if not validated_files:
                validated_files = json.loads(existing["validated_files"])
            if not validation_repo_sha:
                validation_repo_sha = existing["validation_repo_sha"]
            if not validation_reason:
                validation_reason = existing["validation_reason"]
            if not validation_report_path:
                validation_report_path = existing["validation_report_path"]
        self.execute(
            """
            INSERT INTO work_items(work_item_id, source_path, language, module, current_line_coverage, current_branch_coverage, uncovered_lines, uncovered_branches, risk_score, risk_factors, existing_test_files, recommended_test_type, supporting_files, conventions_summary, validation_command, acceptance_criteria, status, priority, content_path, validated_files, validation_repo_sha, validation_reason, validation_report_path)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(work_item_id) DO UPDATE SET
              source_path=excluded.source_path,
              language=excluded.language,
              module=excluded.module,
              current_line_coverage=excluded.current_line_coverage,
              current_branch_coverage=excluded.current_branch_coverage,
              uncovered_lines=excluded.uncovered_lines,
              uncovered_branches=excluded.uncovered_branches,
              risk_score=excluded.risk_score,
              risk_factors=excluded.risk_factors,
              existing_test_files=excluded.existing_test_files,
              recommended_test_type=excluded.recommended_test_type,
              supporting_files=excluded.supporting_files,
              conventions_summary=excluded.conventions_summary,
              validation_command=excluded.validation_command,
              acceptance_criteria=excluded.acceptance_criteria,
              status=excluded.status,
              priority=excluded.priority,
              content_path=excluded.content_path,
              validated_files=excluded.validated_files,
              validation_repo_sha=excluded.validation_repo_sha,
              validation_reason=excluded.validation_reason,
              validation_report_path=excluded.validation_report_path
            """,
            (
                data["work_item_id"],
                data["source_path"],
                data["language"],
                data["module"],
                float(data.get("current_line_coverage", 0)),
                data.get("current_branch_coverage"),
                _json(data.get("uncovered_lines", [])),
                _json(data.get("uncovered_branches", [])),
                float(data.get("risk_score", 0)),
                _json(data.get("risk_factors", {})),
                _json(data.get("existing_test_files", [])),
                data.get("recommended_test_type", "unit"),
                _json(data.get("supporting_files", [])),
                data.get("conventions_summary", ""),
                data.get("validation_command", ""),
                _json(data.get("acceptance_criteria", [])),
                status,
                float(data.get("priority", 0)),
                data.get("content_path", ""),
                _json(validated_files),
                validation_repo_sha,
                validation_reason,
                validation_report_path,
            ),
        )

    def list_work_items(self, status: str | None = None) -> list[sqlite3.Row]:
        if status:
            cur = self.conn.execute("SELECT * FROM work_items WHERE status=? ORDER BY priority DESC, work_item_id ASC", (status,))
        else:
            cur = self.conn.execute("SELECT * FROM work_items ORDER BY priority DESC, work_item_id ASC")
        return list(cur.fetchall())

    def update_work_item_status(self, work_item_id: str, status: str) -> None:
        self.execute("UPDATE work_items SET status=? WHERE work_item_id=?", (status, work_item_id))

    def update_work_item_validation(
        self,
        work_item_id: str,
        *,
        status: str,
        validated_files: list[str] | None = None,
        validation_repo_sha: str = "",
        validation_reason: str = "",
        validation_report_path: str = "",
    ) -> None:
        row = self.get_work_item(work_item_id)
        if row is None:
            return
        self.execute(
            """
            UPDATE work_items
            SET status=?,
                validated_files=?,
                validation_repo_sha=?,
                validation_reason=?,
                validation_report_path=?
            WHERE work_item_id=?
            """,
            (
                status,
                _json(validated_files if validated_files is not None else json.loads(row["validated_files"])),
                validation_repo_sha or row["validation_repo_sha"],
                validation_reason,
                validation_report_path or row["validation_report_path"],
                work_item_id,
            ),
        )

    def get_work_item(self, work_item_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM work_items WHERE work_item_id=?", (work_item_id,)).fetchone()

    def latest_validation_run(self, work_item_id: str, phase: str | None = None) -> sqlite3.Row | None:
        if phase:
            return self.conn.execute(
                "SELECT * FROM validation_runs WHERE work_item_id=? AND phase=? ORDER BY id DESC LIMIT 1",
                (work_item_id, phase),
            ).fetchone()
        return self.conn.execute(
            "SELECT * FROM validation_runs WHERE work_item_id=? ORDER BY id DESC LIMIT 1",
            (work_item_id,),
        ).fetchone()

    def insert_validation_run(self, record: Any) -> None:
        data = _to_jsonable(record)
        self.execute(
            """
            INSERT INTO validation_runs(work_item_id, command, exit_code, stdout, stderr, timeout_seconds, artifact_path, phase)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                data["work_item_id"],
                data["command"],
                int(data["exit_code"]),
                data.get("stdout", ""),
                data.get("stderr", ""),
                int(data.get("timeout_seconds", 0)),
                data.get("artifact_path", ""),
                data.get("phase", "targeted"),
            ),
        )

    def record_exception(self, path: str, reason: str, rule: str, adapter_language: str = "") -> None:
        self.execute(
            "INSERT INTO exceptions(path, reason, rule, adapter_language) VALUES(?,?,?,?)",
            (path, reason, rule, adapter_language),
        )

    def upsert_mutation_candidate(self, path: str, module: str, score: float, evidence: dict[str, Any] | None = None) -> None:
        self.execute(
            """
            INSERT INTO mutation_candidates(path, module, score, evidence)
            VALUES(?,?,?,?)
            ON CONFLICT(path) DO UPDATE SET
              module=excluded.module,
              score=excluded.score,
              evidence=excluded.evidence
            """,
            (path, module, float(score), _json(evidence or {})),
        )

    def upsert_mutation_result(self, path: str, module: str, tool: str, command: str, exit_code: int, stdout: str, stderr: str, score: float = 0.0, report_ref: str = "") -> None:
        self.execute(
            """
            INSERT INTO mutation_results(path, module, tool, command, exit_code, stdout, stderr, score, report_ref)
            VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(path) DO UPDATE SET
              module=excluded.module,
              tool=excluded.tool,
              command=excluded.command,
              exit_code=excluded.exit_code,
              stdout=excluded.stdout,
              stderr=excluded.stderr,
              score=excluded.score,
              report_ref=excluded.report_ref
            """,
            (path, module, tool, command, exit_code, stdout, stderr, score, report_ref),
        )

    def upsert_branch_run(self, branch_name: str, module: str, created: bool, dirty: bool, sha: str = "") -> None:
        self.execute(
            """
            INSERT INTO branch_runs(branch_name, module, created, dirty, sha)
            VALUES(?,?,?,?,?)
            ON CONFLICT(branch_name) DO UPDATE SET
              module=excluded.module,
              created=excluded.created,
              dirty=excluded.dirty,
              sha=excluded.sha
            """,
            (branch_name, module, int(created), int(dirty), sha),
        )

    def upsert_commit(self, module: str, message: str, sha: str = "", files: list[str] | None = None) -> None:
        self.execute(
            """
            INSERT INTO commits(module, message, sha, files)
            VALUES(?,?,?,?)
            ON CONFLICT(module) DO UPDATE SET
              message=excluded.message,
              sha=excluded.sha,
              files=excluded.files
            """,
            (module, message, sha, _json(files or [])),
        )

    def fetch_all(self, table: str) -> list[sqlite3.Row]:
        return list(self.conn.execute(f"SELECT * FROM {table}"))
