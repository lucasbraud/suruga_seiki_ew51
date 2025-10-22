"""Base Pydantic models for API schemas."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from .enums import (
    AxisId,
    StageId,
    ServoState,
    MovementStatus,
    AlignmentMode,
    DaemonState,
)


class Position(BaseModel):
    """Position data for a single axis."""

    model_config = ConfigDict(frozen=True)

    axis: AxisId = Field(..., description="Axis identifier")
    value: float = Field(..., description="Position value in micrometers")


class Position3D(BaseModel):
    """3D position coordinates."""

    model_config = ConfigDict(frozen=True)

    x: float = Field(..., description="X coordinate in micrometers")
    y: float = Field(..., description="Y coordinate in micrometers")
    z: float = Field(..., description="Z coordinate in micrometers")


class AxisStatus(BaseModel):
    """Status information for a single axis."""

    axis: AxisId = Field(..., description="Axis identifier")
    position: float = Field(..., description="Current position in micrometers")
    servo_enabled: bool = Field(..., description="Whether servo is enabled")
    is_moving: bool = Field(..., description="Whether axis is currently moving")
    is_homed: bool = Field(False, description="Whether axis has been homed")


class StageStatus(BaseModel):
    """Status information for a stage (collection of axes)."""

    stage_id: StageId = Field(..., description="Stage identifier")
    axes: List[AxisStatus] = Field(..., description="Status of all axes in stage")
    angle_offset: float = Field(
        0.0, description="Current angular offset for this stage in degrees"
    )


class StationStatus(BaseModel):
    """Overall status of the motion control station."""

    daemon_state: DaemonState = Field(..., description="Current daemon state")
    left_stage: Optional[StageStatus] = Field(None, description="Left stage status")
    right_stage: Optional[StageStatus] = Field(None, description="Right stage status")
    is_mock: bool = Field(..., description="Whether using mock backend")
    connection_established: bool = Field(
        ..., description="Whether connection to controller is established"
    )


class ErrorResponse(BaseModel):
    """Error response schema."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, any]] = Field(None, description="Additional error details")
