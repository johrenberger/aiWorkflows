from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .adapters.java_junit import JavaJUnitAdapter
from .adapters.js_jest_vitest import JsJestVitestAdapter
from .adapters.python_pytest import PythonPytestAdapter
from .analyzers.coverage_normalizer import (
    parse_coverage_final_json,
    parse_coverage_py_json,
    parse_jacoco_xml,
    parse_lcov_info,
    parse_python_coverage_xml,
)
from .analyzers.repo_inventory import inventory_repo
from .analyzers.risk_scorer import is_zero_coverage, priority, score_file, weighted_index
from .analyzers.source_test_mapper import infer_existing_test_files, supporting_files_for_source
from .analyzers.test_type_recommender import conventions_summary, recommend_test_type
from .config import load_config
from .git.branch_manager import create_branch
from .git.commit_manager import changed_files, commit_module, git_head_sha
from .git.pr_summary import render_pr_summary
from .models import CoverageRecord, RiskScoreRecord, SourceTestMapRecord, ValidationRunRecord, WorkItemRecord
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


def _top_level_module(path: str, language: str) -> str:
    """Derive a coarse-grained module key from a file path for the
    module_graph output. For Java/Groovy, this is the Maven module that
    owns the file (the path segment before /src/{main,test}/{java,groovy}/);
    for JavaScript it is the first two path segments; for Python, the
    directory above the file. This keeps the module_graph useful for
    navigation (Bug #33) without changing the granular per-file `module`
    field used in work-items and risk scores.
    """
    rel = (path or "").replace("\\", "/").lstrip("/")
    parts = rel.split("/")
    if not parts or parts == [""]:
        return "root"
    if language in {"java", "groovy"}:
        # Look for the first /src/{main,test}/{java,groovy}/ anchor and
        # collapse everything before it. If there is nothing before
        # `src` (single-module layout), default to "src" so the graph
        # has a single bucket instead of an empty "root".
        for i, segment in enumerate(parts):
            if segment == "src" and i + 2 < len(parts) and parts[i + 1] in {"main", "test"} and parts[i + 2] in {"java", "groovy"}:
                return "/".join(parts[:i]) or "src"
        return parts[0]
    if language == "javascript":
        # If the path is rooted at a /src/main/resources/ anchor, take the
        # path segment(s) before it as the Maven module (matches the
        # Java/Groovy layout). Otherwise fall back to the first two
        # path segments.
        for i, segment in enumerate(parts):
            if segment == "src" and i + 1 < len(parts) and parts[i + 1] in {"main", "test"}:
                return "/".join(parts[:i]) or "src"
        if len(parts) >= 2:
            return "/".join(parts[:2])
        return "root"
    if language == "python":
        return parts[0] if parts else "root"
    return parts[0] if parts else "root"


def _adapter_class_name(adapter_name: str) -> str:
    """Map a CLI-friendly adapter name (e.g. ``python_pytest``) to the
    adapter class name (e.g. ``PythonPytestAdapter``). Used by
    ``_primary_adapter(adapter_name=...)`` to resolve the user's explicit
    adapter choice.
    """
    parts = adapter_name.split("_")
    return "".join(p.capitalize() for p in parts) + "Adapter"


def _module_graph(files: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    graph: dict[str, dict[str, int]] = {}
    for item in files:
        # Skip excluded files so analyzer-output/app-dev-discovery artifacts
        # and other noise don't pollute the module graph (Bug #13).
        if item.get("is_excluded"):
            continue
        module = _top_level_module(item.get("path", ""), item.get("language", "unknown"))
        lang = item.get("language", "unknown")
        bucket = graph.setdefault(module, {})
        bucket[lang] = bucket.get(lang, 0) + 1
    return graph


def _module_matches_scope(module_scope: str | None, path: str, module_name: str = "") -> bool:
    if not module_scope:
        return True
    scope = module_scope.replace("\\", "/").strip("/")
    normalized_path = path.replace("\\", "/")
    normalized_module = module_name.replace("\\", "/").strip("/")
    return (
        normalized_path.startswith(f"{scope}/")
        or f"/{scope}/" in normalized_path
        or normalized_module == scope
        or normalized_module.startswith(f"{scope}/")
    )


def _read_text_prefix(path: Path, limit: int) -> str:
    if not path.exists():
        return ""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return handle.read(limit)
    except OSError:
        return ""


def _parse_mutation_score(stdout: str, stderr: str) -> float | None:
    pattern = re.compile(r"(?i)(?:mutation(?: score)?|score)\D+(\d+(?:\.\d+)?)")
    for text in (stdout, stderr):
        match = pattern.search(text or "")
        if match:
            return float(match.group(1))
    return None


class TestFactoryOrchestrator:
    # Tell the real pytest (>=6) not to try to collect this class as a
    # test class. The name starts with "Test" for historical reasons —
    # it's the orchestrator class, not a test. See Bug #5 (PR #24).
    __test__ = False

    def __init__(self, repo_root: str | Path, out_dir: str | Path, config_path: str | Path | None = None):
        self.repo_root = Path(repo_root).resolve()
        self.out_dir = Path(out_dir).resolve()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts = self.out_dir
        self.config = load_config(self.repo_root, config_path)
        self.storage = Storage(self.artifacts / "test_factory.sqlite")
        self.adapters = [JavaJUnitAdapter(), JsJestVitestAdapter(), PythonPytestAdapter()]
        (self.artifacts / "validation_runs").mkdir(parents=True, exist_ok=True)
        (self.artifacts / "coverage_deltas").mkdir(parents=True, exist_ok=True)
        (self.artifacts / "mutation").mkdir(parents=True, exist_ok=True)

    def close(self) -> None:
        self.storage.close()

    def _file_rows(self, module: str | None = None) -> list[dict[str, Any]]:
        rows = [dict(row) for row in self.storage.fetch_all("files")]
        return [row for row in rows if _module_matches_scope(module, row["path"], row.get("module", ""))]

    def _decode_work_item_row(self, row: dict[str, Any]) -> WorkItemRecord:
        decoded = {key: _decode_json_maybe(value) for key, value in row.items()}
        return WorkItemRecord(**{key: decoded[key] for key in WorkItemRecord.__dataclass_fields__ if key in decoded})

    def _enabled_adapter(self, adapter: Any) -> bool:
        return bool(self.config.language_adapters.get(adapter.language, True))

    def _primary_adapter(self, adapter_name: str | None = None) -> Any | None:
        """Return the adapter whose `detect()` has the highest confidence
        (i.e. the adapter that actually matches the target repo's primary
        language). Used by coverage_generate() to pick which
        discover_coverage_command to invoke. Falls back to the first enabled
        adapter if no adapter detects the repo at all.

        If `adapter_name` is given (Bug #36 fix), return the adapter with
        that name regardless of confidence. The caller has signalled they
        know better than the auto-detector (e.g. when a stray .java test
        file tips the tie-break toward java_junit on an otherwise Python
        repo, as happened running v2 against its own workspace).
        """
        if adapter_name:
            for adapter in self.adapters:
                if getattr(adapter, "language", None) == adapter_name.replace("_pytest", "").replace("_junit", "").replace("_jest_vitest", "") or getattr(adapter, "__class__", type(adapter)).__name__ == _adapter_class_name(adapter_name):
                    if self._enabled_adapter(adapter):
                        return adapter
            # Caller asked for a specific adapter but it isn't loaded
            # or is disabled. Fall through to auto-detect so the call
            # doesn't silently no-op.
        best: tuple[float, Any] | None = None
        for adapter in self.adapters:
            if not self._enabled_adapter(adapter):
                continue
            try:
                detection = adapter.detect(self.repo_root)
            except Exception:
                continue
            confidence = float(getattr(detection, "confidence", 0.0) or 0.0)
            if best is None or confidence > best[0]:
                best = (confidence, adapter)
        if best is None:
            return None
        if best[0] <= 0.0:
            # No adapter detected the repo. Fall back to the first enabled
            # adapter so the command at least gets a chance to run.
            for adapter in self.adapters:
                if self._enabled_adapter(adapter):
                    return adapter
        return best[1]

    def adapter_for_language(self, language: str) -> Any:
        lang = language.lower()
        if lang in {"python", "py"}:
            return next(adapter for adapter in self.adapters if adapter.language == "python" and self._enabled_adapter(adapter))
        if lang in {"java"}:
            return next(adapter for adapter in self.adapters if adapter.language == "java" and self._enabled_adapter(adapter))
        return next(adapter for adapter in self.adapters if adapter.language == "javascript" and self._enabled_adapter(adapter))

    def _discover_reports(self) -> list[Path]:
        reports: list[Path] = []
        # Patterns ordered most-specific-first. pytest-cov 7.x writes `coverage.json`
        # by default; pytest-cov 5.x/6.x wrote `coverage.xml`. v2's self-coverage run
        # (2026-06-10) was producing only `coverage.json` and the orchestrator was
        # not picking it up — see PR #22.
        for pattern in (
            "**/jacoco.xml",
            "**/jacocoTestReport.xml",
            "**/coverage.xml",
            "**/coverage.json",        # pytest-cov 7.x default
            "**/.coverage",            # coverage.py raw data file
            "**/coverage-final.json",  # istanbul / nyc JS coverage
            "**/lcov.info",
        ):
            reports.extend(sorted(self.repo_root.glob(pattern)))
        return reports

    def _collect_coverage_records(self, module: str | None = None) -> list[CoverageRecord]:
        coverage: list[CoverageRecord] = []
        for report in self._discover_reports():
            name = report.name.lower()
            if name in {"jacoco.xml", "jacotestreport.xml"} or "jacoco" in name:
                coverage.extend(parse_jacoco_xml(report))
            elif name == "coverage.xml":
                coverage.extend(parse_python_coverage_xml(report))
            elif name == "coverage.json":
                # `coverage.json` is ambiguous: it could be the coverage.py
                # output (pytest-cov 7.x default) or the istanbul output
                # (renamed). Distinguish by reading the full file and sniffing
                # the JSON shape: coverage.py always has a top-level `files`
                # dict; istanbul files have a per-file `s` (statements) map.
                # Sniffing is more reliable than name-based dispatch because
                # both tools emit a file literally named `coverage.json`.
                # See PR #22.
                head: dict[str, object] = {}
                try:
                    head = json.loads(report.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    head = {}
                if isinstance(head, dict) and isinstance(head.get("files"), dict):
                    coverage.extend(parse_coverage_py_json(report))
                else:
                    coverage.extend(parse_coverage_final_json(report))
            elif name == "coverage-final.json":
                coverage.extend(parse_coverage_final_json(report))
            elif name == "lcov.info":
                coverage.extend(parse_lcov_info(report))
        inventory_paths = [row["path"] for row in self._file_rows(module)]
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
            if inventory_paths and normalized_path not in inventory_paths:
                continue
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

    def _git_snapshot(self) -> dict[str, Any]:
        try:
            return {
                "head_sha": git_head_sha(self.repo_root),
                "changed_files": changed_files(self.repo_root),
            }
        except RuntimeError:
            return {"head_sha": "", "changed_files": []}

    def _adapter_detections(self) -> list[dict[str, Any]]:
        detections: list[dict[str, Any]] = []
        for adapter in self.adapters:
            if not self._enabled_adapter(adapter):
                continue
            detections.append(asdict(adapter.detect(self.repo_root)))
        return sorted(detections, key=lambda item: (item["language"], item["adapter"]))

    def _discovered_commands(self, modules: list[str]) -> list[dict[str, str]]:
        commands: list[dict[str, str]] = []
        for adapter in self.adapters:
            if not self._enabled_adapter(adapter):
                continue
            sample_module = next((module for module in modules if module), "root")
            commands.append({"language": adapter.language, "kind": "test", "command": adapter.discover_test_command(self.repo_root, sample_module).render()})
            commands.append({"language": adapter.language, "kind": "coverage", "command": adapter.discover_coverage_command(self.repo_root, sample_module).render()})
            mutation_command = adapter.discover_mutation_command(self.repo_root, sample_module, [])
            commands.append({"language": adapter.language, "kind": "mutation", "command": mutation_command.render()})
        return commands

    def scan(self, module: str | None = None) -> dict[str, Any]:
        files, exclusions = inventory_repo(self.repo_root, self.config, module=module)
        for record in files:
            self.storage.upsert_file(record)
        for exclusion in exclusions:
            self.storage.record_exception(exclusion["path"], exclusion["reason"], exclusion["rule"], exclusion.get("adapter", ""))
        language_stack = _language_stack([asdict(record) for record in files])
        module_graph = _module_graph([asdict(record) for record in files])
        modules = sorted({record.module for record in files})
        for module_name in modules:
            lang = next((record.language for record in files if record.module == module_name), "unknown")
            source_count = len([record for record in files if record.module == module_name and not record.is_test and not record.is_excluded])
            test_count = len([record for record in files if record.module == module_name and record.is_test])
            self.storage.upsert_module(module_name, lang, source_count, test_count, {"detected": True})
        _dump_json(self.artifacts / "repo_inventory.json", [asdict(record) for record in files])
        _dump_json(self.artifacts / "module_graph.json", module_graph)
        _dump_json(self.artifacts / "language_stack.json", language_stack)
        _dump_json(self.artifacts / "exclusions.json", exclusions)
        _dump_json(self.artifacts / "adapter_detections.json", self._adapter_detections())
        _dump_json(self.artifacts / "commands_discovered.json", self._discovered_commands(modules))
        (self.artifacts / "exceptions_register.yaml").write_text(
            "\n".join(f"- path: {e['path']}\n  reason: {e['reason']}\n  rule: {e['rule']}" for e in exclusions),
            encoding="utf-8",
        )
        return {"inventory": len(files), "exclusions": len(exclusions), "module_scope": module or "all"}

    def coverage(self, module: str | None = None) -> list[CoverageRecord]:
        coverage = self._collect_coverage_records(module)
        for record in coverage:
            self.storage.upsert_coverage(record)
        _dump_json(self.artifacts / "coverage_baseline.json", [asdict(record) for record in coverage])
        _dump_json(self.artifacts / "coverage_deltas" / "baseline.json", [asdict(record) for record in coverage])
        return coverage

    def coverage_generate(self, module: str | None = None, adapter_name: str | None = None) -> dict[str, Any]:
        """Run the primary adapter's `discover_coverage_command` to actually
        *generate* a coverage report on disk, then return the parsed records.

        This is opt-in (called from `run(generate_coverage=True)`) because it
        mutates the target repo (writes `coverage.json` / `coverage.xml`) and
        is the slowest step in the pipeline (5-30 min for a typical repo).

        Bug surfaced 2026-06-10 on v2's self-coverage run: the user had to
        manually run `coverage run -m pytest && coverage json` before
        `test-factory run`, because `coverage()` only reads existing reports.
        See PR #23.
        """
        adapter = self._primary_adapter(adapter_name=adapter_name)
        if adapter is None:
            return {
                "status": "skipped",
                "reason": "no enabled adapter for the primary language",
                "command": None,
                "exit_code": None,
                "stdout": "",
                "stderr": "",
            }
        sample_module = module or "root"
        command = adapter.discover_coverage_command(self.repo_root, sample_module)
        artifact_dir = self.artifacts / "coverage_runs"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        record_path = artifact_dir / "generate.json"
        timeout_seconds = self.config.validation_timeouts.full_seconds
        # Snapshot pre-run reports so we can detect whether the command
        # actually wrote new ones. Silent-pass-but-no-coverage-file is the
        # most common failure mode (e.g. pytest-cov plugin version
        # incompatibility — exits 0 but writes nothing). PR #23 adds the
        # post-run check so the user gets a warning instead of empty
        # coverage_baseline.json.
        #
        # PR #26 (Bug #6) fixes a false-positive in the PR #23 check: it
        # compared by path identity (`post - pre`), so a pre-existing
        # coverage.json that pytest-cov rewrote in place looked like
        # "nothing was written". The fix captures pre-run mtimes and
        # considers a report "new" if its post-run mtime is strictly
        # newer than the snapshot. This catches both:
        #   - truly new files (e.g. `.coverage` is created fresh)
        #   - overwritten files (e.g. `coverage.json` rewritten at the
        #     same path but with newer content)
        repo_root = Path(self.repo_root)
        def _existing_reports() -> dict[Path, float]:
            found: dict[Path, float] = {}
            for pattern in ("**/coverage.json", "**/coverage.xml", "**/.coverage"):
                for p in repo_root.glob(pattern):
                    if p.is_file():
                        try:
                            found[p.resolve()] = p.stat().st_mtime
                        except OSError:
                            continue
            return found
        pre_reports = _existing_reports()
        # Preflight: detect pom patterns that will silently produce empty
        # JaCoCo coverage even when the build succeeds (e.g. Broadleaf-
        # shaped static surefire <argLine>${...}</argLine>). Surface these
        # as preflight_findings on the result so the user sees them BEFORE
        # the multi-minute Maven run, not as a "no_report_written" warning
        # at the end. Adapter-level detection; the orchestrator just
        # threads the result through. Bug surfaced 2026-06-11 on
        # BroadleafCommerce (test-repo PR #13 follow-up).
        preflight_findings: list[dict[str, str]] = []
        if hasattr(adapter, "preflight_coverage_pitfalls"):
            try:
                preflight_findings = list(adapter.preflight_coverage_pitfalls(self.repo_root))
            except Exception as exc:  # pragma: no cover - defensive
                preflight_findings = [{
                    "kind": "preflight_error",
                    "message": f"preflight_coverage_pitfalls raised: {exc!r}",
                }]
        try:
            completed = subprocess.run(
                command.command,
                cwd=command.cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                shell=False,
            )
            status = "completed" if completed.returncode == 0 else "failed"
            result: dict[str, Any] = {
                "status": status,
                "command": command.render(),
                "exit_code": completed.returncode,
                "stdout": completed.stdout[-4000:],  # cap to avoid blowing up artifacts
                "stderr": completed.stderr[-4000:],
                "timeout_seconds": timeout_seconds,
                "preflight_findings": preflight_findings,
            }
        except subprocess.TimeoutExpired as exc:
            result = {
                "status": "timeout",
                "command": command.render(),
                "exit_code": 124,
                "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
                "stderr": (exc.stderr or "timeout")[-4000:] if isinstance(exc.stderr, (str, bytes)) else "timeout",
                "timeout_seconds": timeout_seconds,
                "preflight_findings": preflight_findings,
            }
        except FileNotFoundError as exc:
            result = {
                "status": "missing_binary",
                "command": command.render(),
                "exit_code": 127,
                "stdout": "",
                "stderr": f"command not found: {exc}",
                "timeout_seconds": timeout_seconds,
                "preflight_findings": preflight_findings,
            }
        # Post-run check: did the command actually produce a new coverage
        # report? If the subprocess exited 0 but no file was written,
        # surface that as a warning so the user doesn't waste an hour
        # wondering why coverage_baseline.json is empty.
        #
        # Compare mtimes against the pre-run snapshot. A report is
        # considered "new or updated" if its mtime is strictly newer
        # than the pre-run mtime. This catches both freshly-created
        # files and pre-existing files that were rewritten in place
        # (the most common case once you have any prior coverage run).
        post_reports = _existing_reports()
        new_reports: list[Path] = []
        for path, post_mtime in post_reports.items():
            pre_mtime = pre_reports.get(path)
            if pre_mtime is None or post_mtime > pre_mtime:
                new_reports.append(path)
        new_reports = sorted(new_reports)
        result["new_reports"] = [str(p) for p in new_reports]
        if result["status"] == "completed" and not new_reports:
            result["status"] = "no_report_written"
            result["warning"] = (
                "coverage command exited 0 but did not write a coverage.json / "
                "coverage.xml / .coverage file. Common causes: pytest-cov plugin "
                "version incompatible with the installed pytest; --cov specified "
                "without a package name; coverage.py not installed. The pipeline "
                "will continue with whatever pre-existing reports it can find."
            )
        _dump_json(record_path, result)
        # If the command succeeded (or partially succeeded), refresh parsed
        # records so the caller doesn't have to call `coverage()` separately.
        if result["status"] in {"completed", "no_report_written"}:
            return {"generation": result, "records": [asdict(r) for r in self.coverage(module=module)]}
        return {"generation": result, "records": []}

    def score(self, module: str | None = None) -> list[RiskScoreRecord]:
        coverage_rows = {
            row["path"]: CoverageRecord(
                **{k: row[k] for k in ("path", "line_coverage", "branch_coverage", "uncovered_lines", "uncovered_branches", "report_ref")}
            )
            for row in _read_json(self.artifacts / "coverage_baseline.json", [])
        }
        scores: list[RiskScoreRecord] = []
        for row in self._file_rows(module):
            if row.get("is_excluded") or row.get("is_test"):
                continue
            cov = coverage_rows.get(row["path"])
            source_path = self.repo_root / row["path"]
            text = _read_text_prefix(source_path, self.config.max_source_file_chars)
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
        _dump_json(
            self.artifacts / "risk_weighted_coverage.json",
            {"line_index": weighted_index(scores, use_branch=False), "branch_index": weighted_index(scores, use_branch=True)},
        )
        return scores

    def queue(self, module: str | None = None, zero_coverage_only: bool = False) -> list[dict[str, Any]]:
        scores = [item for item in _read_json(self.artifacts / "risk_scores.json", []) if _module_matches_scope(module, item["path"], item.get("module", ""))]
        queue = []
        for item in scores:
            if item.get("coverage_gap", 0) <= 0 and item.get("risk_score", 0) <= 0:
                continue
            item["priority"] = float(item.get("risk_score", 0)) * float(item.get("coverage_gap", 0))
            # Story 024: annotate every item with `zero_coverage` so
            # downstream consumers (final_report.md, the user's
            # scripts, the new CLI flag) can filter without having
            # to know the line/branch threshold semantics.
            item["zero_coverage"] = is_zero_coverage(
                float(item.get("line_coverage", 0.0) or 0.0),
                item.get("branch_coverage"),
            )
            queue.append(item)
        queue.sort(key=lambda item: (-item["priority"], item["path"]))
        _dump_json(self.artifacts / "test_gap_queue.json", queue)
        _dump_json(
            self.artifacts / "component_test_candidates.json",
            [item for item in queue if self._is_component_candidate(item)],
        )
        # Story 024: separate artifact for zero-coverage-only items,
        # sorted by risk_score (the priority formula collapses to
        # risk_score * 180 for all of them, so risk_score is the
        # meaningful axis). Path is the deterministic tiebreak.
        zero_coverage_queue = sorted(
            [item for item in queue if item.get("zero_coverage")],
            key=lambda item: (-float(item.get("risk_score", 0.0)), item["path"]),
        )
        _dump_json(self.artifacts / "zero_coverage_queue.json", zero_coverage_queue)
        if zero_coverage_only:
            return zero_coverage_queue
        return queue

    @staticmethod
    def _is_component_candidate(item: dict[str, Any]) -> bool:
        """Heuristic for files that benefit from component/integration tests
        (controllers, web layer, REST endpoints, JS UI components).

        Bug #34: the previous filter relied on `recommended_test_type`
        (not set on queue items) OR `risk_score >= 50` (always true for
        Broadleaf's risk distribution), so every queue item leaked into
        `component_test_candidates.json`. The new heuristic looks for web
        layer / controller / REST markers in the path.
        """
        path = str(item.get("path", "")).lower()
        if not path:
            return False
        markers = (
            "/web/",
            "controller",
            "/controller/",
            "endpoint",
            "/rest/",
            "/api/",
            "/resource/",
            "filter",
            "servlet",
            "interceptor",
        )
        return any(marker in path for marker in markers)

    def workitems(self, limit: int | None = None, module: str | None = None, zero_coverage_only: bool = False) -> list[WorkItemRecord]:
        coverage_records = [CoverageRecord(**item) for item in _read_json(self.artifacts / "coverage_baseline.json", []) if _module_matches_scope(module, item["path"])]
        scores = [RiskScoreRecord(**item) for item in _read_json(self.artifacts / "risk_scores.json", []) if _module_matches_scope(module, item["path"], item.get("module", ""))]
        # Story 024: when --zero-coverage-only is set, restrict the
        # generated work items to files with no test coverage.
        if zero_coverage_only:
            scores = [s for s in scores if is_zero_coverage(s.line_coverage, s.branch_coverage)]
        source_maps: dict[str, SourceTestMapRecord] = {}
        for score in scores:
            source_file = self.repo_root / score.path
            source_text = _read_text_prefix(source_file, self.config.max_source_file_chars)
            adapter = self.adapter_for_language(source_file.suffix.lstrip(".").lower() or "javascript")
            candidate_tests = infer_existing_test_files(score.path, adapter.language)
            existing_tests = [path for path in candidate_tests if (self.repo_root / path).exists()]
            supporting_files = []
            for candidate in adapter.recommend_supporting_files(source_file) + supporting_files_for_source(score.path, adapter.language):
                if candidate and (self.repo_root / candidate).exists() and candidate not in supporting_files:
                    supporting_files.append(candidate)
            source_maps[score.path] = SourceTestMapRecord(
                source_path=score.path,
                candidate_tests=existing_tests,
                candidate_paths=candidate_tests,
                supporting_files=supporting_files[: self.config.max_supporting_files_per_work_item],
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
            existing = self.storage.get_work_item(item.work_item_id)
            if existing is not None:
                stored = self._decode_work_item_row(dict(existing))
                item.status = stored.status
                item.validated_files = stored.validated_files
                item.validation_repo_sha = stored.validation_repo_sha
                item.validation_reason = stored.validation_reason
                item.validation_report_path = stored.validation_report_path
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

    def _validation_failure_reason(self, item: WorkItemRecord, before: RiskScoreRecord, after: CoverageRecord | None, targeted: ValidationRunRecord, module_run: ValidationRunRecord) -> str:
        if targeted.exit_code != 0:
            return f"targeted validation failed ({targeted.status})"
        if module_run.exit_code != 0:
            return f"module validation failed ({module_run.status})"
        disallowed = find_disallowed_test_markers(self.repo_root, item.existing_test_files)
        if disallowed:
            return f"disallowed test markers found in {', '.join(disallowed)}"
        if after is None:
            return "coverage report missing after validation"
        improved, reason = coverage_improved(before, after.line_coverage, after.branch_coverage)
        return reason if not improved else ""

    def _validation_summary_path(self, work_item_id: str) -> Path:
        return self.artifacts / "validation_runs" / f"{work_item_id}-summary.json"

    def validate(self, work_item_id: str) -> dict[str, Any]:
        row = self.storage.get_work_item(work_item_id)
        if not row:
            raise KeyError(work_item_id)
        item = self._decode_work_item_row(dict(row))
        risk_row = next((RiskScoreRecord(**payload) for payload in _read_json(self.artifacts / "risk_scores.json", []) if payload["path"] == item.source_path), None)
        if risk_row is None:
            raise RuntimeError(f"missing risk score for {item.source_path}")
        adapter = self.adapter_for_language(item.language)
        targeted_command = adapter.discover_test_command(self.repo_root, item.module)
        module_command = adapter.discover_coverage_command(self.repo_root, item.module)
        validation_dir = self.artifacts / "validation_runs"
        coverage_delta_path = self.artifacts / "coverage_deltas" / f"{work_item_id}.json"
        git_snapshot = self._git_snapshot()
        self.storage.update_work_item_status(work_item_id, "running")
        targeted = run_targeted_validation(self.storage, work_item_id, targeted_command, validation_dir, self.config.validation_timeouts.targeted_seconds)
        if targeted.exit_code == 0:
            module_run = run_module_validation(self.storage, work_item_id, module_command, validation_dir, self.config.validation_timeouts.module_seconds)
        else:
            module_run = ValidationRunRecord(
                work_item_id=work_item_id,
                command=module_command.render(),
                exit_code=125,
                stdout="",
                stderr="module validation skipped because targeted validation failed",
                timeout_seconds=self.config.validation_timeouts.module_seconds,
                artifact_path=str(validation_dir / f"{work_item_id}-module.json"),
                phase="module",
                status="skipped",
            )
            Path(module_run.artifact_path).write_text(json.dumps(asdict(module_run), indent=2), encoding="utf-8")
            self.storage.insert_validation_run(module_run)
        after = self._coverage_for_path(item.source_path) if module_run.exit_code == 0 else None
        delta_payload = {
            "work_item_id": work_item_id,
            "source_path": item.source_path,
            "before_line_coverage": risk_row.line_coverage,
            "before_branch_coverage": risk_row.branch_coverage,
            "after_line_coverage": after.line_coverage if after else None,
            "after_branch_coverage": after.branch_coverage if after else None,
        }
        _dump_json(coverage_delta_path, delta_payload)
        failure_reason = self._validation_failure_reason(item, risk_row, after, targeted, module_run)
        status = "failed" if failure_reason else "passed"
        self.storage.update_work_item_validation(
            work_item_id,
            status=status,
            validated_files=git_snapshot["changed_files"],
            validation_repo_sha=git_snapshot["head_sha"],
            validation_reason=failure_reason,
            validation_report_path=str(coverage_delta_path),
        )
        result = {
            "targeted": asdict(targeted),
            "module": asdict(module_run),
            "status": status,
            "validated_files": git_snapshot["changed_files"],
            "validation_repo_sha": git_snapshot["head_sha"],
            "coverage_delta_path": str(coverage_delta_path),
        }
        if failure_reason:
            result["reason"] = failure_reason
        _dump_json(self._validation_summary_path(work_item_id), result)
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
        command_specs: list[dict[str, Any]] = []
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
            if detection.command:
                command_specs.append({"language": normalized_language, "command": detection.command})
        if mutation_enabled:
            for index, spec in enumerate(command_specs, start=1):
                command = spec["command"]
                artifact_path = mutation_dir / f"mutation-run-{index}.json"
                try:
                    completed = subprocess.run(
                        command,
                        cwd=self.repo_root,
                        capture_output=True,
                        text=True,
                        timeout=self.config.mutation.timeout_seconds,
                        shell=False,
                    )
                    score = _parse_mutation_score(completed.stdout, completed.stderr)
                    result = {
                        "path": f"mutation-run-{index}",
                        "module": spec["language"],
                        "tool": command[0],
                        "command": " ".join(command),
                        "exit_code": completed.returncode,
                        "stdout": completed.stdout,
                        "stderr": completed.stderr,
                        "score": score,
                        "status": "completed",
                        "report_ref": str(artifact_path),
                    }
                except subprocess.TimeoutExpired as exc:
                    result = {
                        "path": f"mutation-run-{index}",
                        "module": spec["language"],
                        "tool": command[0],
                        "command": " ".join(command),
                        "exit_code": 124,
                        "stdout": (exc.stdout or "") if isinstance(exc.stdout, str) else "",
                        "stderr": (exc.stderr or "") if isinstance(exc.stderr, str) else "timeout",
                        "score": None,
                        "status": "timeout",
                        "report_ref": str(artifact_path),
                    }
                except (FileNotFoundError, OSError) as exc:
                    result = {
                        "path": f"mutation-run-{index}",
                        "module": spec["language"],
                        "tool": command[0],
                        "command": " ".join(command),
                        "exit_code": 127,
                        "stdout": "",
                        "stderr": str(exc),
                        "score": None,
                        "status": "missing-executable",
                        "report_ref": str(artifact_path),
                    }
                _dump_json(artifact_path, result)
                results.append(result)
        _dump_json(mutation_dir / "mutation_tool_detection.json", detections)
        _dump_json(mutation_dir / "mutation_commands.json", command_specs)
        _dump_json(mutation_dir / "mutation_results.json", results)
        numeric_scores = [float(result["score"]) for result in results if result.get("score") is not None]
        below_threshold = (
            self.config.mutation.fail_under_score is not None
            and any(score < float(self.config.mutation.fail_under_score) for score in numeric_scores)
        )
        _dump_json(
            mutation_dir / "mutation_score_summary.json",
            {
                "candidates": len(candidates),
                "tool_available": any(item.get("available") for item in detections.values()),
                "executed": mutation_enabled,
                "result_count": len(results),
                "scores": numeric_scores,
                "below_threshold": below_threshold,
            },
        )
        for candidate in candidates:
            self.storage.upsert_mutation_candidate(candidate["path"], candidate["module"], float(candidate["score"]), candidate)
        for result in results:
            self.storage.upsert_mutation_result(
                result["path"],
                result["module"],
                result.get("tool", ""),
                result.get("command", ""),
                int(result.get("exit_code", 0)),
                result.get("stdout", ""),
                result.get("stderr", ""),
                float(result["score"]) if result.get("score") is not None else 0.0,
                result.get("report_ref", ""),
            )
        return {
            "candidates": len(candidates),
            "tool_available": any(item.get("available") for item in detections.values()),
            "executed": mutation_enabled,
            "below_threshold": below_threshold,
        }

    def report(self, module: str | None = None) -> dict[str, str]:
        final_report = render_final_report(self.artifacts)
        json_report = render_json_report(self.artifacts)
        pr_summary = render_pr_summary(self.artifacts, module=module or "")
        (self.artifacts / "final_report.md").write_text(final_report, encoding="utf-8")
        (self.artifacts / "pr_summary.md").write_text(pr_summary, encoding="utf-8")
        (self.artifacts / "final_report.json").write_text(json_report, encoding="utf-8")
        return {"final_report": str(self.artifacts / "final_report.md"), "pr_summary": str(self.artifacts / "pr_summary.md")}

    def run(
        self,
        limit: int | None = None,
        mutation: bool | None = None,
        mutation_high_risk_only: bool | None = None,
        module: str | None = None,
        generate_coverage: bool = False,
        adapter_name: str | None = None,
        zero_coverage_only: bool = False,
    ) -> dict[str, Any]:
        self.scan(module=module)
        # Opt-in coverage generation: when generate_coverage is True, run the
        # primary adapter's `discover_coverage_command` to actually produce a
        # coverage report. This is a non-deterministic, slow, and repo-mutating
        # step (writes coverage.json / coverage.xml into the target repo), so
        # it is OFF by default. When False (the default), `coverage()` below
        # only reads whatever reports already exist on disk. See PR #23.
        #
        # `adapter_name` (Bug #36) lets the caller force a specific adapter
        # when auto-detect picks the wrong one (e.g. a stray .java test file
        # tipping the tie-break toward java_junit on an otherwise Python repo).
        coverage_generation: dict[str, Any] | None = None
        if generate_coverage:
            coverage_generation = self.coverage_generate(module=module, adapter_name=adapter_name)
        self.coverage(module=module)
        self.score(module=module)
        self.queue(module=module, zero_coverage_only=zero_coverage_only)
        self.workitems(limit=limit, module=module, zero_coverage_only=zero_coverage_only)
        self.mutate(enabled=mutation, high_risk_only=mutation_high_risk_only)
        self.report(module=module)
        return {
            "status": "ok",
            "module_scope": module or "all",
            "coverage_generation": coverage_generation,
        }

    def branch(self, module: str, allow_dirty: bool = False) -> dict[str, Any]:
        record = create_branch(self.repo_root, module, self.config.branching.branch_prefix, allow_dirty=allow_dirty or self.config.branching.allow_dirty)
        self.storage.upsert_branch_run(record.branch_name, record.module, record.created, record.dirty, record.sha)
        return asdict(record)

    def commit(self, module: str, allow_dirty: bool = False) -> dict[str, Any]:
        passed_items = [
            self._decode_work_item_row(dict(row))
            for row in self.storage.list_work_items(status="passed")
            if dict(row)["module"] == module
        ]
        if not passed_items:
            raise RuntimeError(f"no passed work items recorded for module {module}")
        validated_files = sorted({path for item in passed_items for path in item.validated_files if path})
        if not validated_files:
            raise RuntimeError(f"no validated file set recorded for module {module}")
        validation_shas = sorted({item.validation_repo_sha for item in passed_items if item.validation_repo_sha})
        if len(validation_shas) != 1:
            raise RuntimeError(f"validated work items for module {module} do not share a single repository baseline")
        record = commit_module(
            self.repo_root,
            module,
            expected_head_sha=validation_shas[0],
            files_to_stage=validated_files,
            allow_dirty=allow_dirty or self.config.branching.allow_dirty,
        )
        self.storage.upsert_commit(record.module, record.message, record.sha, record.files)
        return asdict(record)

    def pr_summary(self, module: str | None = None) -> str:
        summary = render_pr_summary(self.artifacts, module=module or "")
        (self.artifacts / "pr_summary.md").write_text(summary, encoding="utf-8")
        return summary
