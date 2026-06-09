from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.cli import REQUIRED_OUTPUTS, main


class CliTests(unittest.TestCase):
    def test_cli_generates_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as out_dir:
            repo = Path(repo_dir)
            (repo / "package.json").write_text('{"name":"widget","dependencies":{"react":"^18.2.0"}}', encoding="utf-8")
            (repo / "src").mkdir()
            (repo / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
            code = main(
                [
                    "--repo-path",
                    str(repo),
                    "--github-url",
                    "https://github.com/acme/widget",
                    "--commit",
                    "abc123def",
                    "--output-dir",
                    out_dir,
                ]
            )
            self.assertEqual(code, 0)
            output = Path(out_dir)
            for name in REQUIRED_OUTPUTS:
                self.assertTrue((output / name).exists(), name)
            report = (output / "analysis_report.md").read_text(encoding="utf-8")
            self.assertIn("# Repository Analysis: widget", report)
            self.assertIn("## Executive Summary", report)
            self.assertIn("## Technology Stack", report)
            self.assertIn("## Evidence Files", report)
            self.assertIn("validation_report.json", report)


if __name__ == "__main__":
    unittest.main()
