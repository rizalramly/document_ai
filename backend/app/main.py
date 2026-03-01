"""DOCS.ai FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.database import init_db


# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("🚀 DOCS.ai starting up...")
    await init_db()
    logger.info("✅ Database initialized")
    yield
    logger.info("👋 DOCS.ai shutting down...")


app = FastAPI(
    title="DOCS.ai API",
    description="Engineering Document Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for rendered page images
renders_path = Path(settings.render_storage_path)
renders_path.mkdir(parents=True, exist_ok=True)
app.mount("/renders", StaticFiles(directory=str(renders_path)), name="renders")

# Import and register routers
from app.api.documents import router as doc_router
from app.api.chat import router as chat_router
from app.api.annotations import router as ann_router
from app.api.graph import router as graph_router

app.include_router(doc_router)
app.include_router(chat_router)
app.include_router(ann_router)
app.include_router(graph_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    from app.services.llm.provider import llm_provider
    ollama_ok = await llm_provider.health_check()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "ollama_connected": ollama_ok,
    }
