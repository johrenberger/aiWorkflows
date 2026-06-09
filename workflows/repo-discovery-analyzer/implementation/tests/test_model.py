"""Tests for repo_discovery_analyzer.model.dataclass_to_json.

Coverage of the dataclass_to_json branches: dict, list, tuple, and the
plain-value fallback. dataclass instances themselves are exercised by the
CLI / manifest flow (see test_cli.py).
"""

from __future__ import annotations

import unittest

from repo_discovery_analyzer.model import (
    AnalysisConfig,
    AnalysisManifest,
    TOOL_NAME,
    dataclass_to_json,
)


class DataclassToJsonTests(unittest.TestCase):
    def test_dataclass_instance_becomes_dict(self) -> None:
        manifest = AnalysisManifest(
            tool_name=TOOL_NAME,
            tool_version="0.1.0",
            repo_path="/tmp/repo",
            source_url_prefix="https://github.com/acme/widget/blob/abc1234/",
            commit="abc1234",
            output_dir="/tmp/out",
            start_time_utc="2026-06-10T00:00:00Z",
            end_time_utc="2026-06-10T00:00:01Z",
            elapsed_ms=1000,
            warnings=[],
            skipped_files=[],
        )
        result = dataclass_to_json(manifest)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["tool_name"], TOOL_NAME)
        self.assertEqual(result["commit"], "abc1234")
        self.assertEqual(result["elapsed_ms"], 1000)

    def test_dict_is_recursively_converted(self) -> None:
        nested = {
            "outer": AnalysisConfig(
                repo_path="/tmp/repo",
                github_url="https://github.com/acme/widget",
                commit="abc1234",
                output_dir="/tmp/out",
            ),
            "scalar": 42,
            "flag": True,
        }
        result = dataclass_to_json(nested)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["scalar"], 42)
        self.assertTrue(result["flag"])
        # The nested dataclass should have been converted to a plain dict.
        self.assertIsInstance(result["outer"], dict)
        self.assertEqual(result["outer"]["commit"], "abc1234")
        self.assertNotIn("__dataclass_fields__", result["outer"])

    def test_list_is_recursively_converted(self) -> None:
        cfg = AnalysisConfig(
            repo_path="/tmp/repo",
            github_url="https://github.com/acme/widget",
            commit="abc1234",
            output_dir="/tmp/out",
        )
        result = dataclass_to_json([cfg, "scalar", 1, None])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4)
        # The dataclass should be flattened to a dict, scalars passed through.
        self.assertIsInstance(result[0], dict)
        self.assertEqual(result[0]["commit"], "abc1234")
        self.assertEqual(result[1], "scalar")
        self.assertEqual(result[2], 1)
        self.assertIsNone(result[3])

    def test_tuple_is_converted_to_list(self) -> None:
        # dataclass_to_json normalizes tuples to lists so the JSON encoder
        # is happy (json.dumps does not natively emit tuples).
        result = dataclass_to_json((1, 2, 3))
        self.assertIsInstance(result, list)
        self.assertEqual(result, [1, 2, 3])

    def test_tuple_of_dataclasses_is_recursively_converted(self) -> None:
        cfg = AnalysisConfig(
            repo_path="/tmp/repo",
            github_url="https://github.com/acme/widget",
            commit="abc1234",
            output_dir="/tmp/out",
        )
        result = dataclass_to_json((cfg, cfg))
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        for item in result:
            self.assertIsInstance(item, dict)
            self.assertEqual(item["commit"], "abc1234")

    def test_plain_value_fallback(self) -> None:
        # Anything that is not a dataclass/dict/list/tuple is returned as-is.
        self.assertEqual(dataclass_to_json(42), 42)
        self.assertEqual(dataclass_to_json("hello"), "hello")
        self.assertEqual(dataclass_to_json(None), None)
        self.assertEqual(dataclass_to_json(3.14), 3.14)
        self.assertEqual(dataclass_to_json(True), True)


if __name__ == "__main__":
    unittest.main()
