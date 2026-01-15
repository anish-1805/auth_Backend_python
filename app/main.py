"""
FastAPI application initialization and configuration.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, init_db
from app.core.logging import setup_logging, logger
from app.features.auth.routes import router as auth_router
from app.features.files.routes import router as files_router
from app.middleware.error_handler import error_handler_middleware
from app.middleware.logging import logging_middleware
from app.middleware.security import security_headers_middleware

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting FastAPI Auth Backend...")
    await init_db()
    logger.info("✅ Database initialized successfully")
    logger.info(f"📍 Server running on: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔗 Frontend URL: {settings.FRONTEND_URL}")
    logger.info("✅ Server is ready to accept connections!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down FastAPI Auth Backend...")
    await engine.dispose()
    logger.info("✅ Database connections closed")


# Initialize FastAPI app
app = FastAPI(
    title="Auth Backend API",
    description="JWT Authentication Backend with FastAPI and PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Set-Cookie"],
    expose_headers=["Set-Cookie"],
)

# Custom Middleware
app.middleware("http")(security_headers_middleware)
app.middleware("http")(logging_middleware)
app.middleware("http")(error_handler_middleware)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(files_router, prefix="/api", tags=["Files"])


@app.get("/", response_class=JSONResponse)
async def health_check() -> dict[str, str | bool]:
    """
    Root health check endpoint.
    """
    return {
        "success": True,
        "message": "Auth Backend API is running!",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", response_class=JSONResponse)
async def health() -> dict[str, str | bool]:
    """
    Health check endpoint.
    """
    return {
        "success": True,
        "message": "Service is healthy",
        "status": "ok",
    }
