"""Tests for repo_discovery_analyzer.detectors.entry_points.

The detector reads file contents from disk via safe_read_text, so each
test writes real files into a temp dir before invoking the detector.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.detectors.entry_points import detect_entry_points
from repo_discovery_analyzer.model import FileRecord


def _record(path: str) -> FileRecord:
    return FileRecord(
        path=path,
        extension=Path(path).suffix.lower(),
        size_bytes=0,  # detector ignores this
        language_guess="text",
        role_guess="source",
        line_count=None,
        source_line_count=None,
        github_url=f"https://github.com/acme/widget/blob/abc1234/{path}",
        reviewed_by_analyzer=True,
        skipped=False,
        skip_reason=None,
    )


def _write(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class EntryPointsTests(unittest.TestCase):
    def test_java_main_method(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/main/java/Foo.java", "public class Foo { public static void main(String[] args) {} }\n")
            records = [_record("src/main/java/Foo.java")]
            result = detect_entry_points(repo, "acme", "widget", "abc1234", records)
        kinds = [e["type"] for e in result["entry_points"]]
        self.assertIn("java-main", kinds)
        entry = next(e for e in result["entry_points"] if e["type"] == "java-main")
        self.assertEqual(entry["path"], "src/main/java/Foo.java")
        self.assertEqual(entry["framework"], "Java")
        self.assertEqual(entry["confidence"], "high")

    def test_spring_boot_application(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/main/java/App.java", "@SpringBootApplication\npublic class App {}\n")
            records = [_record("src/main/java/App.java")]
            result = detect_entry_points(repo, "acme", "widget", "abc1234", records)
        kinds = [e["type"] for e in result["entry_points"]]
        self.assertIn("spring-boot-app", kinds)

    def test_python_entry_by_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "app.py", "print('hi')\n")
            records = [_record("app.py")]
            result = detect_entry_points(repo, "acme", "widget", "abc1234", records)
        kinds = [e["type"] for e in result["entry_points"]]
        self.assertIn("python-entry", kinds)

    def test_python_entry_by_main_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            text = 'if __name__ == "__main__":\n    main()\n'
            _write(repo, "scripts/run_thing.py", text)
            records = [_record("scripts/run_thing.py")]
            result = detect_entry_points(repo, "acme", "widget", "abc1234", records)
        kinds = [e["type"] for e in result["entry_points"]]
        self.assertIn("python-entry", kinds)

    def test_frontend_index_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for rel in ("src/index.ts", "web/index.tsx", "legacy/index.js", "pages/index.jsx"):
                _write(repo, rel, "export {};\n")
            records = [_record(rel) for rel in ("src/index.ts", "web/index.tsx", "legacy/index.js", "pages/index.jsx")]
            result = detect_entry_points(repo, "acme", "widget", "abc1234", records)
        kinds = [e["type"] for e in result["entry_points"]]
        self.assertEqual(kinds.count("frontend-entry"), 4)

    def test_node_server_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for rel in ("server.js", "src/server.ts", "src/app.js", "src/app.ts"):
                _write(repo, rel, "const x = 1;\n")
            records = [_record(rel) for rel in ("server.js", "src/server.ts", "src/app.js", "src/app.ts")]
            result = detect_entry_points(repo, "acme", "widget", "abc1234", records)
        kinds = [e["type"] for e in result["entry_points"]]
        self.assertEqual(kinds.count("server-entry"), 4)

    def test_package_json_scripts_are_picked_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(
                repo,
                "package.json",
                '{\n'
                '  "scripts": {\n'
                '    "start": "node server.js",\n'
                '    "dev": "vite",\n'
                '    "build": "tsc -b",\n'
                '    "lint": "eslint ."\n'
                '  }\n'
                '}\n',
            )
            records = [_record("package.json")]
            result = detect_entry_points(repo, "acme", "widget", "abc1234", records)
        scripts = [e for e in result["entry_points"] if e["type"] == "script"]
        self.assertEqual(len(scripts), 3)
        for entry in scripts:
            self.assertEqual(entry["path"], "package.json")
            self.assertTrue(
                (entry.get("github_url") or "").endswith("/blob/abc1234/package.json")
            )
        handlers = " | ".join(e["handler"] for e in scripts)
        self.assertIn('"start"', handlers)
        self.assertIn('"dev"', handlers)
        self.assertIn('"build"', handlers)

    def test_package_json_without_keywords_emits_no_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "package.json", '{\n  "name": "widget",\n  "version": "1.0.0"\n}\n')
            records = [_record("package.json")]
            result = detect_entry_points(repo, "acme", "widget", "abc1234", records)
        scripts = [e for e in result["entry_points"] if e["type"] == "script"]
        self.assertEqual(scripts, [])

    def test_package_json_present_but_record_missing_in_files_dict(self) -> None:
        # package.json exists on disk but is NOT in records (maybe filtered
        # out earlier). The detector still walks package.json and emits
        # script entries, with a null github_url.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "package.json", '{\n  "scripts": { "start": "node index.js" }\n}\n')
            result = detect_entry_points(repo, "acme", "widget", "abc1234", [])
        scripts = [e for e in result["entry_points"] if e["type"] == "script"]
        self.assertEqual(len(scripts), 1)
        self.assertIsNone(scripts[0]["github_url"])

    def test_no_files_yields_empty_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = detect_entry_points(Path(tmp), "acme", "widget", "abc1234", [])
        self.assertEqual(result["entry_points"], [])


if __name__ == "__main__":
    unittest.main()
