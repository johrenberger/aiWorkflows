"""Regression tests for Bug #15: vendor JS files at top of queue."""
from test_factory.analyzers.eligibility import classify_file
from test_factory.models import Config


def test_vendor_dir_excluded():
    """Bug #15: /vendor/ and /vendors/ JS/CSS should be excluded."""
    config = Config()
    assert classify_file("src/main/resources/static/vendor/jquery.js", config) == (False, "vendor-bundle")
    assert classify_file("src/main/resources/static/vendors/select2.js", config) == (False, "vendor-bundle")


def test_lib_dir_excluded_for_assets():
    """/lib/ paths with .js/.css should be excluded (commonly third-party)."""
    config = Config()
    assert classify_file("src/main/resources/lib/bootstrap.js", config) == (False, "vendor-bundle")
    assert classify_file("src/main/resources/lib/bootstrap.css", config) == (False, "vendor-bundle")


def test_app_code_in_main_is_not_excluded():
    """Application code in src/main/ should still be eligible."""
    config = Config()
    eligible, reason = classify_file("src/main/java/com/example/Foo.java", config)
    assert eligible is True, f"Java source unexpectedly excluded: {reason}"


def test_python_source_in_lib_dir_still_eligible():
    """The /lib/ rule is JS/CSS-only; Python source files in lib/ are app code."""
    config = Config()
    # Python files in /lib/ (rare) are still eligible - the rule targets JS/CSS bundles
    eligible, reason = classify_file("lib/utils.py", config)
    # If the file matches eligible_source_globs, it's eligible; if not, it's not-source-eligible
    # In either case, NOT vendor-bundle
    assert reason != "vendor-bundle", f"Python lib file wrongly classified as vendor-bundle"
