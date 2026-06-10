from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .adapters.java_junit import JavaJUnitAdapter
from .adapters.js_jest_vitest import JsJestVitestAdapter
from .adapters.python_pytest import PythonPytestAdapter
from .analyzers.coverage_normalizer import (
    parse_coverage_final_json,
    parse_jacoco_xml,
    parse_lcov_info,
    parse_python_coverage_xml,
)
from .analyzers.eligibility import classify_file
from .analyzers.module_detector import detect_language_and_module
from .analyzers.mutation_analyzer import mutation_candidates_from_scores
from .analyzers.repo_inventory import inventory_repo
from .analyzers.risk_scorer import priority, score_file, weighted_index
from .analyzers.source_test_mapper import infer_existing_test_files, map_source_to_tests, supporting_files_for_source
from .analyzers.test_type_recommender import conventions_summary, recommend_test_type
from .config import load_config
from .git.branch_manager import create_branch, is_dirty
from .git.commit_manager import commit_module
from .git.pr_summary import render_pr_summary
from .models import Config, CoverageRecord, FileRecord, RiskScoreRecord, SourceTestMapRecord, WorkItemRecord
from .reports.json_report import render_json_report
from .reports.markdown_report import render_final_report
from .storage import Storage
from .validators.coverage_gate import coverage_improved
from .validators.mutation_runner import discover_mutation_candidates
from .validators.runner import find_disallowed_test_markers, run_module_validation, run_targeted_validation
from .workitems.generator import generate_work_items
from .workitems.renderer import write_work_item


def _dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _decode_json_maybe(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if stripped.startswith("[") or stripped.startswith("{") or stripped in {"null", "true", "false"}:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _language_stack(files: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in files:
        lang = item.get("language", "unknown")
        counts[lang] = counts.get(lang, 0) + 1
    return counts


def _module_graph(files: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    graph: dict[str, dict[str, int]] = {}
    for item in files:
        module = item.get("module", "root")
        lang = item.get("language", "unknown")
        bucket = graph.setdefault(module, {})
        bucket[lang] = bucket.get(lang, 0) + 1
    return graph


class TestFactoryOrchestrator:
    def __init__(self, repo_root: str | Path, out_dir: str | Path, config_path: str | Path | None = None):
        self.repo_root = Path(repo_root).resolve()
        self.out_dir = Path(out_dir).resolve()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts = self.out_dir
        self.config = load_config(self.repo_root, config_path)
        self.storage = Storage(self.artifacts / "test_factory.sqlite")
        self.adapters = [JavaJUnitAdapter(), JsJestVitestAdapter(), PythonPytestAdapter()]

    def close(self) -> None:
        self.storage.close()

    def _file_rows(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.storage.fetch_all("files")]

    def _risk_rows(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.storage.fetch_all("risk_scores")]

    def _decode_work_item_row(self, row: dict[str, Any]) -> WorkItemRecord:
        decoded = {key: _decode_json_maybe(value) for key, value in row.items()}
        return WorkItemRecord(**{key: decoded[key] for key in WorkItemRecord.__dataclass_fields__ if key in decoded})

    def _enabled_adapter(self, adapter: Any) -> bool:
        return bool(self.config.language_adapters.get(adapter.language, True))

    def adapter_for_repo(self) -> Any:
        detections = [adapter.detect(self.repo_root) for adapter in self.adapters if self._enabled_adapter(adapter)]
        detections.sort(key=lambda item: (-item.confidence, item.adapter))
        best = detections[0]
        for adapter in self.adapters:
            if adapter.language == best.language:
                return adapter, best
        return self.adapters[0], best

    def adapter_for_language(self, language: str) -> Any:
        lang = language.lower()
        if lang in {"python", "py"}:
            return next(adapter for adapter in self.adapters if adapter.language == "python" and self._enabled_adapter(adapter))
        if lang in {"java"}:
            return next(adapter for adapter in self.adapters if adapter.language == "java" and self._enabled_adapter(adapter))
        return next(adapter for adapter in self.adapters if adapter.language == "javascript" and self._enabled_adapter(adapter))

    def _discover_reports(self) -> list[Path]:
        reports: list[Path] = []
        for pattern in ("**/jacoco.xml", "**/jacocoTestReport.xml", "**/coverage.xml", "**/coverage-final.json", "**/lcov.info"):
            reports.extend(sorted(self.repo_root.glob(pattern)))
        return reports

    def _collect_coverage_records(self) -> list[CoverageRecord]:
        coverage: list[CoverageRecord] = []
        for report in self._discover_reports():
            name = report.name.lower()
            if name in {"jacoco.xml", "jacotestreport.xml"} or "jacoco" in name:
                coverage.extend(parse_jacoco_xml(report))
            elif name == "coverage.xml":
                coverage.extend(parse_python_coverage_xml(report))
            elif name == "coverage-final.json":
                coverage.extend(parse_coverage_final_json(report))
            elif name == "lcov.info":
                coverage.extend(parse_lcov_info(report))
        inventory_paths = [row["path"] for row in self._file_rows()]
        return self._merge_coverage_records(coverage, inventory_paths)

    def _normalize_coverage_path(self, coverage_path: str, inventory_paths: list[str]) -> str:
        if coverage_path in inventory_paths:
            return coverage_path
        coverage_norm = coverage_path.replace("\\", "/")
        candidates = [path for path in inventory_paths if path.endswith(coverage_norm)]
        if candidates:
            return sorted(candidates, key=len)[0]
        basename = Path(coverage_norm).name
        candidates = [path for path in inventory_paths if Path(path).name == basename]
        return sorted(candidates, key=len)[0] if candidates else coverage_path

    def _merge_coverage_records(self, records: list[CoverageRecord], inventory_paths: list[str]) -> list[CoverageRecord]:
        merged: dict[str, CoverageRecord] = {}
        for record in records:
            normalized_path = self._normalize_coverage_path(record.path, inventory_paths)
            existing = merged.get(normalized_path)
            if existing is None:
                merged[normalized_path] = CoverageRecord(
                    path=normalized_path,
                    line_coverage=record.line_coverage,
                    branch_coverage=record.branch_coverage,
                    uncovered_lines=list(record.uncovered_lines),
                    uncovered_branches=list(record.uncovered_branches),
                    report_ref=record.report_ref,
                )
                continue
            existing.line_coverage = max(existing.line_coverage, record.line_coverage)
            if existing.branch_coverage is None:
                existing.branch_coverage = record.branch_coverage
            elif record.branch_coverage is not None:
                existing.branch_coverage = max(existing.branch_coverage, record.branch_coverage)
            existing.uncovered_lines = sorted(set(existing.uncovered_lines) | set(record.uncovered_lines))
            existing.uncovered_branches = sorted(set(existing.uncovered_branches) | set(record.uncovered_branches))
            existing.report_ref = ";".join(sorted(set(filter(None, [existing.report_ref, record.report_ref]))))
        return sorted(merged.values(), key=lambda item: item.path)

    def scan(self) -> dict[str, Any]:
        files, exclusions = inventory_repo(self.repo_root, self.config)
        for record in files:
            self.storage.upsert_file(record)
        for exclusion in exclusions:
            self.storage.record_exception(exclusion["path"], exclusion["reason"], exclusion["rule"], exclusion.get("adapter", ""))
        language_stack = _language_stack([asdict(record) for record in files])
        module_graph = _module_graph([asdict(record) for record in files])
        modules = sorted({record.module for record in files})
        for module in modules:
            lang = next((record.language for record in files if record.module == module), "unknown")
            source_count = len([record for record in files if record.module == module and not record.is_test and not record.is_excluded])
            test_count = len([record for record in files if record.module == module and record.is_test])
            self.storage.upsert_module(module, lang, source_count, test_count, {"detected": True})
        _dump_json(self.artifacts / "repo_inventory.json", [asdict(record) for record in files])
        _dump_json(self.artifacts / "module_graph.json", module_graph)
        _dump_json(self.artifacts / "language_stack.json", language_stack)
        _dump_json(self.artifacts / "exclusions.json", exclusions)
        (self.artifacts / "exceptions_register.yaml").write_text(
            "\n".join(f"- path: {e['path']}\n  reason: {e['reason']}\n  rule: {e['rule']}" for e in exclusions),
            encoding="utf-8",
        )
        return {"inventory": len(files), "exclusions": len(exclusions)}

    def coverage(self) -> list[CoverageRecord]:
        coverage = self._collect_coverage_records()
        for record in coverage:
            self.storage.upsert_coverage(record)
        _dump_json(self.artifacts / "coverage_baseline.json", [asdict(record) for record in coverage])
        _dump_json(self.artifacts / "coverage_deltas" / "baseline.json", [asdict(record) for record in coverage])
        return coverage

    def score(self) -> list[RiskScoreRecord]:
        coverage_rows = {row["path"]: CoverageRecord(**{k: row[k] for k in ("path", "line_coverage", "branch_coverage", "uncovered_lines", "uncovered_branches", "report_ref")}) for row in _read_json(self.artifacts / "coverage_baseline.json", [])}
        scores: list[RiskScoreRecord] = []
        for row in self._file_rows():
            if row.get("is_excluded") or row.get("is_test"):
                continue
            cov = coverage_rows.get(row["path"])
            source_path = self.repo_root / row["path"]
            text = source_path.read_text(encoding="utf-8", errors="ignore")[: self.config.max_source_file_chars] if source_path.exists() else ""
            complexity = sum(text.count(token) for token in ("if ", "for ", "while ", "case ", "catch ", "except "))
            public_api = 1.0 if any(token in text for token in ("public ", "def ", "export ", "class ")) else 0.0
            dependency_fan_in = text.count("import ") + text.count("require(")
            sensitivity = 1.0 if any(token in row["path"].lower() for token in ("auth", "payment", "billing", "db", "security")) else 0.0
            score = score_file(
                row["path"],
                row["module"],
                cov,
                complexity=float(complexity),
                churn=0.0,
                public_api_exposure=float(public_api),
                dependency_fan_in=float(dependency_fan_in),
                defect_history=0.0,
                data_or_security_sensitivity=float(sensitivity),
                missing_evidence=["churn", "defect_history"] if cov is None else [],
                line_threshold=float(self.config.coverage_threshold_line),
                branch_threshold=float(self.config.coverage_threshold_branch),
            )
            scores.append(score)
            self.storage.upsert_risk_score(score)
        scores.sort(key=lambda item: (-priority(item), item.path))
        _dump_json(self.artifacts / "risk_scores.json", [asdict(score) for score in scores])
        _dump_json(self.artifacts / "risk_weighted_coverage.json", {
            "line_index": weighted_index(scores, use_branch=False),
            "branch_index": weighted_index(scores, use_branch=True),
        })
        return scores

    def queue(self) -> list[dict[str, Any]]:
        scores = [dict(row) for row in _read_json(self.artifacts / "risk_scores.json", [])]
        queue = []
        for item in scores:
            if item.get("coverage_gap", 0) <= 0 and item.get("risk_score", 0) <= 0:
                continue
            item["priority"] = float(item.get("risk_score", 0)) * float(item.get("coverage_gap", 0))
            queue.append(item)
        queue.sort(key=lambda item: (-item["priority"], item["path"]))
        _dump_json(self.artifacts / "test_gap_queue.json", queue)
        _dump_json(self.artifacts / "component_test_candidates.json", [item for item in queue if "component" in str(item.get("recommended_test_type", "")) or item.get("risk_score", 0) >= 50])
        return queue

    def workitems(self, limit: int | None = None) -> list[WorkItemRecord]:
        coverage_records = [CoverageRecord(**item) for item in _read_json(self.artifacts / "coverage_baseline.json", [])]
        scores = [RiskScoreRecord(**item) for item in _read_json(self.artifacts / "risk_scores.json", [])]
        source_maps: dict[str, SourceTestMapRecord] = {}
        for score in scores:
            source_file = self.repo_root / score.path
            source_text = source_file.read_text(encoding="utf-8", errors="ignore")[: self.config.max_source_file_chars] if source_file.exists() else ""
            language = source_file.suffix.lstrip(".").lower()
            adapter = self.adapter_for_language(language if language else "javascript")
            candidate_tests = infer_existing_test_files(score.path, adapter.language)
            existing_tests = [path for path in candidate_tests if (self.repo_root / path).exists()]
            supporting_files = []
            for candidate in adapter.recommend_supporting_files(source_file) + supporting_files_for_source(score.path, adapter.language):
                if candidate and (self.repo_root / candidate).exists() and candidate not in supporting_files:
                    supporting_files.append(candidate)
            source_maps[score.path] = SourceTestMapRecord(
                source_path=score.path,
                candidate_tests=existing_tests or candidate_tests,
                supporting_files=supporting_files,
                recommended_test_type=recommend_test_type(score.path, source_text),
                conventions_summary=conventions_summary(adapter.language, score.path),
            )
        items = generate_work_items(self.repo_root, self.config, coverage_records, scores, source_maps)
        if limit is not None:
            items = items[:limit]
        items_dir = self.artifacts / "ai_work_items"
        items_dir.mkdir(parents=True, exist_ok=True)
        serialized = []
        for item in items:
            item.validation_command = self._validation_command_for(item)
            item.conventions_summary = source_maps.get(item.source_path, SourceTestMapRecord(item.source_path)).conventions_summary
            item.content_path = str(items_dir / f"{item.work_item_id}.md")
            write_work_item(item, self.config)
            self.storage.upsert_work_item(item)
            serialized.append(asdict(item))
        _dump_json(items_dir / "index.json", serialized)
        _dump_json(self.artifacts / "source_test_map.json", [asdict(record) for record in source_maps.values()])
        return items

    def _validation_command_for(self, item: WorkItemRecord) -> str:
        adapter = self.adapter_for_language(item.language)
        return adapter.discover_test_command(self.repo_root, item.module).render()

    def _coverage_for_path(self, path: str) -> CoverageRecord | None:
        coverage = {record.path: record for record in self._collect_coverage_records()}
        return coverage.get(path)

    def _validation_failure_reason(self, item: WorkItemRecord, before: RiskScoreRecord, after: CoverageRecord | None, targeted_exit: int, module_exit: int) -> str:
        if targeted_exit != 0:
            return "targeted validation failed"
        if module_exit != 0:
            return "module validation failed"
        disallowed = find_disallowed_test_markers(self.repo_root, item.existing_test_files)
        if disallowed:
            return f"disallowed test markers found in {', '.join(disallowed)}"
        if after is None:
            return "coverage report missing after validation"
        improved, reason = coverage_improved(before, after.line_coverage, after.branch_coverage)
        return reason if not improved else ""

    def validate(self, work_item_id: str) -> dict[str, Any]:
        row = self.storage.get_work_item(work_item_id)
        if not row:
            raise KeyError(work_item_id)
        item = self._decode_work_item_row(dict(row))
        risk_row = next((RiskScoreRecord(**item_row) for item_row in _read_json(self.artifacts / "risk_scores.json", []) if item_row["path"] == item.source_path), None)
        if risk_row is None:
            raise RuntimeError(f"missing risk score for {item.source_path}")
        adapter = self.adapter_for_language(item.language)
        targeted_command = adapter.discover_test_command(self.repo_root, item.module)
        module_command = adapter.discover_coverage_command(self.repo_root, item.module)
        validation_dir = self.artifacts / "validation_runs"
        self.storage.update_work_item_status(work_item_id, "running")
        targeted = run_targeted_validation(self.storage, work_item_id, targeted_command, validation_dir, self.config.validation_timeouts.targeted_seconds)
        module = run_module_validation(self.storage, work_item_id, module_command, validation_dir, self.config.validation_timeouts.module_seconds)
        after = self._coverage_for_path(item.source_path)
        failure_reason = self._validation_failure_reason(item, risk_row, after, targeted.exit_code, module.exit_code)
        if failure_reason:
            self.storage.update_work_item_status(work_item_id, "failed")
        else:
            self.storage.update_work_item_status(work_item_id, "passed")
        result = {"targeted": asdict(targeted), "module": asdict(module), "status": "failed" if failure_reason else "passed"}
        if failure_reason:
            result["reason"] = failure_reason
        return result

    def mutate(self, enabled: bool | None = None, high_risk_only: bool | None = None) -> dict[str, Any]:
        mutation_enabled = self.config.mutation.enabled if enabled is None else enabled
        use_high_risk_only = self.config.mutation.high_risk_only if high_risk_only is None else high_risk_only
        scores = _read_json(self.artifacts / "risk_scores.json", [])
        candidates = discover_mutation_candidates(scores, high_risk_only=use_high_risk_only)
        mutation_dir = self.artifacts / "mutation"
        mutation_dir.mkdir(parents=True, exist_ok=True)
        _dump_json(mutation_dir / "mutation_candidates.json", candidates)
        detections: dict[str, dict[str, Any]] = {}
        commands: list[list[str]] = []
        results: list[dict[str, Any]] = []
        for language in sorted({Path(candidate["path"]).suffix.lower() for candidate in candidates}):
            normalized_language = {
                ".java": "java",
                ".js": "javascript",
                ".jsx": "javascript",
                ".ts": "javascript",
                ".tsx": "javascript",
                ".py": "python",
            }.get(language, "javascript")
            adapter = self.adapter_for_language(normalized_language)
            detection = adapter.detect_mutation_tool(self.repo_root, "")
            detections[normalized_language] = asdict(detection)
            if detection.command and detection.command not in commands:
                commands.append(detection.command)
        if mutation_enabled:
            for command in commands:
                completed = subprocess.run(command, cwd=self.repo_root, capture_output=True, text=True, timeout=self.config.mutation.timeout_seconds)
                results.append(
                    {
                        "tool": command[0],
                        "command": " ".join(command),
                        "exit_code": completed.returncode,
                        "stdout": completed.stdout,
                        "stderr": completed.stderr,
                    }
                )
        _dump_json(mutation_dir / "mutation_tool_detection.json", detections)
        _dump_json(mutation_dir / "mutation_commands.json", commands)
        _dump_json(mutation_dir / "mutation_results.json", results)
        _dump_json(
            mutation_dir / "mutation_score_summary.json",
            {"candidates": len(candidates), "tool_available": any(item.get("available") for item in detections.values()), "executed": mutation_enabled, "result_count": len(results)},
        )
        for candidate in candidates:
            self.storage.upsert_mutation_candidate(candidate["path"], candidate["module"], float(candidate["score"]), candidate)
        for index, result in enumerate(results, start=1):
            self.storage.upsert_mutation_result(
                f"mutation-run-{index}",
                "global",
                result.get("tool", ""),
                result.get("command", ""),
                int(result.get("exit_code", 0)),
                result.get("stdout", ""),
                result.get("stderr", ""),
            )
        return {"candidates": len(candidates), "tool_available": any(item.get("available") for item in detections.values()), "executed": mutation_enabled}

    def report(self) -> dict[str, str]:
        final_report = render_final_report(self.artifacts)
        json_report = render_json_report(self.artifacts)
        pr_summary = render_pr_summary(self.artifacts)
        (self.artifacts / "final_report.md").write_text(final_report, encoding="utf-8")
        (self.artifacts / "pr_summary.md").write_text(pr_summary, encoding="utf-8")
        (self.artifacts / "final_report.json").write_text(json_report, encoding="utf-8")
        return {"final_report": str(self.artifacts / "final_report.md"), "pr_summary": str(self.artifacts / "pr_summary.md")}

    def run(self, limit: int | None = None, mutation: bool | None = None, mutation_high_risk_only: bool | None = None) -> dict[str, Any]:
        self.scan()
        self.coverage()
        self.score()
        self.queue()
        self.workitems(limit=limit)
        self.mutate(enabled=mutation, high_risk_only=mutation_high_risk_only)
        self.report()
        return {"status": "ok"}

    def branch(self, module: str, allow_dirty: bool = False) -> dict[str, Any]:
        record = create_branch(self.repo_root, module, self.config.branching.branch_prefix, allow_dirty=allow_dirty or self.config.branching.allow_dirty)
        self.storage.upsert_branch_run(record.branch_name, record.module, record.created, record.dirty, record.sha)
        return asdict(record)

    def commit(self, module: str) -> dict[str, Any]:
        passed_items = [
            self._decode_work_item_row(dict(row))
            for row in self.storage.list_work_items(status="passed")
            if dict(row)["module"] == module
        ]
        if not passed_items:
            raise RuntimeError(f"no passed work items recorded for module {module}")
        record = commit_module(self.repo_root, module)
        self.storage.upsert_commit(record.module, record.message, record.sha, record.files)
        return asdict(record)

    def pr_summary(self) -> str:
        summary = render_pr_summary(self.artifacts)
        (self.artifacts / "pr_summary.md").write_text(summary, encoding="utf-8")
        return summary
