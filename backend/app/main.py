from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.session import init_db, close_db
from app.api.routes import router as api_router
from app.api.dependencies import get_vector_store

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Starting DAM backend", env=settings.app_env)

    await init_db()
    logger.info("Database initialized")

    # Initialize vector store
    vector_store = await get_vector_store()
    logger.info("Vector store initialized")

    yield

    # Shutdown
    logger.info("Shutting down DAM backend")
    await close_db()
    vs = await get_vector_store()
    await vs.close()


app = FastAPI(
    title="AI-Powered Digital Asset Management",
    description="Local-first DAM with multimodal AI understanding",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "AI-Powered Digital Asset Management",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health",
    }
