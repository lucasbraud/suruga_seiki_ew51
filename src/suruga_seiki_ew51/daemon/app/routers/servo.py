"""Servo control endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from suruga_seiki_ew51.models import ServoRequest, ServoResponse, AxisId
from suruga_seiki_ew51.daemon.daemon import EW51Daemon
from suruga_seiki_ew51.utils import ServoError
from suruga_seiki_ew51.daemon.app.dependencies import get_daemon

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/servo/enable", response_model=List[ServoResponse])
async def enable_servo(
    request: ServoRequest, daemon: EW51Daemon = Depends(get_daemon)
):
    """Enable servo control for specified axes.

    Args:
        request: Servo enable request containing list of axes.

    Returns:
        List of servo response objects for each axis.

    Raises:
        HTTPException: If servo enable fails.
    """
    logger.info(f"Enabling servo for axes: {[a.name for a in request.axes]}")

    responses = []
    for axis in request.axes:
        try:
            await daemon.backend.enable_servo(axis)
            enabled = await daemon.backend.is_servo_enabled(axis)

            responses.append(
                ServoResponse(axis=axis, enabled=enabled, success=True)
            )
            logger.debug(f"Servo enabled for axis {axis.name}")

        except ServoError as e:
            logger.error(f"Failed to enable servo for axis {axis.name}: {e}")
            responses.append(
                ServoResponse(axis=axis, enabled=False, success=False)
            )

    return responses


@router.post("/servo/disable", response_model=List[ServoResponse])
async def disable_servo(
    request: ServoRequest, daemon: EW51Daemon = Depends(get_daemon)
):
    """Disable servo control for specified axes.

    Args:
        request: Servo disable request containing list of axes.

    Returns:
        List of servo response objects for each axis.

    Raises:
        HTTPException: If servo disable fails.
    """
    logger.info(f"Disabling servo for axes: {[a.name for a in request.axes]}")

    responses = []
    for axis in request.axes:
        try:
            await daemon.backend.disable_servo(axis)
            enabled = await daemon.backend.is_servo_enabled(axis)

            responses.append(
                ServoResponse(axis=axis, enabled=enabled, success=True)
            )
            logger.debug(f"Servo disabled for axis {axis.name}")

        except ServoError as e:
            logger.error(f"Failed to disable servo for axis {axis.name}: {e}")
            responses.append(
                ServoResponse(axis=axis, enabled=True, success=False)
            )

    return responses


@router.get("/servo/status/{axis}", response_model=ServoResponse)
async def get_servo_status(axis: AxisId, daemon: EW51Daemon = Depends(get_daemon)):
    """Get servo status for a specific axis.

    Args:
        axis: Axis identifier.

    Returns:
        Servo status for the specified axis.

    Raises:
        HTTPException: If status cannot be retrieved.
    """
    try:
        enabled = await daemon.backend.is_servo_enabled(axis)
        return ServoResponse(axis=axis, enabled=enabled, success=True)

    except Exception as e:
        logger.error(f"Failed to get servo status for axis {axis.name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get servo status: {e}"
        )
