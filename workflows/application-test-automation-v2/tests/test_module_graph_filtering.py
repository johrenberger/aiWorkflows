"""Tests for module_graph filtering (Bug #13 fix)."""
from test_factory.orchestrator import _module_graph


def test_module_graph_excludes_excluded_files():
    """Bug #13: module_graph should skip is_excluded=True files so that
    artifacts from previous runs (e.g. .openclaw/analyzer-output) don't
    pollute the module graph."""
    files = [
        {"path": "src/main/java/Foo.java", "language": "java", "module": "src", "is_excluded": False},
        {"path": ".openclaw/analyzer-output/foo.json", "language": "unknown", "module": ".openclaw/analyzer-output", "is_excluded": True},
        {"path": ".openclaw/app-dev-discovery/bar.md", "language": "unknown", "module": ".openclaw/app-dev-discovery", "is_excluded": True},
    ]
    graph = _module_graph(files)
    # Only the non-excluded file should appear
    assert ".openclaw/analyzer-output" not in graph
    assert ".openclaw/app-dev-discovery" not in graph
    assert "src" in graph
    assert graph["src"] == {"java": 1}


def test_module_graph_includes_legitimate_files():
    """Non-excluded files of various languages should be in the graph."""
    files = [
        {"path": "src/main/java/Foo.java", "language": "java", "module": "src", "is_excluded": False},
        {"path": "src/main/resources/foo.js", "language": "javascript", "module": "src", "is_excluded": False},
        {"path": "tests/test_foo.py", "language": "python", "module": "tests", "is_excluded": False},
    ]
    graph = _module_graph(files)
    assert "src" in graph
    assert "tests" in graph
    assert graph["src"] == {"java": 1, "javascript": 1}
    assert graph["tests"] == {"python": 1}


def test_module_graph_empty_when_all_excluded():
    """All-excluded input should produce empty graph."""
    files = [
        {"path": "x.json", "language": "unknown", "module": "x", "is_excluded": True},
    ]
    assert _module_graph(files) == {}
