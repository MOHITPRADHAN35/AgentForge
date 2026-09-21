from typing import List, Optional
from pydantic import BaseModel


class FileInfo(BaseModel):
    path: str
    is_test: bool
    line_count: int


class RepositoryManifest(BaseModel):
    language: str = "python"
    test_framework: str = "pytest"
    package_manager: str = "pip"
    file_count: int = 0
    python_modules: int = 0
    test_count: int = 0
    dependencies: List[str] = []
    test_files: List[str] = []
    source_files: List[str] = []
    entrypoints: List[str] = []
