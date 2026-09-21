import os
from pathlib import Path
from typing import Dict, Any, List
from app.sandbox.security import SecurityValidator


class FilesystemTools:
    IGNORE_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}

    @classmethod
    def list_files(cls, workspace_dir: Path, subpath: str = "") -> Dict[str, Any]:
        workspace_dir = workspace_dir.resolve()
        target_dir = SecurityValidator.validate_safe_path(workspace_dir, subpath).resolve()
        if not target_dir.is_dir():
            return {"error": f"Path '{subpath}' is not a directory"}

        files_list = []
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in cls.IGNORE_DIRS]
            for f in files:
                rel = (Path(root).resolve() / f).relative_to(workspace_dir)
                files_list.append(str(rel).replace("\\", "/"))

        return {"files": sorted(files_list), "total": len(files_list)}

    @classmethod
    def read_file(cls, workspace_dir: Path, file_path: str) -> Dict[str, Any]:
        target_file = SecurityValidator.validate_safe_path(workspace_dir, file_path)
        if not target_file.is_file():
            return {"error": f"File '{file_path}' not found"}

        try:
            content = target_file.read_text(encoding="utf-8", errors="replace")
            return {"path": file_path, "content": content, "lines": len(content.splitlines())}
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    @classmethod
    def search_code(cls, workspace_dir: Path, query: str) -> Dict[str, Any]:
        workspace_dir = workspace_dir.resolve()
        results = []
        for root, dirs, files in os.walk(workspace_dir):
            dirs[:] = [d for d in dirs if d not in cls.IGNORE_DIRS]
            for file in files:
                if file.endswith((".py", ".md", ".txt", ".json", ".toml")):
                    full_path = Path(root).resolve() / file
                    try:
                        lines = full_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                        for idx, line in enumerate(lines, 1):
                            if query.lower() in line.lower():
                                rel_path = full_path.relative_to(workspace_dir)
                                results.append({
                                    "file": str(rel_path).replace("\\", "/"),
                                    "line": idx,
                                    "content": line.strip()
                                })
                    except Exception:
                        pass
        return {"query": query, "matches": results[:50], "total_matches": len(results)}

    @classmethod
    def write_file(cls, workspace_dir: Path, file_path: str, content: str) -> Dict[str, Any]:
        target_file = SecurityValidator.validate_safe_path(workspace_dir, file_path)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content, encoding="utf-8")
        return {"success": True, "path": file_path, "bytes_written": len(content.encode("utf-8"))}
