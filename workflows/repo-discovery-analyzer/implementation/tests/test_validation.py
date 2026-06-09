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


if __name__ == "__main__":
    unittest.main()
