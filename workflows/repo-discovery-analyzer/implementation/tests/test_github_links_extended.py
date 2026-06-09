"""Extended tests for repo_discovery_analyzer.github_links.

Covers the parse_github_url / detect_default_branch / build_links_by_path
paths that the original test_github_links.py leaves out.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from repo_discovery_analyzer.github_links import (
    build_links_by_path,
    detect_default_branch,
    parse_github_url,
)


class ParseGithubUrlTests(unittest.TestCase):
    def test_https_url_with_trailing_slash(self) -> None:
        self.assertEqual(parse_github_url("https://github.com/acme/widget/"), ("acme", "widget"))

    def test_https_url_with_dot_git_suffix(self) -> None:
        self.assertEqual(parse_github_url("https://github.com/acme/widget.git"), ("acme", "widget"))

    def test_ssh_url_with_dot_git(self) -> None:
        self.assertEqual(parse_github_url("git@github.com:acme/widget.git"), ("acme", "widget"))

    def test_ssh_url_without_dot_git(self) -> None:
        self.assertEqual(parse_github_url("git@github.com:acme/widget"), ("acme", "widget"))

    def test_url_with_whitespace_is_stripped(self) -> None:
        self.assertEqual(parse_github_url("  https://github.com/acme/widget  "), ("acme", "widget"))

    def test_unsupported_url_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            parse_github_url("https://gitlab.com/acme/widget")
        with self.assertRaises(ValueError):
            parse_github_url("not a url at all")


class DetectDefaultBranchTests(unittest.TestCase):
    def test_uses_symbolic_ref_when_available(self) -> None:
        # First candidate (`symbolic-ref --short refs/remotes/origin/HEAD`)
        # returns "origin/main" → the function should return "main".
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with mock.patch.object(subprocess, "run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="origin/main\n", stderr=""
                )
                branch = detect_default_branch(repo)
            self.assertEqual(branch, "main")

    def test_falls_back_to_remote_show_on_symbolic_ref_failure(self) -> None:
        # When `symbolic-ref` fails, the second candidate is invoked.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            def fake_run(cmd, *a, **kw):
                if "symbolic-ref" in cmd:
                    return subprocess.CompletedProcess(
                        args=cmd, returncode=128, stdout="", stderr="fatal"
                    )
                # remote show origin → "HEAD branch: develop"
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0, stdout="HEAD branch: develop\n", stderr=""
                )

            with mock.patch.object(subprocess, "run", side_effect=fake_run):
                branch = detect_default_branch(repo)
            self.assertEqual(branch, "develop")

    def test_symbolic_ref_without_origin_prefix_is_used_as_is(self) -> None:
        # symbolic-ref output that doesn't start with "origin/" is
        # returned verbatim (defensive branch).
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with mock.patch.object(subprocess, "run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="trunk\n", stderr=""
                )
                branch = detect_default_branch(repo)
            self.assertEqual(branch, "trunk")

    def test_returns_none_when_all_candidates_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            def fake_run(cmd, *a, **kw):
                return subprocess.CompletedProcess(
                    args=cmd, returncode=128, stdout="", stderr="fatal"
                )

            with mock.patch.object(subprocess, "run", side_effect=fake_run):
                branch = detect_default_branch(repo)
            self.assertIsNone(branch)

    def test_subprocess_oserror_is_swallowed(self) -> None:
        # If `git` isn't on PATH, subprocess.run raises OSError, which
        # the detector catches and moves to the next candidate.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with mock.patch.object(
                subprocess, "run", side_effect=OSError("git not found")
            ):
                branch = detect_default_branch(repo)
            self.assertIsNone(branch)

    def test_remote_show_no_head_branch_line(self) -> None:
        # remote show origin returns 0 but contains no "HEAD branch:" line
        # → falls through with no result.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            def fake_run(cmd, *a, **kw):
                if "symbolic-ref" in cmd:
                    return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0, stdout="  Some other output\n", stderr=""
                )

            with mock.patch.object(subprocess, "run", side_effect=fake_run):
                branch = detect_default_branch(repo)
            self.assertIsNone(branch)


class BuildLinksByPathTests(unittest.TestCase):
    def test_links_are_sorted_alphabetically(self) -> None:
        # build_links_by_path sorts the input paths before mapping, so the
        # output dict's iteration order is deterministic.
        links = build_links_by_path("acme", "widget", "abc1234", ["z.py", "a.py", "m.py"])
        self.assertEqual(
            list(links.keys()),
            ["a.py", "m.py", "z.py"],
        )

    def test_empty_paths_yields_empty_dict(self) -> None:
        self.assertEqual(build_links_by_path("acme", "widget", "abc1234", []), {})

    def test_links_use_commit_pinned_prefix(self) -> None:
        links = build_links_by_path("acme", "widget", "abc1234", ["src/app.py"])
        self.assertEqual(
            links["src/app.py"],
            "https://github.com/acme/widget/blob/abc1234/src/app.py",
        )

    def test_links_normalize_backslashes(self) -> None:
        # Windows-style backslashes get converted to forward slashes in
        # the URL value, but the dict key preserves the original (with
        # backslashes). This is a documented quirk — callers that need
        # normalized keys should do so before passing paths in.
        links = build_links_by_path("acme", "widget", "abc1234", ["src\\app.py"])
        self.assertIn("src\\app.py", links)
        self.assertEqual(
            links["src\\app.py"],
            "https://github.com/acme/widget/blob/abc1234/src/app.py",
        )

    def test_links_strip_leading_slashes(self) -> None:
        # A leading "/" in the path is stripped from the URL value but
        # the dict key preserves the original (with the leading slash).
        links = build_links_by_path("acme", "widget", "abc1234", ["/src/app.py"])
        self.assertIn("/src/app.py", links)
        self.assertEqual(
            links["/src/app.py"],
            "https://github.com/acme/widget/blob/abc1234/src/app.py",
        )


if __name__ == "__main__":
    unittest.main()
