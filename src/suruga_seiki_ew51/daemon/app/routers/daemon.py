"""Daemon control endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException

from suruga_seiki_ew51 import __version__
from suruga_seiki_ew51.models import ConnectionResponse, HealthResponse
from suruga_seiki_ew51.daemon.daemon import EW51Daemon

logger = logging.getLogger(__name__)

router = APIRouter()


from suruga_seiki_ew51.daemon.app.dependencies import get_daemon


@router.get("/health", response_model=HealthResponse)
async def health(daemon: EW51Daemon = Depends(get_daemon)):
    """Health check endpoint.

    Returns the current health status of the daemon.
    """
    return HealthResponse(
        status="healthy" if daemon.backend.is_connected else "disconnected",
        version=__version__,
        is_mock=daemon.is_mock,
    )


@router.get("/connection", response_model=ConnectionResponse)
async def connection_status(daemon: EW51Daemon = Depends(get_daemon)):
    """Get connection status.

    Returns information about the backend connection.
    """
    return ConnectionResponse(
        connected=daemon.backend.is_connected,
        is_mock=daemon.is_mock,
        message=f"Connected to {'mock' if daemon.is_mock else 'real'} backend",
    )


@router.post("/emergency-stop")
async def emergency_stop(daemon: EW51Daemon = Depends(get_daemon)):
    """Trigger emergency stop on all axes.

    Immediately stops all motion.
    """
    logger.warning("Emergency stop triggered via API")
    await daemon.emergency_stop()
    return {"status": "emergency_stop_executed", "message": "All motion stopped"}
