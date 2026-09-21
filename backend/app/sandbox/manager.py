import re
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from app.sandbox.docker_runner import DockerRunner
from app.sandbox.security import SecurityValidator
from app.config import settings

logger = logging.getLogger("sandbox.manager")


class SandboxManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.source_dir = project_dir / "source"
        self.sandbox_dir = project_dir / "sandbox_workspace"
        self.runner = DockerRunner()

    def initialize_sandbox(self) -> Path:
        """Create a fresh isolated copy of the repository for sandbox execution."""
        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir)
        shutil.copytree(self.source_dir, self.sandbox_dir)
        logger.info(f"Initialized sandbox workspace at {self.sandbox_dir}")
        return self.sandbox_dir

    def run_tests(self, test_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute pytest in the sandbox and parse structured test results.
        """
        if not self.sandbox_dir.exists():
            self.initialize_sandbox()

        cmd = "pytest -v --tb=short"
        if test_path:
            SecurityValidator.validate_safe_path(self.sandbox_dir, test_path)
            cmd += f" {test_path}"

        raw_result = self.runner.run_command(
            workspace_path=self.sandbox_dir,
            cmd=cmd,
            timeout=settings.SANDBOX_TIMEOUT_SECONDS
        )

        parsed = self._parse_pytest_output(raw_result["stdout"], raw_result["stderr"], raw_result["exit_code"])
        parsed["runner"] = raw_result["runner"]
        parsed["raw_stdout"] = raw_result["stdout"]
        parsed["raw_stderr"] = raw_result["stderr"]
        return parsed

    def _parse_pytest_output(self, stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
        passed = 0
        failed = 0
        errors = 0

        # Pattern: "X passed, Y failed, Z error in ..."
        # or "X passed in ..."
        pass_match = re.search(r"(\d+)\s+passed", stdout)
        if pass_match:
            passed = int(pass_match.group(1))

        fail_match = re.search(r"(\d+)\s+failed", stdout)
        if fail_match:
            failed = int(fail_match.group(1))

        error_match = re.search(r"(\d+)\s+error", stdout)
        if error_match:
            errors = int(error_match.group(1))

        # Check for pytest exit codes:
        # 0: all passed
        # 1: tests failed
        # 2: test execution was interrupted
        # 4: command-line error
        # 5: no tests collected
        return {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "exit_code": exit_code,
            "success": exit_code == 0 and (passed > 0 or (failed == 0 and errors == 0)),
            "summary": f"{passed} passed, {failed} failed, {errors} errors"
        }

    def cleanup(self):
        """Remove temporary sandbox workspace."""
        if self.sandbox_dir.exists():
            try:
                shutil.rmtree(self.sandbox_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup sandbox dir: {e}")
