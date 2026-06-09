from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.detectors.javascript import detect_javascript_routes
from repo_discovery_analyzer.inventory import scan_repo


class JavaScriptRouteTests(unittest.TestCase):
    def test_detects_express_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "server.js").write_text("app.get('/health', (req, res) => res.send('ok'))\n", encoding="utf-8")
            records = scan_repo(repo, "acme", "widget", "abc123", False, 1024)
            result = detect_javascript_routes(repo, "acme", "widget", "abc123", records)
            self.assertEqual(result["routes"][0]["method"], "GET")
            self.assertEqual(result["routes"][0]["path"], "/health")


if __name__ == "__main__":
    unittest.main()

