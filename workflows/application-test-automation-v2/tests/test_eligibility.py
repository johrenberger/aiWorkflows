from __future__ import annotations

from test_factory.analyzers.eligibility import classify_file, file_is_test
from test_factory.models import Config


def test_eligibility_excludes_generated_and_non_source():
    config = Config()
    assert classify_file("src/generated/Foo.java", config)[0] is False
    assert classify_file("README.md", config)[0] is False


def test_test_file_detection():
    assert file_is_test("src/foo.test.ts")
    assert file_is_test("tests/test_foo.py")
