import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # Nebius Token Factory / AI Studio
    NEBIUS_API_KEY: str = "mock_key"
    NEBIUS_BASE_URL: str = "https://api.studio.nebius.ai/v1"
    NEMOTRON_MODEL: str = "nvidia/nemotron-4-340b-instruct"

    # Execution / Sandbox Settings
    SANDBOX_TIMEOUT_SECONDS: int = 120
    SANDBOX_MEMORY_LIMIT: str = "512m"
    SANDBOX_CPU_LIMIT: float = 1.0
    MAX_REPAIR_ATTEMPTS: int = 3
    SANDBOX_IMAGE: str = "agentforge-sandbox:latest"

    # Database Settings
    DATABASE_URL: str = "sqlite:///./agentforge.db"

    # Server Settings
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Workspaces
    WORKSPACE_DIR: Path = Path("./workspaces").resolve()

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
os.makedirs(settings.WORKSPACE_DIR, exist_ok=True)
