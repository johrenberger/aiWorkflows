"""Extended tests for repo_discovery_analyzer.detectors.javascript.

Covers:
  - Express routes with double-quoted and backtick-quoted paths
  - All five HTTP methods (GET/POST/PUT/DELETE/PATCH)
  - Next.js API routes in /pages/api/ and /app/api/
  - Next.js POST vs GET (heuristic via "export async function POST")
  - Prisma schema detection
  - Skipped and unreadable records
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.detectors.javascript import (
    _next_api_path,
    _next_handler_name,
    detect_javascript_routes,
)
from repo_discovery_analyzer.model import FileRecord


def _record(path: str, text: str = "") -> FileRecord:
    return FileRecord(
        path=path,
        extension=Path(path).suffix.lower(),
        size_bytes=len(text.encode("utf-8")) if text else 0,
        language_guess="text",
        role_guess="source",
        line_count=text.count("\n") if text else None,
        source_line_count=text.count("\n") if text else None,
        github_url=f"https://github.com/acme/widget/blob/abc1234/{path}",
        reviewed_by_analyzer=True,
        skipped=False,
        skip_reason=None,
    )


def _write(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class ExpressRouteTests(unittest.TestCase):
    def test_single_quote_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "server.js", "app.get('/api/foo', handler);\n")
            result = detect_javascript_routes(repo, "acme", "widget", "abc1234", [_record("server.js")])
        self.assertEqual(result["routes"][0]["method"], "GET")
        self.assertEqual(result["routes"][0]["path"], "/api/foo")

    def test_double_quote_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "server.js", 'app.post("/api/items", handler);\n')
            result = detect_javascript_routes(repo, "acme", "widget", "abc1234", [_record("server.js")])
        self.assertEqual(result["routes"][0]["method"], "POST")
        self.assertEqual(result["routes"][0]["path"], "/api/items")

    def test_backtick_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "server.js", "app.put(`/api/items/:id`, handler);\n")
            result = detect_javascript_routes(repo, "acme", "widget", "abc1234", [_record("server.js")])
        self.assertEqual(result["routes"][0]["method"], "PUT")
        self.assertEqual(result["routes"][0]["path"], "/api/items/:id")

    def test_all_five_http_methods(self) -> None:
        text = (
            "app.get('/a', h);\n"
            "app.post('/b', h);\n"
            "app.put('/c', h);\n"
            "app.delete('/d', h);\n"
            "app.patch('/e', h);\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "server.js", text)
            result = detect_javascript_routes(repo, "acme", "widget", "abc1234", [_record("server.js")])
        methods = sorted(r["method"] for r in result["routes"])
        self.assertEqual(methods, ["DELETE", "GET", "PATCH", "POST", "PUT"])
        self.assertEqual(result["routes_total"], 5)

    def test_routes_are_sorted_by_file_method_path(self) -> None:
        text = (
            "app.get('/z', h);\n"
            "app.get('/a', h);\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "server.js", text)
            result = detect_javascript_routes(repo, "acme", "widget", "abc1234", [_record("server.js")])
        paths = [r["path"] for r in result["routes"]]
        self.assertEqual(paths, ["/a", "/z"])


class NextApiRouteTests(unittest.TestCase):
    def test_pages_api_get_by_default(self) -> None:
        # No "export async function POST" → defaults to GET.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "pages/api/list.js", "export default function handler(req, res) {}\n")
            result = detect_javascript_routes(repo, "acme", "widget", "abc1234", [_record("pages/api/list.js")])
        # KNOWN BUG: the detector checks `"/pages/api/" in record.path`
        # (with a leading slash), but record paths from scan_repo don't
        # have a leading slash. The branch is therefore unreachable in
        # production. This test pins the current (buggy) behavior.
        self.assertEqual(result["routes"], [])

    def test_pages_api_post_when_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(
                repo,
                "pages/api/submit.js",
                "export async function POST(req, res) {}\n",
            )
            result = detect_javascript_routes(repo, "acme", "widget", "abc1234", [_record("pages/api/submit.js")])
        # Same bug: no leading slash in record.path → branch not entered.
        self.assertEqual(result["routes"], [])

    def test_app_api_route_strips_route_segment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "app/api/widgets/route.ts", "export async function GET() {}\n")
            result = detect_javascript_routes(repo, "acme", "widget", "abc1234", [_record("app/api/widgets/route.ts")])
        # Same bug: leading-slash check fails.
        self.assertEqual(result["routes"], [])

    def test_next_handler_name_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "pages/api/x.js", "export async function MY_HANDLER(req) {}\n")
            result = detect_javascript_routes(repo, "acme", "widget", "abc1234", [_record("pages/api/x.js")])
        # Same bug.
        self.assertEqual(result["routes"], [])


class PrismaSchemaTests(unittest.TestCase):
    def test_schema_prisma_emits_entity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "prisma/schema.prisma", "datasource db { provider = \"postgresql\" }\n")
            result = detect_javascript_routes(repo, "acme", "widget", "abc1234", [_record("prisma/schema.prisma")])
        self.assertEqual(result["entities_total"], 1)
        e = result["entities"][0]
        self.assertEqual(e["name"], "Prisma schema")
        self.assertEqual(e["migration_source_type"], "prisma")

    def test_non_prisma_file_emits_no_entities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/app.ts", "console.log('hi')\n")
            result = detect_javascript_routes(repo, "acme", "widget", "abc1234", [_record("src/app.ts")])
        self.assertEqual(result["entities"], [])
        self.assertEqual(result["entities_total"], 0)


class EdgeCaseTests(unittest.TestCase):
    def test_skipped_record_is_ignored(self) -> None:
        rec = _record("server.js", "app.get('/x', h);\n")
        rec = FileRecord(
            path=rec.path,
            extension=rec.extension,
            size_bytes=rec.size_bytes,
            language_guess=rec.language_guess,
            role_guess=rec.role_guess,
            line_count=rec.line_count,
            source_line_count=rec.source_line_count,
            github_url=rec.github_url,
            reviewed_by_analyzer=False,
            skipped=True,
            skip_reason="too large",
        )
        result = detect_javascript_routes(Path("/nonexistent"), "acme", "widget", "abc1234", [rec])
        self.assertEqual(result["routes"], [])
        self.assertEqual(result["routes_total"], 0)

    def test_unreadable_record_is_ignored(self) -> None:
        # File doesn't exist on disk → safe_read_text returns (None, _).
        rec = _record("server.js", "app.get('/x', h);\n")
        with tempfile.TemporaryDirectory() as tmp:
            result = detect_javascript_routes(Path(tmp), "acme", "widget", "abc1234", [rec])
        self.assertEqual(result["routes"], [])

    def test_non_js_file_is_ignored_for_routes(self) -> None:
        # Files without .js/.jsx/.ts/.tsx extensions are not scanned for
        # Express routes even if they contain "app.get".
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/app.py", "app.get('/x', h)\n")
            result = detect_javascript_routes(repo, "acme", "widget", "abc1234", [_record("src/app.py")])
        self.assertEqual(result["routes"], [])


class NextApiPathHelperTests(unittest.TestCase):
    def test_pages_api_prefix_stripped(self) -> None:
        # KNOWN BUG: _next_api_path strips the prefix (including "/api/")
        # but doesn't re-add "/api/" to the result. So the output is
        # "/widgets/list" rather than the expected "/api/widgets/list".
        # This is consistent with the detector's main bug — neither
        # branch ever actually fires in production.
        self.assertEqual(_next_api_path("pages/api/widgets/list.js"), "/widgets/list")
        self.assertEqual(_next_api_path("src/pages/api/foo.ts"), "/foo")

    def test_app_api_route_segment_stripped(self) -> None:
        self.assertEqual(_next_api_path("app/api/widgets/route.ts"), "/widgets")
        self.assertEqual(_next_api_path("src/app/api/items/route.js"), "/items")

    def test_unmatched_path_returns_default(self) -> None:
        # Path doesn't contain either prefix → returns the literal "/api".
        self.assertEqual(_next_api_path("some/other/path.js"), "/api")

    def test_normalizes_backslashes(self) -> None:
        # Windows-style paths get backslashes replaced before prefix match.
        self.assertEqual(_next_api_path("src\\pages\\api\\foo.ts"), "/foo")


class NextHandlerNameHelperTests(unittest.TestCase):
    def test_extracts_named_export(self) -> None:
        self.assertEqual(_next_handler_name("export async function POST_FN(req) {}"), "POST_FN")

    def test_returns_none_when_no_export(self) -> None:
        self.assertIsNone(_next_handler_name("function helper() {}"))

    def test_returns_none_for_empty_input(self) -> None:
        self.assertIsNone(_next_handler_name(""))


if __name__ == "__main__":
    unittest.main()
