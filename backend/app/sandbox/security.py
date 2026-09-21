import os
from pathlib import Path


class SecurityValidator:
    FORBIDDEN_PATTERNS = [
        "..",
        "/etc",
        "/proc",
        "/sys",
        "/var/run/docker.sock",
        "C:\\Windows",
        "~",
        ".env",
    ]

    @classmethod
    def validate_safe_path(cls, base_dir: Path, target_path: str) -> Path:
        """Ensure that target_path does not escape base_dir."""
        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern in target_path:
                raise ValueError(f"Security violation: path contains forbidden pattern '{pattern}'")

        resolved_base = base_dir.resolve()
        resolved_target = (base_dir / target_path).resolve()

        try:
            resolved_target.relative_to(resolved_base)
        except ValueError:
            raise ValueError(f"Path traversal detected: {target_path} resolves outside {base_dir}")

        return resolved_target
