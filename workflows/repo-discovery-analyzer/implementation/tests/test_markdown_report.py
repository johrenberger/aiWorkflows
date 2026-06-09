from __future__ import annotations

import unittest

from repo_discovery_analyzer.markdown_report import MAX_REPORT_ROWS, render_markdown_report


class MarkdownReportTests(unittest.TestCase):
    def test_report_is_deterministic_and_bounds_large_sections(self) -> None:
        findings = [
            {
                "type": "marker",
                "path": f"src/module_{index}.py",
                "github_url": f"https://github.com/acme/widget/blob/abc123def/src/module_{index}.py",
                "line_number": index + 1,
                "impact_hint": "follow up",
                "confidence": "high",
            }
            for index in range(MAX_REPORT_ROWS + 5)
        ]
        data = {
            "analysis_manifest": {"commit": "abc123def", "repo_path": "/tmp/widget", "elapsed_ms": 10},
            "github_links": {"repo_url": "https://github.com/acme/widget"},
            "loc_metrics": {"total_files": 55, "total_lines": 100},
            "validation_report": {"status": "passed", "warnings": []},
            "tests": {"source_to_test_ratio": {"source_files": 50, "test_files": 5, "ratio": 0.1}},
            "hygiene_findings": {
                "hygiene_findings": findings,
                "hygiene_findings_total": len(findings),
                "hygiene_findings_truncated": False,
            },
        }

        first = render_markdown_report(data)
        second = render_markdown_report(data)

        self.assertEqual(first, second)
        self.assertIn("Showing 50 of 55 items", first)
        self.assertNotIn("src/module_54.py", first)
        self.assertIn("[`src/module_0.py`](https://github.com/acme/widget/blob/abc123def/src/module_0.py)", first)


if __name__ == "__main__":
    unittest.main()
