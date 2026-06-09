from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from repo_discovery_analyzer import io_utils
from repo_discovery_analyzer.detectors.hygiene import detect_hygiene
from repo_discovery_analyzer.detectors.security import detect_security
from repo_discovery_analyzer.inventory import scan_repo


class DetectorNoiseTests(unittest.TestCase):
    def test_generated_docs_do_not_create_security_or_url_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            docs = repo / "_docs" / "component-analysis"
            docs.mkdir(parents=True)
            (docs / "report.json").write_text(
                '{"auth":"session token","repo":"https://github.com/acme/widget"}\n',
                encoding="utf-8",
            )
            (repo / "REPORT.md").write_text(
                "Authentication report with OAuth and session details.\n"
                "Repository: https://github.com/acme/widget\n",
                encoding="utf-8",
            )
            records = scan_repo(repo, "acme", "widget", "abc1234", False, 4096)

            security = detect_security(repo, "acme", "widget", "abc1234", records)
            hygiene = detect_hygiene(repo, "acme", "widget", "abc1234", records)

            self.assertEqual(security["security_signals"], [])
            self.assertEqual(hygiene["hygiene_findings"], [])

    def test_ci_permissions_and_test_placeholders_are_not_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            workflow = repo / ".github" / "workflows"
            workflow.mkdir(parents=True)
            (workflow / "ci.yml").write_text(
                "permissions:\n"
                "  id-token: write\n"
                "env:\n"
                "  WEBHOOK_SECRET: test-secret\n"
                "steps:\n"
                "  - run: echo \"login with wrong password: expected 401\"\n",
                encoding="utf-8",
            )
            records = scan_repo(repo, "acme", "widget", "abc1234", False, 4096)

            security = detect_security(repo, "acme", "widget", "abc1234", records)
            hygiene = detect_hygiene(repo, "acme", "widget", "abc1234", records)

            self.assertFalse(
                any(item["category"] == "secrets-like pattern" for item in security["security_signals"])
            )
            self.assertFalse(
                any(item["type"] == "credential-like-key" for item in hygiene["hygiene_findings"])
            )

    def test_source_secrets_and_external_urls_remain_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "config.js").write_text(
                'const API_KEY = "live-production-key-12345";\n'
                'const endpoint = "https://api.example.net/v1";\n',
                encoding="utf-8",
            )
            records = scan_repo(repo, "acme", "widget", "abc1234", False, 4096)

            security = detect_security(repo, "acme", "widget", "abc1234", records)
            hygiene = detect_hygiene(repo, "acme", "widget", "abc1234", records)

            self.assertTrue(
                any(item["category"] == "secrets-like pattern" for item in security["security_signals"])
            )
            self.assertTrue(
                any(item["type"] == "credential-like-key" for item in hygiene["hygiene_findings"])
            )
            self.assertTrue(
                any(item["type"] == "hardcoded-url" for item in hygiene["hygiene_findings"])
            )

    def test_runtime_values_and_template_literals_are_not_credentials_or_env_vars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "auth.js").write_text(
                "const password = hashPassword(input);\n"
                "const cookies = parseCookies(req.headers.cookie || '');\n"
                "const message = `Exchange #${id} response: ${response}`;\n",
                encoding="utf-8",
            )
            records = scan_repo(repo, "acme", "widget", "abc1234", False, 4096)

            security = detect_security(repo, "acme", "widget", "abc1234", records)
            hygiene = detect_hygiene(repo, "acme", "widget", "abc1234", records)

            self.assertFalse(
                any(item["category"] == "secrets-like pattern" for item in security["security_signals"])
            )
            self.assertFalse(
                any(item["category"] == "environment variable usage" for item in security["security_signals"])
            )
            self.assertFalse(
                any(item["type"] == "credential-like-key" for item in hygiene["hygiene_findings"])
            )

    def test_unquoted_config_secret_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "application.yml").write_text(
                "service:\n"
                "  client_secret: production-secret-value-123\n",
                encoding="utf-8",
            )
            records = scan_repo(repo, "acme", "widget", "abc1234", False, 4096)

            security = detect_security(repo, "acme", "widget", "abc1234", records)
            hygiene = detect_hygiene(repo, "acme", "widget", "abc1234", records)

            self.assertTrue(
                any(item["category"] == "secrets-like pattern" for item in security["security_signals"])
            )
            self.assertTrue(
                any(item["type"] == "credential-like-key" for item in hygiene["hygiene_findings"])
            )

    def test_safe_read_text_caches_repeat_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / "README.md"
            path.write_text("cached content\n", encoding="utf-8")

            io_utils.clear_safe_read_text_cache()
            with patch("repo_discovery_analyzer.io_utils._read_text_uncached", wraps=io_utils._read_text_uncached) as mocked:
                first = io_utils.safe_read_text(path)
                second = io_utils.safe_read_text(path)

            self.assertEqual(first, second)
            self.assertEqual(mocked.call_count, 1)

    def test_safe_read_text_stops_at_requested_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "large.txt"
            path.write_text("x" * 32, encoding="utf-8")

            io_utils.clear_safe_read_text_cache()
            text, reason = io_utils.safe_read_text(path, max_bytes=16)

            self.assertIsNone(text)
            self.assertIn("file exceeds max read size", reason or "")

    def test_bounded_items_reports_truncation(self) -> None:
        items, total, truncated = io_utils.bounded_items(list(range(5)), limit=3)

        self.assertEqual(items, [0, 1, 2])
        self.assertEqual(total, 5)
        self.assertTrue(truncated)

    def test_hygiene_findings_report_bounded_total(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for index in range(5):
                (repo / f"module_{index}.py").write_text("# TODO: follow up\n", encoding="utf-8")
            records = scan_repo(repo, "acme", "widget", "abc1234", False, 4096)

            with patch("repo_discovery_analyzer.detectors.hygiene.DEFAULT_MAX_SUMMARY_ITEMS", 3):
                result = detect_hygiene(repo, "acme", "widget", "abc1234", records)

            self.assertEqual(len(result["hygiene_findings"]), 3)
            self.assertEqual(result["hygiene_findings_total"], 5)
            self.assertTrue(result["hygiene_findings_truncated"])


if __name__ == "__main__":
    unittest.main()
