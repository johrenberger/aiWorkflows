"""Regression tests for Bug #8: Spock/Groovy support."""
from test_factory.analyzers.module_detector import detect_language_and_module
from test_factory.analyzers.eligibility import file_is_test
from test_factory.analyzers.source_test_mapper import map_source_to_tests
from test_factory.analyzers.test_type_recommender import conventions_summary
from pathlib import Path
import tempfile


def test_groovy_module_detection(tmp_path):
    """Bug #8: .groovy files in src/test/groovy/ should be detected as groovy language."""
    (tmp_path / "src" / "test" / "groovy" / "com" / "example").mkdir(parents=True)
    spec = tmp_path / "src" / "test" / "groovy" / "com" / "example" / "FooSpec.groovy"
    spec.write_text("class FooSpec extends Specification { def 'example'() { expect: 1 == 1 } }")
    lang, mod, evidence = detect_language_and_module(tmp_path, spec)
    assert lang == "groovy"
    assert "framework" in evidence and evidence["framework"] == "spock"
    assert mod == "com/example"


def test_groovy_main_source_detection(tmp_path):
    """Groovy main source files (not just test) should be detected too."""
    (tmp_path / "src" / "main" / "groovy" / "com" / "example").mkdir(parents=True)
    src = tmp_path / "src" / "main" / "groovy" / "com" / "example" / "Foo.groovy"
    src.write_text("class Foo {}")
    lang, mod, _ = detect_language_and_module(tmp_path, src)
    assert lang == "groovy"
    assert mod == "com/example"


def test_spec_groovy_is_test_file():
    """Bug #8: *Spec.groovy files must be classified as test files."""
    assert file_is_test("src/test/groovy/com/example/FooSpec.groovy") is True


def test_groovy_test_file_in_test_dir():
    """*Test.groovy in test dir is a test file."""
    assert file_is_test("src/test/groovy/com/example/BarTest.groovy") is True


def test_groovy_main_is_not_test():
    """*Service.groovy in main dir is NOT a test file."""
    assert file_is_test("src/main/groovy/com/example/FooService.groovy") is False


def test_java_source_includes_spock_candidate():
    """Bug #8: Java source's candidate_paths should include Spock convention."""
    candidates = map_source_to_tests(
        "src/main/java/com/example/Foo.java", "java"
    )
    # Should still have the Java JUnit candidates
    assert any("FooTest.java" in c for c in candidates)
    # Should ALSO have the Spock convention (Bug #8 fix)
    assert any("FooSpec.groovy" in c for c in candidates)
    assert any("FooTest.groovy" in c for c in candidates)


def test_groovy_source_uses_spock_convention():
    """Groovy source should map to FooSpec.groovy convention."""
    candidates = map_source_to_tests(
        "src/main/groovy/com/example/Foo.groovy", "groovy"
    )
    assert "src/test/groovy/com/example/FooSpec.groovy" in candidates
    assert "src/test/groovy/com/example/FooTest.groovy" in candidates


def test_conventions_summary_for_groovy():
    """Work-items for groovy files should get a Spock convention hint."""
    summary = conventions_summary("groovy", "src/main/groovy/Foo.groovy")
    assert "Spock" in summary
    assert "*Spec.groovy" in summary
