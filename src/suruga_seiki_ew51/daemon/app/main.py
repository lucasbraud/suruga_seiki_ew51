"""Main FastAPI application for the EW-51 daemon."""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from suruga_seiki_ew51 import __version__
from suruga_seiki_ew51.daemon.daemon import EW51Daemon
from suruga_seiki_ew51.utils import StationException
from suruga_seiki_ew51.config import settings
from suruga_seiki_ew51.daemon.app.routers import (
    daemon_router,
    servo_router,
    movement_router,
    status_router,
    alignment_router,
)
from suruga_seiki_ew51.daemon.app import dependencies

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application.

    Handles startup and shutdown of the daemon.
    """
    # Startup
    logger.info("Starting EW-51 daemon application...")

    # Get configuration from app state (set by CLI)
    use_mock = app.state.use_mock if hasattr(app.state, "use_mock") else True
    dll_path = app.state.dll_path if hasattr(app.state, "dll_path") else None

    # Create and set the global daemon instance
    dependencies.daemon = EW51Daemon(use_mock=use_mock, dll_path=dll_path)

    try:
        await dependencies.daemon.start()
        logger.info("Daemon started successfully")
    except Exception as e:
        logger.error(f"Failed to start daemon: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down daemon...")
    if dependencies.daemon:
        await dependencies.daemon.stop()
        dependencies.daemon = None
    logger.info("Daemon shutdown complete")


def create_app(use_mock: bool = True) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        use_mock: Whether to use mock backend.
        dll_path: Path to srgmc.dll (for real backend).

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="Suruga Seiki EW-51 Motion Control API",
        description="REST API for controlling the Suruga Seiki EW-51 motion controller",
        version=__version__,
        lifespan=lifespan,
    )

    # Store configuration in app state
    app.state.use_mock = use_mock
    app.state.dll_path = None if use_mock else settings.SRGMC_DLL_PATH

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler for StationException
    @app.exception_handler(StationException)
    async def station_exception_handler(request: Request, exc: StationException):
        """Handle custom station exceptions."""
        logger.error(f"Station exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": exc.__class__.__name__, "message": str(exc)},
        )

    # Dependencies are now handled through the shared dependencies module

    # Include routers
    app.include_router(daemon_router, prefix="/ew51", tags=["daemon"])
    app.include_router(servo_router, prefix="/ew51", tags=["servo"])
    app.include_router(movement_router, prefix="/ew51", tags=["movement"])
    app.include_router(status_router, prefix="/ew51", tags=["status"])
    app.include_router(alignment_router, prefix="/ew51", tags=["alignment"])

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Suruga Seiki EW-51 Motion Control API",
            "version": __version__,
            "docs": "/docs",
        }

    # Health check endpoint
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": __version__,
            "daemon_state": dependencies.daemon.state.value if dependencies.daemon else "not_initialized",
        }

    return app


# Create default app instance
app = create_app()
