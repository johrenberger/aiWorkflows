from __future__ import annotations

import json
import re
from pathlib import Path

from ..github_links import url_for_path
from ..io_utils import DEFAULT_MAX_SUMMARY_ITEMS, safe_read_text, short_snippet
from ..model import FileRecord


def detect_stack(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    files = {r.path: r for r in records}
    items: list[dict] = []

    def add(technology: str, category: str, confidence: str, paths: list[str], version: str | None = None, snippets: list[str] | None = None):
        all_paths = [p for p in sorted(set(paths)) if p in files]
        paths = all_paths[:DEFAULT_MAX_SUMMARY_ITEMS]
        if not paths:
            return
        evidence_urls = [files[p].github_url for p in paths]
        items.append(
            {
                "technology": technology,
                "category": category,
                "confidence": confidence,
                "evidence_paths": paths,
                "evidence_urls": evidence_urls,
                "evidence_path_count": len(all_paths),
                "evidence_paths_truncated": len(all_paths) > len(paths),
                "evidence_snippets": snippets or [],
                "version": version,
            }
        )

    package_json = _read_json(repo_path / "package.json")
    if package_json:
        deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
        if "react" in deps:
            add("React", "frontend-framework", "high", ["package.json"], deps.get("react"), [_snippet_for_path(repo_path / "package.json", '"react"')])
        if any(k.startswith("next") for k in deps):
            add("Next.js", "frontend-framework", "high", ["package.json"], deps.get("next"), [_snippet_for_path(repo_path / "package.json", '"next"')])
        if "vue" in deps or "@vue/runtime-dom" in deps:
            add("Vue", "frontend-framework", "high", ["package.json"], deps.get("vue"), [_snippet_for_path(repo_path / "package.json", '"vue"')])
        if "angular" in deps or "@angular/core" in deps:
            add("Angular", "frontend-framework", "high", ["package.json"], deps.get("@angular/core") or deps.get("angular"), [_snippet_for_path(repo_path / "package.json", '"@angular/core"')])
        if "express" in deps:
            add("Express", "backend-framework", "high", ["package.json"], deps.get("express"), [_snippet_for_path(repo_path / "package.json", '"express"')])
        if "vite" in deps:
            add("Vite", "build-tool", "high", ["package.json"], deps.get("vite"), [_snippet_for_path(repo_path / "package.json", '"vite"')])
        if "webpack" in deps:
            add("Webpack", "build-tool", "medium", ["package.json"], deps.get("webpack"), [_snippet_for_path(repo_path / "package.json", '"webpack"')])
        for tech, key in [("Jest", "jest"), ("Vitest", "vitest"), ("Cypress", "cypress"), ("Playwright", "playwright")]:
            if key in deps:
                add(tech, "testing", "high", ["package.json"], deps.get(key), [_snippet_for_path(repo_path / "package.json", f'"{key}"')])
        if "typescript" in deps or any(r.path.endswith((".ts", ".tsx")) for r in records):
            add("TypeScript", "language", "high", ["package.json"], deps.get("typescript"), [_snippet_for_path(repo_path / "package.json", '"typescript"') if package_json else None])
        add("npm", "package-manager", "high", ["package.json"], None, [_snippet_for_path(repo_path / "package.json", '"scripts"')])

    if (repo_path / "yarn.lock").exists():
        add("yarn", "package-manager", "high", ["yarn.lock"], None, [_snippet_for_path(repo_path / "yarn.lock", "")])
    if (repo_path / "pnpm-lock.yaml").exists():
        add("pnpm", "package-manager", "high", ["pnpm-lock.yaml"], None, [_snippet_for_path(repo_path / "pnpm-lock.yaml", "")])

    pom = repo_path / "pom.xml"
    if pom.exists():
        text, _ = safe_read_text(pom)
        if text:
            if "<artifactId>spring-boot-starter" in text or "spring-boot-maven-plugin" in text:
                add("Spring Boot", "backend-framework", "high", ["pom.xml"], _pom_version(text), [_pom_snippet(text, "spring-boot")])
            if "spring-context" in text or "spring-webmvc" in text:
                add("Spring MVC", "backend-framework", "high", ["pom.xml"], None, [_pom_snippet(text, "spring-webmvc")])
            if "spring-security" in text:
                add("Spring Security", "security", "high", ["pom.xml"], None, [_pom_snippet(text, "spring-security")])
            if "hibernate" in text:
                add("Hibernate", "database", "medium", ["pom.xml"], None, [_pom_snippet(text, "hibernate")])
            if "jakarta." in text:
                add("Jakarta", "platform", "medium", ["pom.xml"], None, [_pom_snippet(text, "jakarta")])
            if "javax." in text:
                add("Javax", "platform", "medium", ["pom.xml"], None, [_pom_snippet(text, "javax")])

    gradle_paths = [p for p in ("build.gradle", "build.gradle.kts") if (repo_path / p).exists()]
    for path in gradle_paths:
        text, _ = safe_read_text(repo_path / path)
        if text:
            if "spring-boot" in text:
                add("Spring Boot", "backend-framework", "high", [path], _gradle_version(text), [_pom_snippet(text, "spring-boot")])
            if "org.springframework" in text or "spring-webmvc" in text:
                add("Spring MVC", "backend-framework", "medium", [path], None, [_pom_snippet(text, "spring-webmvc")])
            if "spring-security" in text:
                add("Spring Security", "security", "medium", [path], None, [_pom_snippet(text, "spring-security")])

    java_files = [r for r in records if r.path.endswith(".java") and not r.skipped]
    java_texts = {r.path: (_read_text(repo_path / r.path) or "") for r in java_files}
    if any("public static void main" in text for text in java_texts.values()):
        add("Java", "language", "high", [java_files[0].path], None, [])
    spring_boot_paths = [path for path, text in java_texts.items() if "@SpringBootApplication" in text]
    if spring_boot_paths:
        add("Spring Boot", "backend-framework", "high", spring_boot_paths[:5], None, [])
    spring_mvc_paths = [path for path, text in java_texts.items() if "@RestController" in text or "@Controller" in text]
    if spring_mvc_paths:
        add("Spring MVC", "backend-framework", "high", spring_mvc_paths[:5], None, [])

    dockerfile_paths = [r.path for r in records if Path(r.path).name.lower() in {"dockerfile", "containerfile"}]
    if dockerfile_paths:
        add("Docker", "infrastructure", "high", dockerfile_paths)
    if any(Path(r.path).name.startswith("docker-compose") or Path(r.path).name.startswith("compose") for r in records):
        add("docker-compose", "infrastructure", "high", [r.path for r in records if Path(r.path).name.startswith(("docker-compose", "compose"))])
    if any(".github/workflows" in r.path for r in records):
        add("GitHub Actions", "ci", "high", [r.path for r in records if ".github/workflows" in r.path])
    if any(r.path.endswith((".tf", ".tfvars")) for r in records):
        add("Terraform", "infrastructure", "high", [r.path for r in records if r.path.endswith((".tf", ".tfvars"))])
    if any("k8s" in r.path.lower() or "kubernetes" in r.path.lower() for r in records):
        add("Kubernetes", "infrastructure", "medium", [r.path for r in records if "k8s" in r.path.lower() or "kubernetes" in r.path.lower()])

    cloud_hits: dict[str, list[str]] = {"AWS": [], "Azure": [], "GCP": []}
    for record in records:
        text = java_texts.get(record.path)
        if text is None:
            text = _read_text(repo_path / record.path) or ""
        lowered = text.lower()
        if "aws-sdk" in lowered or "boto3" in lowered:
            cloud_hits["AWS"].append(record.path)
        if "azure" in lowered:
            cloud_hits["Azure"].append(record.path)
        if "google" in lowered or "gcp" in lowered:
            cloud_hits["GCP"].append(record.path)
    if cloud_hits["AWS"]:
        add("AWS", "cloud", "medium", cloud_hits["AWS"][:5])
    if cloud_hits["Azure"]:
        add("Azure", "cloud", "medium", cloud_hits["Azure"][:5])
    if cloud_hits["GCP"]:
        add("GCP", "cloud", "medium", cloud_hits["GCP"][:5])

    items = sorted(items, key=lambda x: (x["category"], x["technology"], tuple(x["evidence_paths"])))
    return {"technologies": items}


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_text(path: Path) -> str | None:
    text, _ = safe_read_text(path)
    return text


def _snippet_for_path(path: Path, needle: str) -> str | None:
    text, _ = safe_read_text(path)
    if not text:
        return None
    for line in text.splitlines():
        if needle.lower() in line.lower():
            return short_snippet(line)
    return short_snippet(text)


def _pom_version(text: str) -> str | None:
    m = re.search(r"<version>([^<]+)</version>", text)
    return m.group(1).strip() if m else None


def _gradle_version(text: str) -> str | None:
    m = re.search(r'org\.springframework\.boot[:=]\s*[\'"]?([0-9A-Za-z.\-]+)', text)
    return m.group(1).strip() if m else None


def _pom_snippet(text: str, needle: str) -> str | None:
    for line in text.splitlines():
        if needle.lower() in line.lower():
            return short_snippet(line)
    return short_snippet(text)
