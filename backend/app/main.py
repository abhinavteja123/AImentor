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
from .database.mongodb import init_mongodb, close_mongodb
from .database.redis_client import init_redis, close_redis

# Import API routers
from .api.v1 import auth, profile, skills, roadmap, progress, mentor, resume

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
    
    # Initialize databases
    await init_db()
    logger.info("✅ PostgreSQL connected")
    
    await init_mongodb()
    logger.info("✅ MongoDB connected")
    
    await init_redis()
    logger.info("✅ Redis connected")
    
    logger.info(f"🎯 {settings.APP_NAME} v{settings.APP_VERSION} is ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AI Life Mentor Backend...")
    await close_db()
    await close_mongodb()
    await close_redis()
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
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["Profile"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["Skills"])
app.include_router(roadmap.router, prefix="/api/v1/roadmap", tags=["Roadmap"])
app.include_router(progress.router, prefix="/api/v1/progress", tags=["Progress"])
app.include_router(mentor.router, prefix="/api/v1/mentor", tags=["Mentor Chat"])
app.include_router(resume.router, prefix="/api/v1/resume", tags=["Resume"])


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
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
