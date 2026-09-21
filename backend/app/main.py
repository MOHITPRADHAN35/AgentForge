import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.session import init_db
from app.api.health import router as health_router
from app.api.projects import router as projects_router
from app.api.ws import router as ws_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("agentforge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AgentForge database...")
    init_db()
    logger.info(f"AgentForge backend started. Target model: {settings.NEMOTRON_MODEL}")
    yield
    logger.info("AgentForge backend shutting down...")


app = FastAPI(
    title="AgentForge API",
    description="Autonomous Software Testing & Repair Agent powered by NVIDIA Nemotron via Nebius Token Factory",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health_router)
app.include_router(projects_router)
app.include_router(ws_router)


@app.get("/")
def read_root():
    return {
        "app": "AgentForge",
        "description": "Autonomous Software Testing & Repair Agent",
        "version": "1.0.0",
        "docs_url": "/docs"
    }
