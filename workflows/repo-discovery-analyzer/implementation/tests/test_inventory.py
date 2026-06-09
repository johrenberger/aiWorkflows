from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from repo_discovery_analyzer.inventory import build_project_structure, scan_repo
from repo_discovery_analyzer.model import FileRecord


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

    def test_unreadable_path_is_marked_skipped_with_reason(self) -> None:
        # NOTE: This branch is essentially defensive — scan_repo's try/except
        # is around `path.stat().st_size`, but `walk_files` (via `path.is_dir()`)
        # calls `path.stat()` first and is NOT guarded. So in practice this
        # branch only fires if the file is unlinkable between is_dir() and
        # stat() (a TOCTOU race). We exercise it by stubbing stat AFTER the
        # walk yields paths, which simulates that race deterministically.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "ghost.py").write_text("print('hi')\n", encoding="utf-8")
            ghost = repo / "ghost.py"

            real_stat = Path.stat

            def flaky_stat(self, *a, **kw):
                if self == ghost:
                    raise OSError(5, "input/output error")  # EIO
                return real_stat(self, *a, **kw)

            # Patch is_dir too — otherwise the OSError from the walk phase
            # leaks out before the OSError-protected stat() runs.
            real_is_dir = Path.is_dir

            def flaky_is_dir(self, *a, **kw):
                if self == ghost:
                    return False  # walk proceeds past it
                return real_is_dir(self, *a, **kw)

            with mock.patch.object(Path, "is_dir", flaky_is_dir), \
                 mock.patch.object(Path, "stat", flaky_stat):
                records = scan_repo(repo, "acme", "widget", "abc1234", False, 1024)

            ghost_rec = next(r for r in records if r.path == "ghost.py")
            self.assertTrue(ghost_rec.skipped)
            self.assertIsNone(ghost_rec.line_count)
            self.assertIsNotNone(ghost_rec.skip_reason)
            self.assertTrue(ghost_rec.skip_reason.startswith("unreadable:"))
            self.assertIn("input/output error", ghost_rec.skip_reason)
            self.assertFalse(ghost_rec.reviewed_by_analyzer)


class BuildProjectStructureTests(unittest.TestCase):
    def _record(self, path: str) -> FileRecord:
        return FileRecord(
            path=path,
            extension=Path(path).suffix.lower(),
            size_bytes=10,
            language_guess="text",
            role_guess="source",
            line_count=1,
            source_line_count=1,
            github_url=f"https://github.com/acme/widget/blob/abc1234/{path}",
            reviewed_by_analyzer=True,
            skipped=False,
            skip_reason=None,
        )

    def test_top_level_entries_and_notable_directories(self) -> None:
        records = [
            self._record("src/index.ts"),
            self._record("src/app.ts"),
            self._record("src/util.ts"),
            self._record("docs/readme.md"),
            self._record("package.json"),
            self._record("README.md"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            structure = build_project_structure(Path(tmp), records)

        # top_level_entries is sorted alphabetically.
        self.assertEqual(
            structure["top_level_entries"],
            ["README.md", "docs", "package.json", "src"],
        )

        # Notable directories: sorted by descending file_count, then path.
        # "src" has 3 files, "docs" has 1, root (".") is filtered out.
        dirs = {d["path"]: d["file_count"] for d in structure["notable_directories"]}
        self.assertEqual(dirs.get("src"), 3)
        self.assertEqual(dirs.get("docs"), 1)
        self.assertNotIn(".", dirs)
        self.assertNotIn("", dirs)
        # Capped at 25 — 2 records, well under cap.
        self.assertLessEqual(len(structure["notable_directories"]), 25)

    def test_reading_order_prefers_canonical_entry_points(self) -> None:
        records = [
            self._record("package.json"),
            self._record("src/index.ts"),
            self._record("lib/util.ts"),
            self._record("README.md"),
            self._record("Dockerfile"),
            self._record("build.gradle"),
            self._record("pyproject.toml"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            structure = build_project_structure(Path(tmp), records)

        order = structure["reading_order"]
        # Canonical reading order is: README.md, src/* (any subpath of
        # "src"), app, lib, package.json, pyproject.toml, pom.xml,
        # build.gradle, Dockerfile. Files in the candidate list that are
        # subdirs add the first matching record's *path* (so "src" adds
        # "src/index.ts", not "src").
        self.assertIn("README.md", order)
        self.assertIn("src/index.ts", order)
        self.assertIn("lib/util.ts", order)
        self.assertIn("package.json", order)
        self.assertIn("pyproject.toml", order)
        self.assertIn("build.gradle", order)
        self.assertIn("Dockerfile", order)
        # Reading order should be deterministic, no duplicates.
        self.assertEqual(len(order), len(set(order)))
        # README.md must come before everything else in canonical order.
        self.assertEqual(order.index("README.md"), 0)


if __name__ == "__main__":
    unittest.main()
