import os
import shutil
import zipfile
import subprocess
from pathlib import Path
from typing import Tuple


class RepositoryLoader:
    @staticmethod
    def from_zip(zip_bytes: bytes, target_dir: Path) -> Path:
        """Extract a zip archive into target_dir."""
        target_dir.mkdir(parents=True, exist_ok=True)
        zip_path = target_dir / "repo.zip"
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)

        extract_path = target_dir / "source"
        extract_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        os.remove(zip_path)

        # If the zip had a single root folder, unwrap it
        children = list(extract_path.iterdir())
        if len(children) == 1 and children[0].is_dir():
            inner_dir = children[0]
            temp_dir = target_dir / "temp_source"
            shutil.move(str(inner_dir), str(temp_dir))
            shutil.rmtree(str(extract_path))
            shutil.move(str(temp_dir), str(extract_path))

        return extract_path

    @staticmethod
    def normalize_git_url(url: str) -> str:
        url = url.strip()
        if not url:
            return url
        if url.startswith("http://") or url.startswith("https://") or url.startswith("git@"):
            return url
        KNOWN_REPOS = {
            "colorama": "https://github.com/tartley/colorama.git",
            "click": "https://github.com/pallets/click.git",
            "bottle": "https://github.com/bottlepy/bottle.git",
            "requests": "https://github.com/psf/requests.git",
            "flask": "https://github.com/pallets/flask.git",
        }
        if url.lower() in KNOWN_REPOS:
            return KNOWN_REPOS[url.lower()]
        if "/" in url:
            return f"https://github.com/{url}.git"
        return f"https://github.com/{url}/{url}.git"

    @classmethod
    def from_git(cls, git_url: str, target_dir: Path) -> Path:
        """Clone a git repository into target_dir/source."""
        git_url = cls.normalize_git_url(git_url)
        extract_path = target_dir / "source"
        if extract_path.exists():
            shutil.rmtree(extract_path)
        extract_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = ["git", "clone", "--depth", "1", git_url, str(extract_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to clone repository: {result.stderr}")

        return extract_path

    @staticmethod
    def from_local_dir(source_path: Path, target_dir: Path) -> Path:
        """Copy a local repository into target_dir/source."""
        extract_path = target_dir / "source"
        if extract_path.exists():
            shutil.rmtree(extract_path)
        extract_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_path, extract_path)
        return extract_path
