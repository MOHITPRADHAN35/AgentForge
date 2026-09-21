import difflib
import os
from pathlib import Path
from typing import Dict, Any
from app.sandbox.security import SecurityValidator


class PatchingTools:
    IGNORE_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}

    @classmethod
    def apply_patch(
        cls,
        workspace_dir: Path,
        file_path: str,
        old_snippet: str,
        new_snippet: str
    ) -> Dict[str, Any]:
        target_file = SecurityValidator.validate_safe_path(workspace_dir, file_path)
        if not target_file.is_file():
            return {"error": f"Target file '{file_path}' does not exist."}

        content = target_file.read_text(encoding="utf-8")

        # Normalize line endings
        normalized_content = content.replace("\r\n", "\n")
        normalized_old = old_snippet.replace("\r\n", "\n").strip()
        normalized_new = new_snippet.replace("\r\n", "\n").strip()

        if normalized_old not in normalized_content:
            # Try fuzzy/stripped line match
            return {
                "success": False,
                "error": "The specified old_snippet was not found verbatim in the file. Please re-read the file to ensure exact line matching."
            }

        patched_content = normalized_content.replace(normalized_old, normalized_new, 1)
        target_file.write_text(patched_content, encoding="utf-8")

        return {
            "success": True,
            "file_path": file_path,
            "message": f"Successfully applied patch to {file_path}"
        }

    @classmethod
    def compute_diff(cls, original_dir: Path, modified_dir: Path) -> str:
        """Compute unified diff between original and modified directory."""
        diff_lines = []

        all_rel_files = set()
        for d in [original_dir, modified_dir]:
            if not d.exists():
                continue
            for root, dirs, files in os.walk(d):
                dirs[:] = [dir_name for dir_name in dirs if dir_name not in cls.IGNORE_DIRS]
                for file in files:
                    rel = (Path(root) / file).relative_to(d)
                    all_rel_files.add(str(rel).replace("\\", "/"))

        for rel in sorted(all_rel_files):
            orig_file = original_dir / rel
            mod_file = modified_dir / rel

            orig_text = orig_file.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True) if orig_file.exists() else []
            mod_text = mod_file.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True) if mod_file.exists() else []

            diff = difflib.unified_diff(
                orig_text,
                mod_text,
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}"
            )
            file_diff = list(diff)
            if file_diff:
                diff_lines.extend(file_diff)

        return "".join(diff_lines)
