import os
import re
from pathlib import Path
from typing import List
from app.repository.manifest import RepositoryManifest


class RepositoryAnalyzer:
    IGNORE_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", ".tox"}

    @classmethod
    def analyze(cls, repo_path: Path) -> RepositoryManifest:
        file_count = 0
        python_modules = 0
        test_count = 0
        source_files: List[str] = []
        test_files: List[str] = []
        dependencies: List[str] = []
        has_pytest = False

        # Check requirements.txt
        req_file = repo_path / "requirements.txt"
        if req_file.exists():
            try:
                for line in req_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                    clean = line.strip()
                    if clean and not clean.startswith("#"):
                        dependencies.append(clean)
                        if "pytest" in clean.lower():
                            has_pytest = True
            except Exception:
                pass

        # Check pyproject.toml
        pyproject = repo_path / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8", errors="ignore").lower()
                if "pytest" in content:
                    has_pytest = True
            except Exception:
                pass

        # Walk through directory
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in cls.IGNORE_DIRS]
            for file in files:
                file_count += 1
                rel_path = Path(root).relative_to(repo_path) / file
                rel_str = str(rel_path).replace("\\", "/")

                if file.endswith(".py"):
                    python_modules += 1
                    is_test_file = "test" in file.lower() or "tests" in rel_str.lower()
                    if is_test_file:
                        test_files.append(rel_str)
                        has_pytest = True
                        # Count test functions
                        try:
                            code = (repo_path / rel_path).read_text(encoding="utf-8", errors="ignore")
                            tests_found = re.findall(r"^\s*def\s+(test_\w+)\s*\(", code, re.MULTILINE)
                            test_count += len(tests_found)
                        except Exception:
                            pass
                    else:
                        source_files.append(rel_str)

        return RepositoryManifest(
            language="python",
            test_framework="pytest" if has_pytest or test_files else "unknown",
            package_manager="pip",
            file_count=file_count,
            python_modules=python_modules,
            test_count=max(test_count, len(test_files)),
            dependencies=dependencies,
            test_files=sorted(test_files),
            source_files=sorted(source_files),
        )
