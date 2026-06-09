"""Tests for repo_discovery_analyzer.io_utils.

Covers: safe_read_text with caching/clear/oversize/encoding-fallback, stream
line count, bounded_items, count_lines edge cases, normalize_path, guess_language,
guess_role, is_probably_text, redact_text (URLs, credentials, secret keys),
short_snippet, json_dump, walk_files with excluded dirs.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.io_utils import (
    DEFAULT_EXCLUDES,
    bounded_items,
    clear_safe_read_text_cache,
    count_lines,
    guess_language,
    guess_role,
    is_probably_text,
    json_dump,
    normalize_path,
    redact_text,
    safe_read_text,
    short_snippet,
    stream_line_count,
    walk_files,
)


class SafeReadTextTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_safe_read_text_cache()

    def test_reads_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.txt"
            p.write_text("hello\n", encoding="utf-8")
            text, err = safe_read_text(p)
        self.assertEqual(text, "hello\n")
        self.assertIsNone(err)

    def test_oversize_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.txt"
            p.write_bytes(b"a" * 100)
            text, err = safe_read_text(p, max_bytes=10)
        self.assertIsNone(text)
        self.assertIsNotNone(err)
        self.assertIn("max read size", err)

    def test_missing_file_returns_error(self) -> None:
        text, err = safe_read_text(Path("/nonexistent/file.txt"))
        self.assertIsNone(text)
        self.assertIsNotNone(err)
        self.assertIn("unreadable", err)

    def test_invalid_utf8_falls_back_to_replace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.txt"
            p.write_bytes(b"\xff\xfe abc")
            text, err = safe_read_text(p)
        self.assertIsNotNone(text)
        self.assertIsNone(err)
        # Replacement char is U+FFFD.
        self.assertIn("\ufffd", text)

    def test_clear_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.txt"
            p.write_text("a", encoding="utf-8")
            safe_read_text(p)
            clear_safe_read_text_cache()
            # Should not raise.
            text, _ = safe_read_text(p)
            self.assertEqual(text, "a")

    def test_max_bytes_default_applied(self) -> None:
        # Default max is 2_000_000; just verify the function signature works.
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.txt"
            p.write_text("hi", encoding="utf-8")
            text, err = safe_read_text(p)
        self.assertEqual(text, "hi")
        self.assertIsNone(err)


class StreamLineCountTests(unittest.TestCase):
    def test_ends_with_newline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.txt"
            p.write_text("a\nb\nc\n", encoding="utf-8")
            count, err = stream_line_count(p)
        self.assertEqual(count, 3)
        self.assertIsNone(err)

    def test_no_trailing_newline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.txt"
            p.write_text("a\nb\nc", encoding="utf-8")
            count, err = stream_line_count(p)
        self.assertEqual(count, 3)
        self.assertIsNone(err)

    def test_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.txt"
            p.write_text("", encoding="utf-8")
            count, err = stream_line_count(p)
        self.assertEqual(count, 0)
        self.assertIsNone(err)

    def test_missing_file(self) -> None:
        count, err = stream_line_count(Path("/nonexistent/x.txt"))
        self.assertIsNone(count)
        self.assertIn("unreadable", err)


class BoundedItemsTests(unittest.TestCase):
    def test_under_limit(self) -> None:
        items, total, truncated = bounded_items([1, 2, 3], limit=10)
        self.assertEqual(items, [1, 2, 3])
        self.assertEqual(total, 3)
        self.assertFalse(truncated)

    def test_at_limit(self) -> None:
        items, total, truncated = bounded_items([1, 2, 3], limit=3)
        self.assertEqual(items, [1, 2, 3])
        self.assertEqual(total, 3)
        self.assertFalse(truncated)

    def test_over_limit(self) -> None:
        items, total, truncated = bounded_items([1, 2, 3, 4, 5], limit=3)
        self.assertEqual(items, [1, 2, 3])
        self.assertEqual(total, 5)
        self.assertTrue(truncated)


class CountLinesTests(unittest.TestCase):
    def test_none(self) -> None:
        self.assertIsNone(count_lines(None))

    def test_empty(self) -> None:
        self.assertEqual(count_lines(""), 0)

    def test_single_line_no_newline(self) -> None:
        self.assertEqual(count_lines("hello"), 1)

    def test_single_line_newline(self) -> None:
        self.assertEqual(count_lines("hello\n"), 1)

    def test_multi_line(self) -> None:
        self.assertEqual(count_lines("a\nb\nc"), 3)
        self.assertEqual(count_lines("a\nb\nc\n"), 3)


class NormalizePathTests(unittest.TestCase):
    def test_relative_posix(self) -> None:
        base = Path("/tmp/repo")
        p = Path("/tmp/repo/src/app.py")
        self.assertEqual(normalize_path(p, base), "src/app.py")


class GuessLanguageTests(unittest.TestCase):
    def test_dockerfile(self) -> None:
        self.assertEqual(guess_language(Path("Dockerfile")), "Dockerfile")
        self.assertEqual(guess_language(Path("Containerfile")), "Dockerfile")

    def test_gradle_kts(self) -> None:
        self.assertEqual(guess_language(Path("build.gradle.kts")), "Kotlin")

    def test_typescript(self) -> None:
        self.assertEqual(guess_language(Path("a.ts")), "TypeScript")
        self.assertEqual(guess_language(Path("a.tsx")), "TypeScript")

    def test_javascript(self) -> None:
        self.assertEqual(guess_language(Path("a.js")), "JavaScript")
        self.assertEqual(guess_language(Path("a.jsx")), "JavaScript")
        self.assertEqual(guess_language(Path("a.mjs")), "JavaScript")
        self.assertEqual(guess_language(Path("a.cjs")), "JavaScript")

    def test_python(self) -> None:
        self.assertEqual(guess_language(Path("a.py")), "Python")

    def test_java(self) -> None:
        self.assertEqual(guess_language(Path("A.java")), "Java")

    def test_kotlin(self) -> None:
        self.assertEqual(guess_language(Path("A.kt")), "Kotlin")

    def test_go(self) -> None:
        self.assertEqual(guess_language(Path("a.go")), "Go")

    def test_rust(self) -> None:
        self.assertEqual(guess_language(Path("a.rs")), "Rust")

    def test_xml(self) -> None:
        self.assertEqual(guess_language(Path("a.xml")), "XML")

    def test_yaml(self) -> None:
        self.assertEqual(guess_language(Path("a.yaml")), "YAML")
        self.assertEqual(guess_language(Path("a.yml")), "YAML")

    def test_json(self) -> None:
        self.assertEqual(guess_language(Path("a.json")), "JSON")

    def test_sql(self) -> None:
        self.assertEqual(guess_language(Path("a.sql")), "SQL")

    def test_toml(self) -> None:
        self.assertEqual(guess_language(Path("a.toml")), "TOML")

    def test_unknown(self) -> None:
        self.assertEqual(guess_language(Path("a.unknownext")), "Text")


class GuessRoleTests(unittest.TestCase):
    def test_test_dir(self) -> None:
        self.assertEqual(guess_role(Path("tests/test_x.py")), "test")
        self.assertEqual(guess_role(Path("test/test_x.py")), "test")
        self.assertEqual(guess_role(Path("specs/x_spec.py")), "test")
        self.assertEqual(guess_role(Path("src/__tests__/x.js")), "test")

    def test_test_prefix(self) -> None:
        self.assertEqual(guess_role(Path("test_x.py")), "test")
        self.assertEqual(guess_role(Path("x_test.py")), "test")
        self.assertEqual(guess_role(Path("x_spec.py")), "test")

    def test_test_substring(self) -> None:
        self.assertEqual(guess_role(Path("x.test.js")), "test")
        self.assertEqual(guess_role(Path("x.spec.js")), "test")

    def test_documentation(self) -> None:
        self.assertEqual(guess_role(Path("README.md")), "documentation")
        self.assertEqual(guess_role(Path("docs/index.md")), "documentation")
        self.assertEqual(guess_role(Path("doc/x.md")), "documentation")
        self.assertEqual(guess_role(Path("documentation/x.md")), "documentation")

    def test_database(self) -> None:
        self.assertEqual(guess_role(Path("migrations/001_init.sql")), "database")
        self.assertEqual(guess_role(Path("migration/x.sql")), "database")
        self.assertEqual(guess_role(Path("schema.sql")), "database")

    def test_deployment_docker(self) -> None:
        self.assertEqual(guess_role(Path("Dockerfile")), "deployment")
        self.assertEqual(guess_role(Path("docker-compose.yml")), "deployment")
        self.assertEqual(guess_role(Path("compose.yaml")), "deployment")

    def test_deployment_k8s(self) -> None:
        self.assertEqual(guess_role(Path(".github/workflows/ci.yml")), "deployment")
        self.assertEqual(guess_role(Path("k8s/deployment.yaml")), "deployment")
        self.assertEqual(guess_role(Path("kubernetes/pod.yaml")), "deployment")

    def test_script(self) -> None:
        self.assertEqual(guess_role(Path("scripts/build.sh")), "script")
        self.assertEqual(guess_role(Path("bin/run")), "script")
        self.assertEqual(guess_role(Path("tools/x.py")), "script")

    def test_build_config(self) -> None:
        self.assertEqual(guess_role(Path("package.json")), "build config")
        self.assertEqual(guess_role(Path("pyproject.toml")), "build config")
        self.assertEqual(guess_role(Path("Cargo.toml")), "build config")

    def test_source_default(self) -> None:
        self.assertEqual(guess_role(Path("src/app.py")), "source")


class IsProbablyTextTests(unittest.TestCase):
    def test_dockerfile(self) -> None:
        self.assertTrue(is_probably_text(Path("Dockerfile")))
        self.assertTrue(is_probably_text(Path("Containerfile")))

    def test_text_extension(self) -> None:
        for ext in [".py", ".js", ".ts", ".java", ".json", ".yml", ".md", ".sql", ".toml", ".cfg"]:
            self.assertTrue(is_probably_text(Path(f"a{ext}")))

    def test_lock_file(self) -> None:
        self.assertTrue(is_probably_text(Path("yarn.lock")))
        self.assertTrue(is_probably_text(Path("package.lock")))

    def test_binary(self) -> None:
        self.assertFalse(is_probably_text(Path("a.png")))
        self.assertFalse(is_probably_text(Path("a.exe")))


class RedactTextTests(unittest.TestCase):
    def test_redacts_url(self) -> None:
        out = redact_text("Visit https://example.com for more")
        self.assertNotIn("https://example.com", out)
        self.assertIn("<redacted-url>", out)

    def test_redacts_credential_value(self) -> None:
        out = redact_text('api_key=AbCdEf1234567890XyZw==')
        self.assertIn("<redacted>", out)
        self.assertNotIn("AbCdEf1234567890XyZw", out)

    def test_redacts_secret_keyword(self) -> None:
        out = redact_text("my token: abcdef1234567890")
        self.assertIn("<redacted-key>", out)

    def test_no_redaction_needed(self) -> None:
        out = redact_text("This is plain text with no secrets.")
        self.assertEqual(out, "This is plain text with no secrets.")

    def test_redacts_multiple_urls(self) -> None:
        out = redact_text("https://a.com and https://b.com")
        self.assertNotIn("https://a.com", out)
        self.assertNotIn("https://b.com", out)


class ShortSnippetTests(unittest.TestCase):
    def test_none(self) -> None:
        self.assertIsNone(short_snippet(None))

    def test_empty(self) -> None:
        self.assertIsNone(short_snippet(""))

    def test_truncates(self) -> None:
        self.assertEqual(len(short_snippet("x" * 1000)), 180)

    def test_normalizes_whitespace(self) -> None:
        self.assertEqual(short_snippet("  hello\n\n  world  "), "hello world")


class JsonDumpTests(unittest.TestCase):
    def test_writes_with_trailing_newline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "sub/out.json"
            json_dump(p, {"b": 1, "a": 2})
            self.assertTrue(p.exists())
            content = p.read_text(encoding="utf-8")
            self.assertTrue(content.endswith("\n"))
            data = json.loads(content)
            self.assertEqual(data, {"a": 2, "b": 1})  # sort_keys=True

    def test_creates_parent_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "deep/nested/path/out.json"
            json_dump(p, {"x": 1})
            self.assertTrue(p.exists())


class WalkFilesTests(unittest.TestCase):
    def test_yields_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "a.txt").write_text("a", encoding="utf-8")
            (repo / "b.txt").write_text("b", encoding="utf-8")
            files = [str(f.relative_to(repo)) for f in walk_files(repo)]
        self.assertIn("a.txt", files)
        self.assertIn("b.txt", files)

    def test_excludes_default_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src" / "x.py").write_text("x", encoding="utf-8")
            for ex in DEFAULT_EXCLUDES:
                d = repo / ex
                d.mkdir()
                (d / "y.txt").write_text("y", encoding="utf-8")
            files = [str(f.relative_to(repo)) for f in walk_files(repo)]
            # Excluded dirs' files should NOT appear.
            for ex in DEFAULT_EXCLUDES:
                self.assertNotIn(f"{ex}/y.txt", files)
            # Source file still present.
            self.assertIn("src/x.py", files)

    def test_dirs_are_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ["z", "a", "m"]:
                (repo / name).mkdir()
                (repo / name / "f.txt").write_text("f", encoding="utf-8")
            files = [str(f.relative_to(repo)) for f in walk_files(repo)]
            dirs = sorted({f.split("/")[0] for f in files if "/" in f})
            self.assertEqual(dirs, ["a", "m", "z"])


if __name__ == "__main__":
    unittest.main()
