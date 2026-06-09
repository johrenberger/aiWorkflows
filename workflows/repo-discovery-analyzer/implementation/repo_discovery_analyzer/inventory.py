from __future__ import annotations

from pathlib import Path

from .github_links import url_for_path
from .io_utils import guess_language, guess_role, is_probably_text, normalize_path, stream_line_count, walk_files
from .model import FileRecord


def scan_repo(repo_path: Path, owner: str, repo: str, commit: str, include_large_files: bool, max_file_bytes: int) -> list[FileRecord]:
    records: list[FileRecord] = []
    for path in walk_files(repo_path):
        rel = normalize_path(path, repo_path)
        if path.is_dir():
            continue
        try:
            size_bytes = path.stat().st_size
        except OSError as exc:
            records.append(
                FileRecord(
                    path=rel,
                    extension=path.suffix.lower(),
                    size_bytes=0,
                    language_guess=guess_language(path),
                    role_guess=guess_role(path),
                    line_count=None,
                    source_line_count=None,
                    github_url=url_for_path(owner, repo, commit, rel),
                    reviewed_by_analyzer=False,
                    skipped=True,
                    skip_reason=f"unreadable: {exc.strerror or exc.__class__.__name__}",
                )
            )
            continue
        if not include_large_files and size_bytes > max_file_bytes:
            records.append(
                FileRecord(
                    path=rel,
                    extension=path.suffix.lower(),
                    size_bytes=size_bytes,
                    language_guess=guess_language(path),
                    role_guess=guess_role(path),
                    line_count=None,
                    source_line_count=None,
                    github_url=url_for_path(owner, repo, commit, rel),
                    reviewed_by_analyzer=False,
                    skipped=True,
                    skip_reason=f"file exceeds max_file_bytes ({size_bytes} > {max_file_bytes})",
                )
            )
            continue
        line_count = None
        skip_reason = None
        if is_probably_text(path):
            line_count, skip_reason = stream_line_count(path)
        if skip_reason:
            records.append(
                FileRecord(
                    path=rel,
                    extension=path.suffix.lower(),
                    size_bytes=size_bytes,
                    language_guess=guess_language(path),
                    role_guess=guess_role(path),
                    line_count=None,
                    source_line_count=None,
                    github_url=url_for_path(owner, repo, commit, rel),
                    reviewed_by_analyzer=False,
                    skipped=True,
                    skip_reason=skip_reason,
                )
            )
            continue
        records.append(
            FileRecord(
                path=rel,
                extension=path.suffix.lower(),
                size_bytes=size_bytes,
                language_guess=guess_language(path),
                role_guess=guess_role(path),
                line_count=line_count,
                source_line_count=line_count,
                github_url=url_for_path(owner, repo, commit, rel),
                reviewed_by_analyzer=True,
                skipped=False,
                skip_reason=None,
            )
        )
    return records


def build_project_structure(repo_path: Path, records: list[FileRecord]) -> dict:
    directories: dict[str, int] = {}
    top_level: set[str] = set()
    for record in records:
        path = Path(record.path)
        if path.parts:
            top_level.add(path.parts[0])
        parent = path.parent.as_posix()
        directories[parent] = directories.get(parent, 0) + 1
    notable_dirs = sorted(
        (
            {"path": path, "file_count": count}
            for path, count in directories.items()
            if path not in {".", ""}
        ),
        key=lambda item: (-item["file_count"], item["path"]),
    )[:25]
    reading_order = []
    for candidate in [
        "README.md",
        "src",
        "app",
        "lib",
        "package.json",
        "pyproject.toml",
        "pom.xml",
        "build.gradle",
        "Dockerfile",
    ]:
        for record in records:
            if record.path == candidate or record.path.startswith(candidate + "/"):
                reading_order.append(record.path)
                break
    return {
        "top_level_entries": sorted(top_level),
        "notable_directories": notable_dirs,
        "reading_order": reading_order,
    }
