from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.detectors.security import detect_security
from repo_discovery_analyzer.inventory import scan_repo


class SecurityRedactionTests(unittest.TestCase):
    def test_redacts_secret_like_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "config.py").write_text("API_KEY = 'supersecretapikeyvalue'\n", encoding="utf-8")
            records = scan_repo(repo, "acme", "widget", "abc123", False, 1024)
            result = detect_security(repo, "acme", "widget", "abc123", records)
            text = str(result)
            self.assertIn("<redacted>", text)
            self.assertNotIn("supersecretapikeyvalue", text)


if __name__ == "__main__":
    unittest.main()

