"""Movement control endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from suruga_seiki_ew51.models import (
    MovementRequest,
    MovementResponse,
    MultiAxisMovementRequest,
    MultiAxisMovementResponse,
    PositionResponse,
    Position,
    AxisId,
    MovementStatus,
    HomeRequest,
)
from suruga_seiki_ew51.daemon.daemon import EW51Daemon
from suruga_seiki_ew51.utils import MovementError, ServoError

logger = logging.getLogger(__name__)

router = APIRouter()


from suruga_seiki_ew51.daemon.app.dependencies import get_daemon


@router.post("/move", response_model=MovementResponse)
async def move_axis(
    request: MovementRequest, daemon: EW51Daemon = Depends(get_daemon)
):
    """Move a single axis to target position.

    Args:
        request: Movement request containing axis, target, and parameters.

    Returns:
        Movement response with status and final position.

    Raises:
        HTTPException: If movement fails.
    """
    logger.info(
        f"Moving axis {request.axis.name} to {request.target} "
        f"({'relative' if request.relative else 'absolute'})"
    )

    try:
        # Execute movement
        await daemon.backend.move_axis(
            axis=request.axis,
            target=request.target,
            relative=request.relative,
            speed=request.speed,
        )

        # Wait for completion if requested
        if request.wait:
            await daemon.backend.wait_for_motion_complete(request.axis, timeout=30.0)

        # Get final position
        position = await daemon.backend.get_axis_position(request.axis)

        return MovementResponse(
            axis=request.axis,
            status=MovementStatus.COMPLETED,
            current_position=position,
            target_position=request.target if not request.relative else position,
        )

    except ServoError as e:
        logger.error(f"Servo error during movement: {e}")
        position = await daemon.backend.get_axis_position(request.axis)
        return MovementResponse(
            axis=request.axis,
            status=MovementStatus.ERROR,
            current_position=position,
            target_position=request.target,
            error_message=str(e),
        )

    except MovementError as e:
        logger.error(f"Movement error: {e}")
        position = await daemon.backend.get_axis_position(request.axis)
        return MovementResponse(
            axis=request.axis,
            status=MovementStatus.ERROR,
            current_position=position,
            target_position=request.target,
            error_message=str(e),
        )

    except Exception as e:
        logger.error(f"Unexpected error during movement: {e}")
        raise HTTPException(status_code=500, detail=f"Movement failed: {e}")


@router.post("/move/multi", response_model=MultiAxisMovementResponse)
async def move_multiple_axes(
    request: MultiAxisMovementRequest, daemon: EW51Daemon = Depends(get_daemon)
):
    """Move multiple axes simultaneously.

    Args:
        request: Multi-axis movement request.

    Returns:
        Multi-axis movement response with individual results.

    Raises:
        HTTPException: If movement fails.
    """
    logger.info(f"Moving {len(request.movements)} axes simultaneously")

    responses: List[MovementResponse] = []
    overall_status = MovementStatus.COMPLETED

    # Start all movements
    for move_req in request.movements:
        try:
            await daemon.backend.move_axis(
                axis=move_req.axis,
                target=move_req.target,
                relative=move_req.relative,
                speed=move_req.speed,
            )
        except Exception as e:
            logger.error(f"Failed to start movement for axis {move_req.axis.name}: {e}")
            overall_status = MovementStatus.ERROR

    # Wait for all movements if requested
    if request.wait:
        for move_req in request.movements:
            try:
                await daemon.backend.wait_for_motion_complete(move_req.axis, timeout=30.0)
                position = await daemon.backend.get_axis_position(move_req.axis)

                responses.append(
                    MovementResponse(
                        axis=move_req.axis,
                        status=MovementStatus.COMPLETED,
                        current_position=position,
                        target_position=move_req.target if not move_req.relative else position,
                    )
                )

            except Exception as e:
                logger.error(f"Movement failed for axis {move_req.axis.name}: {e}")
                position = await daemon.backend.get_axis_position(move_req.axis)

                responses.append(
                    MovementResponse(
                        axis=move_req.axis,
                        status=MovementStatus.ERROR,
                        current_position=position,
                        target_position=move_req.target,
                        error_message=str(e),
                    )
                )
                overall_status = MovementStatus.ERROR

    else:
        # Just get current positions without waiting
        for move_req in request.movements:
            position = await daemon.backend.get_axis_position(move_req.axis)
            responses.append(
                MovementResponse(
                    axis=move_req.axis,
                    status=MovementStatus.MOVING,
                    current_position=position,
                    target_position=move_req.target,
                )
            )

    return MultiAxisMovementResponse(
        movements=responses,
        overall_status=overall_status,
    )


@router.get("/position/{axis}", response_model=Position)
async def get_axis_position(axis: AxisId, daemon: EW51Daemon = Depends(get_daemon)):
    """Get current position of a single axis.

    Args:
        axis: Axis identifier.

    Returns:
        Current position of the axis.

    Raises:
        HTTPException: If position cannot be retrieved.
    """
    try:
        position = await daemon.backend.get_axis_position(axis)
        return Position(axis=axis, value=position)

    except Exception as e:
        logger.error(f"Failed to get position for axis {axis.name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get position: {e}")


@router.get("/positions", response_model=PositionResponse)
async def get_all_positions(daemon: EW51Daemon = Depends(get_daemon)):
    """Get current positions of all axes.

    Returns:
        Positions of all axes.

    Raises:
        HTTPException: If positions cannot be retrieved.
    """
    try:
        positions_dict = await daemon.backend.get_all_positions()
        positions = [
            Position(axis=axis, value=pos) for axis, pos in positions_dict.items()
        ]
        return PositionResponse(positions=positions)

    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {e}")


@router.post("/home")
async def home_axes(request: HomeRequest, daemon: EW51Daemon = Depends(get_daemon)):
    """Home specified axes.

    Args:
        request: Home request containing axes to home.

    Returns:
        Status of homing operation.

    Raises:
        HTTPException: If homing fails.
    """
    logger.info(f"Homing axes: {[a.name for a in request.axes]}")

    results = {}
    for axis in request.axes:
        try:
            await daemon.backend.home_axis(axis)

            if request.wait:
                await daemon.backend.wait_for_motion_complete(axis, timeout=60.0)

            results[axis.name] = "homed"
            logger.info(f"Axis {axis.name} homed successfully")

        except Exception as e:
            logger.error(f"Failed to home axis {axis.name}: {e}")
            results[axis.name] = f"error: {e}"

    return {"homing_results": results}
