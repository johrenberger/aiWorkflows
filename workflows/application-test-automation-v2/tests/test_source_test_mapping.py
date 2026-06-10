from __future__ import annotations

from test_factory.analyzers.source_test_mapper import map_source_to_tests


def test_java_mapping():
    assert map_source_to_tests("src/main/java/com/example/Foo.java", "java")[0].endswith("FooTest.java")


def test_js_mapping():
    assert map_source_to_tests("src/foo.ts", "javascript")[0].endswith("foo.test.ts")


def test_python_mapping():
    assert map_source_to_tests("package/foo.py", "python")[0] == "tests/test_foo.py"
