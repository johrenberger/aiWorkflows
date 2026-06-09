from __future__ import annotations

import unittest

from repo_discovery_analyzer.github_links import commit_pinned_prefix, parse_github_url, url_for_path


class GitHubLinksTests(unittest.TestCase):
    def test_parse_https_url(self) -> None:
        self.assertEqual(parse_github_url("https://github.com/acme/widget"), ("acme", "widget"))

    def test_parse_ssh_url(self) -> None:
        self.assertEqual(parse_github_url("git@github.com:acme/widget.git"), ("acme", "widget"))

    def test_commit_pinned_url(self) -> None:
        prefix = commit_pinned_prefix("acme", "widget", "abc123")
        self.assertEqual(prefix, "https://github.com/acme/widget/blob/abc123/")
        self.assertEqual(url_for_path("acme", "widget", "abc123", "src/app.py"), "https://github.com/acme/widget/blob/abc123/src/app.py")


if __name__ == "__main__":
    unittest.main()

