from __future__ import annotations

from pathlib import Path


def map_source_to_tests(source_path: str, language: str) -> list[str]:
    p = Path(source_path)
    stem = p.stem
    parent = p.parent.as_posix()
    if language == "java":
        package_dir = parent.replace("src/main/java", "src/test/java")
        java_candidates = [f"{package_dir}/{stem}Test.java", f"{package_dir}/{stem}IT.java"]
        # Also include Spock convention for Java sources
        groovy_dir = parent.replace("src/main/java", "src/test/groovy")
        java_candidates += [f"{groovy_dir}/{stem}Spec.groovy", f"{groovy_dir}/{stem}Test.groovy"]
        return java_candidates
    if language == "groovy":
        # Groovy source files: Spock convention is FooSpec.groovy
        package_dir = parent.replace("src/main/groovy", "src/test/groovy")
        return [f"{package_dir}/{stem}Spec.groovy", f"{package_dir}/{stem}Test.groovy"]
    if language == "javascript":
        candidates = [
            f"{parent}/{stem}.test{p.suffix}",
            f"{parent}/{stem}.spec{p.suffix}",
            f"{parent}/__tests__/{stem}.test{p.suffix}",
        ]
        return candidates
    if language == "python":
        return [f"tests/test_{stem}.py", f"{parent}/test_{stem}.py"]
    return []


def infer_existing_test_files(source_path: str, language: str) -> list[str]:
    return map_source_to_tests(source_path, language)


def supporting_files_for_source(source_path: str, language: str) -> list[str]:
    source = Path(source_path).as_posix()
    parent = Path(source_path).parent.as_posix()
    if language == "java":
        return [f"{parent}/pom.xml", "pom.xml", "build.gradle", "build.gradle.kts"]
    if language == "javascript":
        return [f"{parent}/package.json", "package.json", "jest.config.js", "jest.config.ts", "vitest.config.ts", "vitest.config.js"]
    if language == "python":
        return [f"{parent}/pyproject.toml", "pyproject.toml", "pytest.ini", "setup.py", "setup.cfg"]
    return []
