from __future__ import annotations

import inspect
import tempfile
from contextlib import ContextDecorator
from dataclasses import dataclass
from pathlib import Path


class SkipTest(Exception):
    """Raised to mark a test as skipped."""


class RaisesContext(ContextDecorator):
    def __init__(self, expected_exception: type[BaseException]) -> None:
        self.expected_exception = expected_exception

    def __enter__(self) -> "RaisesContext":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            raise AssertionError(f"Expected {self.expected_exception.__name__} to be raised")
        if not issubclass(exc_type, self.expected_exception):
            return False
        return True


@dataclass(slots=True)
class SkipIfMarker:
    condition: bool
    reason: str = ""

    def __call__(self, func):
        markers = getattr(func, "__pytest_markers__", [])
        markers.append(self)
        func.__pytest_markers__ = markers
        return func


class MarkNamespace:
    def skipif(self, condition: bool, reason: str = "") -> SkipIfMarker:
        return SkipIfMarker(condition=condition, reason=reason)


mark = MarkNamespace()


def fixture(func=None):
    def decorator(target):
        target.__pytest_fixture__ = True
        return target

    if func is None:
        return decorator
    return decorator(func)


def raises(expected_exception: type[BaseException]) -> RaisesContext:
    return RaisesContext(expected_exception)


def skip(reason: str = "") -> None:
    raise SkipTest(reason or "skipped")


def build_builtin_fixture(name: str):
    if name != "tmp_path":
        raise KeyError(name)
    return Path(tempfile.mkdtemp()), None


def resolve_arguments(callable_obj, fixture_functions, cache, finalizers):
    arguments = {}
    for parameter_name in inspect.signature(callable_obj).parameters:
        arguments[parameter_name] = resolve_fixture(parameter_name, fixture_functions, cache, finalizers)
    return arguments


def resolve_fixture(name: str, fixture_functions, cache, finalizers):
    if name in cache:
        return cache[name]

    if name == "tmp_path":
        value, temp_dir = build_builtin_fixture(name)
        finalizers.append(None)
        cache[name] = value
        return value

    if name not in fixture_functions:
        raise KeyError(f"Unknown fixture: {name}")

    fixture_func = fixture_functions[name]
    arguments = resolve_arguments(fixture_func, fixture_functions, cache, finalizers)
    value = fixture_func(**arguments)
    cache[name] = value
    return value
