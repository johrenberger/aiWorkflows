from __future__ import annotations

from pathlib import Path

from test_factory.adapters.java_junit import JavaJUnitAdapter
from test_factory.adapters.js_jest_vitest import JsJestVitestAdapter
from test_factory.adapters.python_pytest import PythonPytestAdapter


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-repo"


def test_adapter_detection_uses_fixture_signals():
    assert JavaJUnitAdapter().detect(FIXTURE).confidence > 0
    assert JsJestVitestAdapter().detect(FIXTURE).confidence > 0
    assert PythonPytestAdapter().detect(FIXTURE).confidence > 0
