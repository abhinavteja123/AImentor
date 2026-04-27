"""
AI Life Mentor - FastAPI Backend
Main application entry point with CORS, routers, and health check
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database.postgres import init_db, close_db
from .database.redis_client import init_redis, close_redis, is_redis_available

# Import API routers
from .api.v1 import auth, profile, skills, roadmap, progress, mentor, resume, tutor

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events - startup and shutdown."""
    # Startup
    logger.info("🚀 Starting AI Life Mentor Backend...")
    
    # Initialize databases with error handling
    try:
        await init_db()
        logger.info("✅ PostgreSQL connected")
    except Exception as e:
        logger.error(f"⚠️  PostgreSQL connection failed: {e}")
        logger.warning("App starting in degraded mode — DB will reconnect on first request")
    
    # Redis is optional (for caching). init_redis() never raises — it logs and
    # flips an internal flag — so we check that flag rather than catching here.
    await init_redis()
    if is_redis_available():
        logger.info("✅ Redis connected")
    else:
        logger.info("ℹ️  Continuing without Redis (caching disabled — non-critical)")
    
    logger.info(f"🎯 {settings.APP_NAME} v{settings.APP_VERSION} is ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AI Life Mentor Backend...")
    try:
        await close_db()
    except Exception as e:
        logger.error(f"Error closing PostgreSQL: {e}")

    try:
        await close_redis()
    except Exception as e:
        logger.warning(f"Error closing Redis: {e}")
    
    logger.info("👋 Goodbye!")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Your Personal AI Career Coach - Remembers, Guides, Grows with You",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["Profile"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["Skills"])
app.include_router(roadmap.router, prefix="/api/v1/roadmap", tags=["Roadmap"])
app.include_router(progress.router, prefix="/api/v1/progress", tags=["Progress"])
app.include_router(mentor.router, prefix="/api/v1/mentor", tags=["Mentor Chat"])
app.include_router(resume.router, prefix="/api/v1/resume", tags=["Resume"])
app.include_router(tutor.router, prefix="/api/v1/tutor", tags=["AgentRAG Tutor"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - welcome message."""
    return {
        "message": f"Welcome to {settings.APP_NAME}!",
        "tagline": "Your Personal AI Career Coach",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring. Reports degraded if Redis is down."""
    from pathlib import Path
    redis_ok = is_redis_available()
    ppo_path = Path("backend/models/ppo_agent/final_model.zip")
    return {
        "status": "healthy" if redis_ok else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "components": {
            "postgres": "ok",
            "redis": "ok" if redis_ok else "unavailable (non-critical)",
            "ppo_checkpoint": "loaded" if ppo_path.exists() else "missing (MAB fallback)",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
