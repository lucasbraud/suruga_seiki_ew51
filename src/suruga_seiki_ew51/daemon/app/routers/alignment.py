"""Alignment control endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path

from suruga_seiki_ew51.models import (
    FlatAlignmentParameters,
    FocusAlignmentParameters,
    AlignmentStatusResponse,
    AlignmentResultResponse,
    ProfileDataType,
    ProfileData,
)
from suruga_seiki_ew51.daemon.daemon import EW51Daemon
from suruga_seiki_ew51.daemon.backend.real import RealBackend
from suruga_seiki_ew51.utils import AlignmentError

logger = logging.getLogger(__name__)

router = APIRouter()


from suruga_seiki_ew51.daemon.app.dependencies import get_daemon


@router.post("/alignment/flat/configure")
async def configure_flat_alignment(
    params: FlatAlignmentParameters,
    wavelength: Optional[int] = Query(None, description="Wavelength in nm (e.g., 1310, 1550)"),
    daemon: EW51Daemon = Depends(get_daemon),
):
    """Configure flat alignment parameters.

    Args:
        params: Flat alignment parameters.
        wavelength: Optional measurement wavelength in nm.

    Returns:
        Configuration confirmation.

    Raises:
        HTTPException: If configuration fails or backend is not real hardware.
    """
    logger.info("Configuring flat alignment")

    # Check if using real backend
    if daemon.is_mock:
        raise HTTPException(
            status_code=400,
            detail="Alignment not supported with mock backend. Use real hardware.",
        )

    try:
        backend = daemon.backend
        if not isinstance(backend, RealBackend):
            raise HTTPException(
                status_code=400,
                detail="Alignment requires real hardware backend",
            )

        alignment_controller = backend.get_alignment_controller()
        await alignment_controller.configure_flat_alignment(params, wavelength)

        return {
            "status": "configured",
            "mode": "flat",
            "wavelength": wavelength,
            "message": "Flat alignment configured successfully",
        }

    except AlignmentError as e:
        logger.error(f"Alignment configuration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during alignment configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {e}")


@router.post("/alignment/focus/configure")
async def configure_focus_alignment(
    params: FocusAlignmentParameters,
    wavelength: Optional[int] = Query(None, description="Wavelength in nm (e.g., 1310, 1550)"),
    daemon: EW51Daemon = Depends(get_daemon),
):
    """Configure focus alignment parameters.

    Args:
        params: Focus alignment parameters.
        wavelength: Optional measurement wavelength in nm.

    Returns:
        Configuration confirmation.

    Raises:
        HTTPException: If configuration fails or backend is not real hardware.
    """
    logger.info("Configuring focus alignment")

    # Check if using real backend
    if daemon.is_mock:
        raise HTTPException(
            status_code=400,
            detail="Alignment not supported with mock backend. Use real hardware.",
        )

    try:
        backend = daemon.backend
        if not isinstance(backend, RealBackend):
            raise HTTPException(
                status_code=400,
                detail="Alignment requires real hardware backend",
            )

        alignment_controller = backend.get_alignment_controller()
        await alignment_controller.configure_focus_alignment(params, wavelength)

        return {
            "status": "configured",
            "mode": "focus",
            "z_mode": params.z_mode.value,
            "wavelength": wavelength,
            "message": "Focus alignment configured successfully",
        }

    except AlignmentError as e:
        logger.error(f"Alignment configuration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during alignment configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {e}")


@router.post("/alignment/flat/start", response_model=dict)
async def start_flat_alignment(daemon: EW51Daemon = Depends(get_daemon)):
    """Start flat alignment execution.

    Returns:
        Start confirmation with status.

    Raises:
        HTTPException: If start fails or backend is not real hardware.
    """
    logger.info("Starting flat alignment")

    if daemon.is_mock:
        raise HTTPException(
            status_code=400,
            detail="Alignment not supported with mock backend",
        )

    try:
        backend = daemon.backend
        if not isinstance(backend, RealBackend):
            raise HTTPException(
                status_code=400,
                detail="Alignment requires real hardware backend",
            )

        alignment_controller = backend.get_alignment_controller()
        await alignment_controller.start_flat_alignment()

        return {
            "status": "started",
            "mode": "flat",
            "message": "Flat alignment started successfully",
        }

    except AlignmentError as e:
        logger.error(f"Failed to start alignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error starting alignment: {e}")
        raise HTTPException(status_code=500, detail=f"Start failed: {e}")


@router.post("/alignment/focus/start", response_model=dict)
async def start_focus_alignment(daemon: EW51Daemon = Depends(get_daemon)):
    """Start focus alignment execution.

    Returns:
        Start confirmation with status.

    Raises:
        HTTPException: If start fails or backend is not real hardware.
    """
    logger.info("Starting focus alignment")

    if daemon.is_mock:
        raise HTTPException(
            status_code=400,
            detail="Alignment not supported with mock backend",
        )

    try:
        backend = daemon.backend
        if not isinstance(backend, RealBackend):
            raise HTTPException(
                status_code=400,
                detail="Alignment requires real hardware backend",
            )

        alignment_controller = backend.get_alignment_controller()
        await alignment_controller.start_focus_alignment()

        return {
            "status": "started",
            "mode": "focus",
            "message": "Focus alignment started successfully",
        }

    except AlignmentError as e:
        logger.error(f"Failed to start alignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error starting alignment: {e}")
        raise HTTPException(status_code=500, detail=f"Start failed: {e}")


@router.post("/alignment/stop", response_model=dict)
async def stop_alignment(daemon: EW51Daemon = Depends(get_daemon)):
    """Stop alignment execution.

    Returns:
        Stop confirmation.

    Raises:
        HTTPException: If stop fails or backend is not real hardware.
    """
    logger.info("Stopping alignment")

    if daemon.is_mock:
        raise HTTPException(
            status_code=400,
            detail="Alignment not supported with mock backend",
        )

    try:
        backend = daemon.backend
        if not isinstance(backend, RealBackend):
            raise HTTPException(
                status_code=400,
                detail="Alignment requires real hardware backend",
            )

        alignment_controller = backend.get_alignment_controller()
        await alignment_controller.stop_alignment()

        return {
            "status": "stopped",
            "message": "Alignment stopped successfully",
        }

    except AlignmentError as e:
        logger.error(f"Failed to stop alignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error stopping alignment: {e}")
        raise HTTPException(status_code=500, detail=f"Stop failed: {e}")


@router.get("/alignment/status", response_model=AlignmentStatusResponse)
async def get_alignment_status(
    pm_channel: Optional[int] = Query(None, ge=1, le=4, description="Power meter channel (1-4)"),
    daemon: EW51Daemon = Depends(get_daemon),
):
    """Get current alignment status.

    Args:
        pm_channel: Optional power meter channel to read optical power.

    Returns:
        Current alignment status including optical power if requested.

    Raises:
        HTTPException: If status cannot be retrieved or backend is not real hardware.
    """
    if daemon.is_mock:
        raise HTTPException(
            status_code=400,
            detail="Alignment not supported with mock backend",
        )

    try:
        backend = daemon.backend
        if not isinstance(backend, RealBackend):
            raise HTTPException(
                status_code=400,
                detail="Alignment requires real hardware backend",
            )

        alignment_controller = backend.get_alignment_controller()
        status = await alignment_controller.get_status_info(pm_channel)

        return status

    except Exception as e:
        logger.error(f"Failed to get alignment status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {e}")


@router.post("/alignment/wait", response_model=AlignmentResultResponse)
async def wait_for_alignment_completion(
    timeout: float = Query(300.0, ge=1.0, le=600.0, description="Timeout in seconds"),
    daemon: EW51Daemon = Depends(get_daemon),
):
    """Wait for alignment to complete.

    Args:
        timeout: Maximum time to wait in seconds (default: 300, max: 600).

    Returns:
        Alignment result after completion.

    Raises:
        HTTPException: If alignment fails, times out, or backend is not real hardware.
    """
    logger.info(f"Waiting for alignment completion (timeout: {timeout}s)")

    if daemon.is_mock:
        raise HTTPException(
            status_code=400,
            detail="Alignment not supported with mock backend",
        )

    try:
        backend = daemon.backend
        if not isinstance(backend, RealBackend):
            raise HTTPException(
                status_code=400,
                detail="Alignment requires real hardware backend",
            )

        alignment_controller = backend.get_alignment_controller()
        result = await alignment_controller.wait_for_completion(timeout=timeout)

        return result

    except AlignmentError as e:
        logger.error(f"Alignment completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error waiting for alignment: {e}")
        raise HTTPException(status_code=500, detail=f"Wait failed: {e}")


@router.get("/alignment/profile/{profile_type}/count", response_model=dict)
async def get_profile_packet_count(
    profile_type: ProfileDataType,
    daemon: EW51Daemon = Depends(get_daemon),
):
    """Get number of profile data packets available.

    Args:
        profile_type: Type of profile data (FieldSearch, PeakSearchX, PeakSearchY).

    Returns:
        Number of packets available.

    Raises:
        HTTPException: If count cannot be retrieved or backend is not real hardware.
    """
    if daemon.is_mock:
        raise HTTPException(
            status_code=400,
            detail="Alignment not supported with mock backend",
        )

    try:
        backend = daemon.backend
        if not isinstance(backend, RealBackend):
            raise HTTPException(
                status_code=400,
                detail="Alignment requires real hardware backend",
            )

        alignment_controller = backend.get_alignment_controller()
        count = alignment_controller.get_profile_packet_count(profile_type)

        return {
            "profile_type": profile_type.value,
            "packet_count": count,
        }

    except Exception as e:
        logger.error(f"Failed to get profile packet count: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get count: {e}")


@router.get("/alignment/profile/{profile_type}/{packet_number}", response_model=ProfileData)
async def get_profile_data_packet(
    profile_type: ProfileDataType,
    packet_number: int = Path(..., ge=1, description="Packet number (1-indexed)"),
    daemon: EW51Daemon = Depends(get_daemon),
):
    """Get specific profile data packet.

    Args:
        profile_type: Type of profile data.
        packet_number: Packet number to retrieve (1-indexed).

    Returns:
        Profile data packet with positions and signals.

    Raises:
        HTTPException: If packet cannot be retrieved or backend is not real hardware.
    """
    if daemon.is_mock:
        raise HTTPException(
            status_code=400,
            detail="Alignment not supported with mock backend",
        )

    try:
        backend = daemon.backend
        if not isinstance(backend, RealBackend):
            raise HTTPException(
                status_code=400,
                detail="Alignment requires real hardware backend",
            )

        alignment_controller = backend.get_alignment_controller()
        data = alignment_controller.get_profile_data(profile_type, packet_number)

        return data

    except Exception as e:
        logger.error(f"Failed to get profile data packet: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get packet: {e}")
