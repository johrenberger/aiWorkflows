from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.detectors.java_spring import detect_java_spring_routes
from repo_discovery_analyzer.inventory import scan_repo


class JavaSpringRouteTests(unittest.TestCase):
    def test_detects_spring_route_and_entity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            src = repo / "src" / "main" / "java" / "com" / "acme"
            src.mkdir(parents=True)
            (src / "WidgetController.java").write_text(
                """
package com.acme;
import org.springframework.web.bind.annotation.*;
@RestController
class WidgetController {
  @GetMapping("/widgets")
  public String list() { return "ok"; }
}
""".strip()
                + "\n",
                encoding="utf-8",
            )
            records = scan_repo(repo, "acme", "widget", "abc123", False, 1024)
            result = detect_java_spring_routes(repo, "acme", "widget", "abc123", records)
            self.assertEqual(result["routes"][0]["path"], "/widgets")
            self.assertEqual(result["routes"][0]["method"], "GET")


if __name__ == "__main__":
    unittest.main()

