"""Regression tests for Bug #9: uncovered_lines empty -> no LLM guidance.

When v2 has no coverage data (e.g. fresh repo, no JaCoCo run), the
work-item spec used to say 'Uncovered lines: none' which is not
actionable for the LLM. Now it falls back to extracting public
method/function signatures from the source file.
"""
import pytest
from pathlib import Path
import tempfile

from test_factory.analyzers.source_signatures import (
    extract_public_signatures,
    _extract_java,
    _extract_python,
    _extract_js_or_groovy,
)
from test_factory.analyzers.risk_scorer import score_file
from test_factory.models import Config, CoverageRecord, SourceTestMapRecord
from test_factory.workitems.generator import generate_work_items
from test_factory.workitems.renderer import render_work_item_markdown


def test_extract_java_public_methods():
    text = '''
public class Foo {
    public void bar() { }
    public String baz(int x) { return null; }
    public static final int CONSTANT = 5;
    private void privateMethod() { }
    public <T> T genericMethod() { return null; }
}
'''
    methods = _extract_java(text)
    assert "bar" in methods
    assert "baz" in methods
    assert "genericMethod" in methods
    assert "privateMethod" not in methods  # private should be excluded
    assert "CONSTANT" not in methods  # constants are not methods


def test_extract_python_top_level_functions():
    text = '''
def public_func():
    pass

def _private_func():
    pass

async def async_func():
    pass

class MyClass:
    def public_method(self):
        pass
    def _private_method(self):
        pass
'''
    sigs = _extract_python(text)
    assert "public_func" in sigs
    assert "async_func" in sigs
    assert "MyClass.public_method" in sigs
    assert "_private_func" not in sigs
    assert "_private_method" not in sigs


def test_extract_js_class_methods():
    text = '''
class MyClass {
    doSomething() { return 1; }
    async fetchData() { return null; }
    static createInstance() { return new MyClass(); }
    if (true) { foo() }
}
'''
    methods = _extract_js_or_groovy(text)
    assert "doSomething" in methods
    assert "fetchData" in methods
    assert "createInstance" in methods
    # 'if' is a keyword and should be filtered
    assert "if" not in methods


def test_workitem_includes_signatures_when_no_coverage(tmp_path):
    """Bug #9: when no coverage data, workitem should list public signatures."""
    # Create a real Java file
    src = tmp_path / "src" / "main" / "java" / "com" / "example"
    src.mkdir(parents=True)
    (src / "Foo.java").write_text('''
public class Foo {
    public void publicMethod() { }
    private void privateMethod() { }
    public String anotherPublic() { return "hi"; }
}
''')
    config = Config()
    score = score_file(
        "src/main/java/com/example/Foo.java", "com/example",
        None,  # NO COVERAGE RECORD (Bug #9 condition)
        complexity=10, public_api_exposure=1
    )
    mapping = {
        "src/main/java/com/example/Foo.java": SourceTestMapRecord(
            source_path="src/main/java/com/example/Foo.java"
        )
    }
    items = generate_work_items(tmp_path, config, [], [score], mapping)
    assert len(items) == 1
    # The workitem should have extracted public signatures
    assert "publicMethod" in items[0].public_signatures
    assert "anotherPublic" in items[0].public_signatures
    # The renderer should display them
    rendered = render_work_item_markdown(items[0], config)
    assert "Public signatures" in rendered
    assert "publicMethod" in rendered
    assert "anotherPublic" in rendered


def test_workitem_signatures_empty_when_coverage_present(tmp_path):
    """When coverage data IS present, public_signatures should be empty
    (we trust the coverage data instead of falling back)."""
    src = tmp_path / "src" / "main" / "java" / "com" / "example"
    src.mkdir(parents=True)
    (src / "Foo.java").write_text("public class Foo { public void bar() { } }")
    config = Config()
    coverage = CoverageRecord(
        path="src/main/java/com/example/Foo.java",
        line_coverage=80.0,
        branch_coverage=70.0,
        uncovered_lines=[42, 43],
    )
    score = score_file(
        "src/main/java/com/example/Foo.java", "com/example",
        coverage, complexity=10, public_api_exposure=1
    )
    mapping = {
        "src/main/java/com/example/Foo.java": SourceTestMapRecord(
            source_path="src/main/java/com/example/Foo.java"
        )
    }
    items = generate_work_items(tmp_path, config, [coverage], [score], mapping)
    # With coverage data, public_signatures should NOT be populated
    assert items[0].public_signatures == []
    rendered = render_work_item_markdown(items[0], config)
    # Should still show 'Uncovered lines: 42, 43' (from coverage)
    assert "42, 43" in rendered
    # And NOT show "Public signatures"
    assert "Public signatures" not in rendered or "n/a" in rendered.split("Public signatures")[1].split("\n")[0]


def test_extract_js_object_literal_methods():
    """Bug #31: JS files using object-literal method shorthand
    (name : function(...) { ... }) should also be detected."""
    text = '''
BLCAdmin.prototype = {
    init : function() { },
    doSomething : function(arg) { return arg; },
    staticMethod: function() { },
    async fetchData() { },
};
'''
    methods = _extract_js_or_groovy(text)
    assert "init" in methods
    assert "doSomething" in methods
    assert "staticMethod" in methods
    assert "fetchData" in methods
