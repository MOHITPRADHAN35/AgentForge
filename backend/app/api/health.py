from fastapi import APIRouter
from app.config import settings
from app.sandbox.docker_runner import DockerRunner
from app.nebius.client import NebiusClient

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def get_health():
    runner = DockerRunner()
    nebius = NebiusClient()
    return {
        "status": "healthy",
        "docker_available": runner.is_docker_available,
        "nebius_configured": nebius.is_configured,
        "model": settings.NEMOTRON_MODEL,
        "sandbox_timeout": settings.SANDBOX_TIMEOUT_SECONDS
    }
