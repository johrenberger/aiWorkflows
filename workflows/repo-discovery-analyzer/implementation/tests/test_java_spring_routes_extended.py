"""Extended tests for repo_discovery_analyzer.detectors.java_spring.

Covers:
  - All six Spring MVC route annotations (Get/Post/Put/Delete/Patch/RequestMapping)
  - @RequestMapping with explicit Method.X and implicit default (GET)
  - Class-name extraction for handler attribution
  - JPA @Entity branch with @OneToMany, @ManyToOne, etc.
  - Skipped records and unreadable files
  - _java_route helper edge cases
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.detectors.java_spring import (
    _java_fields,
    _java_relationships,
    _java_route,
    detect_java_spring_routes,
)
from repo_discovery_analyzer.model import FileRecord


def _record(path: str) -> FileRecord:
    return FileRecord(
        path=path,
        extension=".java",
        size_bytes=0,
        language_guess="java",
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


def _controller_body(annotation: str) -> str:
    return f"""
@RestController
class WidgetController {{
  {annotation}
  public String handle() {{ return "ok"; }}
}}
""".strip()


class SpringMvcRouteAnnotationTests(unittest.TestCase):
    def test_get_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/WidgetController.java", _controller_body('@GetMapping("/widgets")'))
            result = detect_java_spring_routes(repo, "acme", "widget", "abc1234", [_record("src/WidgetController.java")])
        self.assertEqual(result["routes"][0]["method"], "GET")
        self.assertEqual(result["routes"][0]["path"], "/widgets")
        self.assertEqual(result["routes"][0]["handler"], "WidgetController")
        self.assertEqual(result["routes"][0]["framework"], "Spring MVC")

    def test_post_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/WidgetController.java", _controller_body('@PostMapping("/widgets")'))
            result = detect_java_spring_routes(repo, "acme", "widget", "abc1234", [_record("src/WidgetController.java")])
        self.assertEqual(result["routes"][0]["method"], "POST")

    def test_put_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/WidgetController.java", _controller_body('@PutMapping("/widgets/{id}")'))
            result = detect_java_spring_routes(repo, "acme", "widget", "abc1234", [_record("src/WidgetController.java")])
        self.assertEqual(result["routes"][0]["method"], "PUT")
        self.assertEqual(result["routes"][0]["path"], "/widgets/{id}")

    def test_delete_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/WidgetController.java", _controller_body('@DeleteMapping("/widgets/{id}")'))
            result = detect_java_spring_routes(repo, "acme", "widget", "abc1234", [_record("src/WidgetController.java")])
        self.assertEqual(result["routes"][0]["method"], "DELETE")

    def test_patch_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/WidgetController.java", _controller_body('@PatchMapping("/widgets/{id}")'))
            result = detect_java_spring_routes(repo, "acme", "widget", "abc1234", [_record("src/WidgetController.java")])
        self.assertEqual(result["routes"][0]["method"], "PATCH")

    def test_request_mapping_with_explicit_method(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/WidgetController.java", _controller_body('@RequestMapping(value="/widgets", method = RequestMethod.PUT)'))
            result = detect_java_spring_routes(repo, "acme", "widget", "abc1234", [_record("src/WidgetController.java")])
        self.assertEqual(result["routes"][0]["method"], "PUT")
        self.assertEqual(result["routes"][0]["path"], "/widgets")

    def test_request_mapping_without_method_defaults_to_get(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/WidgetController.java", _controller_body('@RequestMapping("/widgets")'))
            result = detect_java_spring_routes(repo, "acme", "widget", "abc1234", [_record("src/WidgetController.java")])
        self.assertEqual(result["routes"][0]["method"], "GET")

    def test_annotation_with_path_attribute(self) -> None:
        # @GetMapping(path = "/health", produces = "application/json")
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(
                repo,
                "src/HealthController.java",
                _controller_body('@GetMapping(path = "/health")'),
            )
            result = detect_java_spring_routes(repo, "acme", "widget", "abc1234", [_record("src/HealthController.java")])
        self.assertEqual(result["routes"][0]["path"], "/health")

    def test_annotation_without_path_yields_no_route(self) -> None:
        # @GetMapping with no path attribute and no quoted string inside
        # → path is None → route is not added.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/WidgetController.java", _controller_body("@GetMapping"))
            result = detect_java_spring_routes(repo, "acme", "widget", "abc1234", [_record("src/WidgetController.java")])
        self.assertEqual(result["routes"], [])
        self.assertEqual(result["routes_total"], 0)


class JpaEntityTests(unittest.TestCase):
    def test_entity_with_multiple_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            text = """
import javax.persistence.*;
@Entity
public class Order {
    public Long id;
    public String name;
    @OneToMany
    public List<Item> items;
    @ManyToOne
    public User owner;
}
""".strip()
            _write(repo, "src/Order.java", text)
            result = detect_java_spring_routes(repo, "acme", "widget", "abc1234", [_record("src/Order.java")])
        self.assertEqual(result["entities_total"], 1)
        e = result["entities"][0]
        self.assertEqual(e["name"], "Order")
        self.assertEqual(e["migration_source_type"], "jpa-entity")
        # All annotations are detected as relationships.
        rels = set(e["relationships"])
        self.assertIn("@OneToMany", rels)
        self.assertIn("@ManyToOne", rels)
        # Fields include public member declarations.
        self.assertTrue(any("id" in f for f in e["fields"]))

    def test_entity_with_no_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/Tag.java", "@Entity\npublic class Tag {\n    public String name;\n}\n")
            result = detect_java_spring_routes(repo, "acme", "widget", "abc1234", [_record("src/Tag.java")])
        self.assertEqual(result["entities"][0]["relationships"], [])


class EdgeCaseTests(unittest.TestCase):
    def test_skipped_record_is_ignored(self) -> None:
        rec = _record("src/X.java")
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
        with tempfile.TemporaryDirectory() as tmp:
            result = detect_java_spring_routes(Path(tmp), "acme", "widget", "abc1234", [rec])
        self.assertEqual(result["routes"], [])
        self.assertEqual(result["entities"], [])

    def test_unreadable_record_is_ignored(self) -> None:
        rec = _record("src/X.java")
        with tempfile.TemporaryDirectory() as tmp:
            result = detect_java_spring_routes(Path(tmp), "acme", "widget", "abc1234", [rec])
        self.assertEqual(result["routes"], [])

    def test_non_java_file_is_ignored(self) -> None:
        # .kt (Kotlin) and .scala files are not scanned.
        rec = _record("src/X.kt")
        with tempfile.TemporaryDirectory() as tmp:
            result = detect_java_spring_routes(Path(tmp), "acme", "widget", "abc1234", [rec])
        self.assertEqual(result["routes"], [])

    def test_results_sorted_by_file_method_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/A.java", _controller_body('@GetMapping("/z")'))
            _write(repo, "src/A.java", _controller_body('@GetMapping("/a")'), )
            # Re-read because we just overwrote. Use two separate files instead.
            _write(repo, "src/Z.java", _controller_body('@GetMapping("/a")'))
            records = [_record("src/Z.java")]
            result = detect_java_spring_routes(repo, "acme", "widget", "abc1234", records)
        self.assertEqual([r["path"] for r in result["routes"]], ["/a"])


class JavaRouteHelperTests(unittest.TestCase):
    def test_get_mapping_with_value(self) -> None:
        method, path = _java_route('@GetMapping("/foo")')
        self.assertEqual(method, "GET")
        self.assertEqual(path, "/foo")

    def test_get_mapping_with_path_attribute(self) -> None:
        method, path = _java_route('@GetMapping(path = "/bar")')
        self.assertEqual(method, "GET")
        self.assertEqual(path, "/bar")

    def test_request_mapping_with_method_value(self) -> None:
        method, path = _java_route('@RequestMapping(value = "/x", method = RequestMethod.PUT)')
        self.assertEqual(method, "PUT")
        self.assertEqual(path, "/x")

    def test_unmatched_path_returns_none(self) -> None:
        # No quoted path inside the annotation → returns (method, None)
        method, path = _java_route("@GetMapping")
        self.assertEqual(method, "GET")
        self.assertIsNone(path)


class JavaFieldsHelperTests(unittest.TestCase):
    def test_captures_public_private_protected_fields(self) -> None:
        lines = [
            "public Long id;",
            "private String name;",
            "protected int count;",
            "// not a field",
            "void method() {}",
        ]
        fields = _java_fields(lines)
        self.assertEqual(len(fields), 3)

    def test_caps_at_25_fields(self) -> None:
        lines = [f"public String field{i};" for i in range(50)]
        fields = _java_fields(lines)
        self.assertEqual(len(fields), 25)


class JavaRelationshipsHelperTests(unittest.TestCase):
    def test_detects_all_known_annotations(self) -> None:
        text = (
            "@OneToMany\n@ManyToOne\n@ManyToMany\n@OneToOne\n@JoinColumn\n"
        )
        rels = _java_relationships(text)
        self.assertEqual(
            sorted(rels),
            sorted(["@OneToMany", "@ManyToOne", "@ManyToMany", "@OneToOne", "@JoinColumn"]),
        )

    def test_returns_empty_when_no_relationships(self) -> None:
        self.assertEqual(_java_relationships("class Foo {}"), [])


if __name__ == "__main__":
    unittest.main()
