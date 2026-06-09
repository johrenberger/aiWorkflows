from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.inventory import scan_repo


class InventoryTests(unittest.TestCase):
    def test_inventory_excludes_vendor_dirs_and_tracks_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
            (repo / "node_modules").mkdir()
            (repo / "node_modules" / "junk.js").write_text("alert(1)\n", encoding="utf-8")
            records = scan_repo(repo, "acme", "widget", "abc123", include_large_files=False, max_file_bytes=1024)
            paths = [record.path for record in records]
            self.assertIn("src/app.py", paths)
            self.assertNotIn("node_modules/junk.js", paths)
            app = next(record for record in records if record.path == "src/app.py")
            self.assertFalse(app.skipped)
            self.assertEqual(app.line_count, 1)
            self.assertTrue(app.github_url.endswith("/blob/abc123/src/app.py"))

    def test_classifies_common_test_names_and_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "tests").mkdir()
            (repo / "tests" / "auth.test.js").write_text("test('auth', () => {})\n", encoding="utf-8")
            (repo / "widget.spec.ts").write_text("describe('widget', () => {})\n", encoding="utf-8")
            records = scan_repo(repo, "acme", "widget", "abc1234", False, 1024)
            roles = {record.path: record.role_guess for record in records}
            self.assertEqual(roles["tests/auth.test.js"], "test")
            self.assertEqual(roles["widget.spec.ts"], "test")

    def test_large_file_is_skipped_by_default_and_streamed_when_included(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / "large.py"
            path.write_text("line\n" * 20, encoding="utf-8")

            skipped = scan_repo(repo, "acme", "widget", "abc1234", False, 16)[0]
            included = scan_repo(repo, "acme", "widget", "abc1234", True, 16)[0]

            self.assertTrue(skipped.skipped)
            self.assertIn("file exceeds max_file_bytes", skipped.skip_reason or "")
            self.assertFalse(included.skipped)
            self.assertEqual(included.line_count, 20)


if __name__ == "__main__":
    unittest.main()
