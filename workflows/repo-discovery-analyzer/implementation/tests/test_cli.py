from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.cli import REQUIRED_OUTPUTS, _merge_sorted, main


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


class MergeSortedDedupTests(unittest.TestCase):
    """Regression tests for _merge_sorted dedup behaviour.

    On johrenberger/BroadleafCommerce, the previous dedup-by-full-JSON
    behaviour produced 109 files that emitted TWO `db_schema.json`
    entries — one from `detect_database_schema` and one from
    `detect_java_spring_routes` — because the two detectors compute
    `relationships` differently for the same file. The full-JSON key
    treated them as distinct records, so neither was collapsed.

    The fix introduces a `key_fields` parameter so the caller can pick
    the identity tuple. These tests pin both modes.
    """

    def test_dedup_by_full_json_default(self) -> None:
        """Without key_fields, the previous behaviour is preserved: only
        entries that are byte-identical collapse."""
        items = [
            {"source_file": "Foo.java", "name": "Foo", "relationships": ["@OneToMany"]},
            {"source_file": "Foo.java", "name": "Foo", "relationships": ["@OneToMany", "@ManyToOne"]},
        ]
        out = _merge_sorted(items)
        # Two distinct entries (different `relationships` arrays)
        self.assertEqual(len(out), 2)

    def test_dedup_by_key_fields_collapses_same_file_name(self) -> None:
        """With key_fields=['source_file', 'name'], two records for the
        same file and class name collapse regardless of other fields."""
        items = [
            {"source_file": "Foo.java", "name": "Foo", "relationships": ["@OneToMany"]},
            {"source_file": "Foo.java", "name": "Foo", "relationships": ["@OneToMany", "@ManyToOne"]},
        ]
        out = _merge_sorted(items, key_fields=["source_file", "name"])
        self.assertEqual(len(out), 1)
        # First occurrence wins
        self.assertEqual(out[0]["relationships"], ["@OneToMany"])

    def test_dedup_keeps_distinct_entries(self) -> None:
        items = [
            {"source_file": "Foo.java", "name": "Foo"},
            {"source_file": "Bar.java", "name": "Foo"},
            {"source_file": "Foo.java", "name": "Bar"},
        ]
        out = _merge_sorted(items, key_fields=["source_file", "name"])
        self.assertEqual(len(out), 3)

    def test_dedup_routes_by_source_method_path(self) -> None:
        """Routes use (source_file, method, path) as the identity tuple
        because a controller can have multiple methods but each method
        has a unique (method, path) pair within its file."""
        items = [
            {"source_file": "FooCtrl.java", "method": "GET", "path": "/foo", "handler": "FooCtrl"},
            {"source_file": "FooCtrl.java", "method": "GET", "path": "/foo", "handler": "OldName"},
            {"source_file": "FooCtrl.java", "method": "POST", "path": "/foo", "handler": "FooCtrl"},
        ]
        out = _merge_sorted(items, key_fields=["source_file", "method", "path"])
        self.assertEqual(len(out), 2)
        # First occurrence of each (method, path) wins.
        paths = {(r["method"], r["path"]): r["handler"] for r in out}
        self.assertEqual(paths[("GET", "/foo")], "FooCtrl")
        self.assertEqual(paths[("POST", "/foo")], "FooCtrl")

    def test_dedup_handles_missing_key_fields(self) -> None:
        """A record missing a key field produces a None in the tuple;
        the function should not raise and should still dedup correctly
        by the remaining fields."""
        items = [
            {"source_file": "Foo.java", "name": "Foo"},
            {"source_file": "Foo.java"},  # missing 'name'
        ]
        out = _merge_sorted(items, key_fields=["source_file", "name"])
        self.assertEqual(len(out), 2)


if __name__ == "__main__":
    unittest.main()
