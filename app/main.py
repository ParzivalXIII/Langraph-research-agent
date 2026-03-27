"""FastAPI application initialization and routing."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.research import router as research_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import configure_logging, get_logger
from app.services.metrics import get_metrics_service

# Configure logging on import
settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Manage application lifecycle events (startup and shutdown).

    Args:
        app: FastAPI application instance

    Yields:
        Control back to FastAPI after startup
    """
    # Startup event
    logger.info(
        "app_startup",
        version=settings.api_version,
        debug=settings.debug,
        database_url=(
            settings.database_url[:50] + "..."
            if len(settings.database_url) > 50
            else settings.database_url
        ),
    )

    # Initialize database tables
    try:
        init_db()
        logger.info("database_initialized")
    except Exception as exc:
        logger.error("database_initialization_failed", error=str(exc))
        raise

    yield

    # Shutdown event
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Metrics recording middleware
    @app.middleware("http")
    async def record_metrics_middleware(request: Request, call_next):
        """Record request metrics (latency, success/failure)."""
        # Get metrics service fresh each request (called at runtime, not module load)
        metrics_service = get_metrics_service()
        start_time = time.time()
        try:
            response = await call_next(request)
            latency_ms = (time.time() - start_time) * 1000
            success = 200 <= response.status_code < 300
            metrics_service.record_request(latency_ms, success=success)
            return response
        except Exception:
            latency_ms = (time.time() - start_time) * 1000
            metrics_service.record_request(latency_ms, success=False)
            raise

    # Global exception handler for JSON responses
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        """Handle ValueError exceptions with JSON response."""
        logger.warning("value_error_handler", error=str(exc))
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "INVALID_INPUT",
                "message": str(exc),
            },
        )

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Research Agent API",
            "version": settings.api_version,
            "docs": "/docs",
        }

    # Include routers
    app.include_router(health_router)
    app.include_router(research_router)

    logger.info("app_created", routes_count=len(app.routes))
    return app


# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower(),
    )
