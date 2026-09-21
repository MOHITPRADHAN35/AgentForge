import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger("sandbox.docker")


class DockerRunner:
    def __init__(self):
        self.client = None
        self._check_docker()

    def _check_docker(self):
        try:
            import docker
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker daemon connected successfully.")
        except Exception as e:
            logger.warning(f"Docker not available: {e}. Fallback to subprocess execution will be used.")
            self.client = None

    @property
    def is_docker_available(self) -> bool:
        if self.client is None:
            self._check_docker()
        return self.client is not None

    def run_command(
        self,
        workspace_path: Path,
        cmd: str,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Run a command in an isolated Docker container or fallback subprocess.
        Returns: { 'exit_code': int, 'stdout': str, 'stderr': str, 'runner': 'docker' | 'subprocess' }
        """
        if self.is_docker_available:
            return self._run_in_docker(workspace_path, cmd, timeout)
        else:
            return self._run_in_subprocess(workspace_path, cmd, timeout)

    def _run_in_docker(
        self,
        workspace_path: Path,
        cmd: str,
        timeout: int
    ) -> Dict[str, Any]:
        container = None
        try:
            # Mount host workspace_path to container /workspace
            abs_path = str(workspace_path.resolve())
            volumes = {
                abs_path: {"bind": "/workspace", "mode": "rw"}
            }

            # Security limits
            mem_limit = settings.SANDBOX_MEMORY_LIMIT
            nano_cpus = int(settings.SANDBOX_CPU_LIMIT * 1e9)

            logger.info(f"Spawning sandbox container for command: {cmd}")
            container = self.client.containers.create(
                image=settings.SANDBOX_IMAGE,
                command=f"sh -c '{cmd}'",
                working_dir="/workspace",
                volumes=volumes,
                mem_limit=mem_limit,
                nano_cpus=nano_cpus,
                network_mode="none",  # Restrict external network by default
                user="root",
            )
            container.start()

            # Wait for completion with timeout
            result = container.wait(timeout=timeout)
            exit_code = result.get("StatusCode", 1)

            logs = container.logs(stdout=True, stderr=True)
            stdout = logs.decode("utf-8", errors="replace")

            return {
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": "",
                "runner": "docker"
            }
        except Exception as e:
            logger.error(f"Docker execution failed: {e}")
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Sandbox execution error: {str(e)}",
                "runner": "docker"
            }
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def _run_in_subprocess(
        self,
        workspace_path: Path,
        cmd: str,
        timeout: int
    ) -> Dict[str, Any]:
        """Local fallback when Docker daemon is not active."""
        logger.info(f"Running fallback command in {workspace_path}: {cmd}")
        env = os.environ.copy()
        # Add python workspace to PYTHONPATH
        env["PYTHONPATH"] = str(workspace_path.resolve())

        # If cmd starts with pytest, use the active python -m pytest
        command_to_run = cmd
        if cmd.strip().startswith("pytest"):
            command_to_run = f"{sys.executable} -m {cmd}"

        try:
            proc = subprocess.run(
                command_to_run,
                shell=True,
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            return {
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "runner": "subprocess"
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": 124,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "runner": "subprocess"
            }
        except Exception as e:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e),
                "runner": "subprocess"
            }
