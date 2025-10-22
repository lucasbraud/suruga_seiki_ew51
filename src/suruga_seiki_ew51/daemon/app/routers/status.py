"""Status query endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException

from suruga_seiki_ew51.models import (
    StatusResponse,
    AxisStatus,
    StageStatus,
    AxisId,
    StageId,
)
from suruga_seiki_ew51.daemon.daemon import EW51Daemon

logger = logging.getLogger(__name__)

router = APIRouter()


from suruga_seiki_ew51.daemon.app.dependencies import get_daemon


@router.get("/status", response_model=StatusResponse)
async def get_full_status(daemon: EW51Daemon = Depends(get_daemon)):
    """Get complete station status.

    Returns full status including daemon state, both stages, and all axes.

    Returns:
        Complete station status.

    Raises:
        HTTPException: If status cannot be retrieved.
    """
    try:
        status = await daemon.get_status()
        return StatusResponse(station=status)

    except Exception as e:
        logger.error(f"Failed to get station status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {e}")


@router.get("/status/axis/{axis}", response_model=AxisStatus)
async def get_axis_status(axis: AxisId, daemon: EW51Daemon = Depends(get_daemon)):
    """Get status for a specific axis.

    Args:
        axis: Axis identifier.

    Returns:
        Status information for the specified axis.

    Raises:
        HTTPException: If status cannot be retrieved.
    """
    try:
        status = await daemon.backend.get_axis_status(axis)
        return status

    except Exception as e:
        logger.error(f"Failed to get axis status for {axis.name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get axis status: {e}"
        )


@router.get("/status/stage/{stage}", response_model=StageStatus)
async def get_stage_status(stage: StageId, daemon: EW51Daemon = Depends(get_daemon)):
    """Get status for a specific stage.

    Args:
        stage: Stage identifier (LEFT or RIGHT).

    Returns:
        Status information for the specified stage including all its axes.

    Raises:
        HTTPException: If status cannot be retrieved.
    """
    try:
        status = await daemon.backend.get_stage_status(stage)
        return status

    except Exception as e:
        logger.error(f"Failed to get stage status for {stage.name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get stage status: {e}"
        )
