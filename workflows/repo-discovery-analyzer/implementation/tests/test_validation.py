from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.io_utils import json_dump
from repo_discovery_analyzer.validation import validate_outputs


class ValidationTests(unittest.TestCase):
    def test_validation_passes_on_commit_pinned_urls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            json_dump(out / "analysis_manifest.json", {"tool_name": "x"}, indent=2)
            json_dump(out / "repo_inventory.json", {"files": [{"github_url": "https://github.com/acme/widget/blob/abc1234/src/app.py"}]}, indent=2)
            for name in [
                "loc_metrics.json",
                "tech_stack.json",
                "entry_points.json",
                "project_structure.json",
                "routes.json",
                "db_schema.json",
                "dependencies.json",
                "integrations.json",
                "tests.json",
                "error_logging.json",
                "security_signals.json",
                "build_deploy.json",
                "hygiene_findings.json",
                "contradiction_candidates.json",
                "github_links.json",
            ]:
                json_dump(out / name, {}, indent=2)
            result = validate_outputs(out, ["analysis_manifest.json", "repo_inventory.json"], [])
            self.assertEqual(result["status"], "passed")

    def test_validation_fails_on_unpinned_inventory_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            repo = Path(tmp) / "repo"
            repo.mkdir()
            json_dump(out / "analysis_manifest.json", {"tool_name": "repo-discovery-analyzer", "tool_version": "0.1.0", "commit": "abc1234", "start_time_utc": "t", "end_time_utc": "t", "elapsed_ms": 1}, indent=2)
            json_dump(out / "repo_inventory.json", {"files": [{"path": "src/app.py", "github_url": "https://github.com/acme/widget/blob/main/src/app.py", "reviewed_by_analyzer": True, "skipped": False}]}, indent=2)
            for name in [
                "loc_metrics.json",
                "tech_stack.json",
                "entry_points.json",
                "project_structure.json",
                "routes.json",
                "db_schema.json",
                "dependencies.json",
                "integrations.json",
                "tests.json",
                "error_logging.json",
                "security_signals.json",
                "build_deploy.json",
                "hygiene_findings.json",
                "contradiction_candidates.json",
                "github_links.json",
            ]:
                json_dump(out / name, {}, indent=2)
            result = validate_outputs(out, ["analysis_manifest.json", "repo_inventory.json"], [], repo_path=repo, commit="abc1234")
            self.assertEqual(result["status"], "failed")

    def test_validation_fails_on_invalid_json_payload(self) -> None:
        # A required file that exists but contains garbage JSON should
        # produce a "json:<filename>" check failure rather than crashing.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "analysis_manifest.json").write_text("{ not json", encoding="utf-8")
            (out / "repo_inventory.json").write_text("{ not json either", encoding="utf-8")
            result = validate_outputs(out, ["analysis_manifest.json", "repo_inventory.json"], [])
        self.assertEqual(result["status"], "failed")
        names = {c["check"].split(":", 1)[1] for c in result["checks"] if c["check"].startswith("json:")}
        self.assertIn("analysis_manifest.json", names)
        self.assertIn("repo_inventory.json", names)

    def test_validation_inventory_path_against_missing_repo_file(self) -> None:
        # If repo_path is provided and an inventory entry references a path
        # that does not exist on disk (and the entry is not marked skipped),
        # the inventory:paths check should record a False status. Note: this
        # is currently a reporting-only check — it does not flip the overall
        # status to "failed" (that decision is reserved for the required_files
        # existence/json/urls checks). This test pins that behavior.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / "real.py").write_text("x = 1\n", encoding="utf-8")
            manifest = {
                "tool_name": "repo-discovery-analyzer",
                "tool_version": "0.1.0",
                "commit": "abc1234",
                "start_time_utc": "t",
                "end_time_utc": "t",
                "elapsed_ms": 1,
            }
            inventory = {
                "files": [
                    {
                        "path": "real.py",
                        "github_url": "https://github.com/acme/widget/blob/abc1234/real.py",
                        "reviewed_by_analyzer": True,
                        "skipped": False,
                    },
                    {
                        "path": "ghost.py",
                        "github_url": "https://github.com/acme/widget/blob/abc1234/ghost.py",
                        "reviewed_by_analyzer": True,
                        "skipped": False,
                    },
                ]
            }
            json_dump(out / "analysis_manifest.json", manifest, indent=2)
            json_dump(out / "repo_inventory.json", inventory, indent=2)
            for name in [
                "loc_metrics.json",
                "tech_stack.json",
                "entry_points.json",
                "project_structure.json",
                "routes.json",
                "db_schema.json",
                "dependencies.json",
                "integrations.json",
                "tests.json",
                "error_logging.json",
                "security_signals.json",
                "build_deploy.json",
                "hygiene_findings.json",
                "contradiction_candidates.json",
                "github_links.json",
            ]:
                json_dump(out / name, {}, indent=2)
            result = validate_outputs(
                out,
                ["analysis_manifest.json", "repo_inventory.json"],
                [],
                repo_path=repo,
                commit="abc1234",
            )
        # Overall status remains "passed" because no required-file checks failed.
        self.assertEqual(result["status"], "passed")
        # But the inventory:paths check should have recorded False.
        paths_check = next(c for c in result["checks"] if c["check"] == "inventory:paths")
        self.assertFalse(paths_check["status"])

    def test_validation_inventory_no_reviewed_files_fails(self) -> None:
        # inventory:reviewed_files requires at least one reviewed file.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            json_dump(out / "analysis_manifest.json", {"tool_name": "x"}, indent=2)
            json_dump(
                out / "repo_inventory.json",
                {"files": [{"path": "x.py", "reviewed_by_analyzer": False, "skipped": True, "github_url": ""}]},
                indent=2,
            )
            result = validate_outputs(out, ["analysis_manifest.json", "repo_inventory.json"], [])
        reviewed_check = next(c for c in result["checks"] if c["check"] == "inventory:reviewed_files")
        self.assertFalse(reviewed_check["status"])

    def test_validation_status_is_passed_with_warnings_when_warnings_list_nonempty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            json_dump(out / "analysis_manifest.json", {"tool_name": "x"}, indent=2)
            json_dump(out / "repo_inventory.json", {"files": []}, indent=2)
            result = validate_outputs(out, ["analysis_manifest.json", "repo_inventory.json"], ["one warning"])
        self.assertEqual(result["status"], "passed_with_warnings")
        warnings_check = next(c for c in result["checks"] if c["check"] == "warnings:collected")
        self.assertTrue(warnings_check["status"])

    def test_validation_fails_when_manifest_tool_name_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            json_dump(out / "analysis_manifest.json", {"tool_name": "wrong-tool"}, indent=2)
            json_dump(out / "repo_inventory.json", {"files": [{"path": "a", "github_url": "", "reviewed_by_analyzer": True, "skipped": False}]}, indent=2)
            result = validate_outputs(out, ["analysis_manifest.json", "repo_inventory.json"], [])
        tool_check = next(c for c in result["checks"] if c["check"] == "manifest:tool_name")
        self.assertFalse(tool_check["status"])

    def test_validation_fails_on_unpinned_string_in_payload(self) -> None:
        # A bare unpinned github URL string in a payload (not in a *_github_url
        # key) should still be flagged by the recursive _urls_commit_pinned walker.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            json_dump(out / "analysis_manifest.json", {"tool_name": "x"}, indent=2)
            json_dump(
                out / "repo_inventory.json",
                {"files": [], "extra": "see https://github.com/acme/widget/blob/main/docs"},
                indent=2,
            )
            result = validate_outputs(out, ["analysis_manifest.json", "repo_inventory.json"], [])
        url_check = next(c for c in result["checks"] if c["check"] == "urls:repo_inventory.json")
        self.assertFalse(url_check["status"])


if __name__ == "__main__":
    unittest.main()
