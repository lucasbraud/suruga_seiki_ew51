"""Request models for API endpoints."""

from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

from .enums import AxisId, StageId, AlignmentMode


class MovementRequest(BaseModel):
    """Request for single-axis movement."""

    axis: AxisId = Field(..., description="Axis to move")
    target: float = Field(..., description="Target position in micrometers")
    relative: bool = Field(False, description="Whether movement is relative")
    speed: Optional[float] = Field(
        None, description="Movement speed (if None, use default)"
    )
    wait: bool = Field(
        True, description="Whether to wait for movement completion"
    )

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: float) -> float:
        """Validate target position is within reasonable bounds."""
        if abs(v) > 1_000_000:  # 1 meter
            raise ValueError("Target position exceeds reasonable bounds (±1m)")
        return v


class MultiAxisMovementRequest(BaseModel):
    """Request for simultaneous multi-axis movement."""

    movements: List[MovementRequest] = Field(
        ..., description="List of movement requests to execute simultaneously"
    )
    wait: bool = Field(
        True, description="Whether to wait for all movements to complete"
    )


class Stage2DMovementRequest(BaseModel):
    """Request for 2D movement on a stage (X, Y)."""

    stage: StageId = Field(..., description="Stage identifier")
    x: float = Field(..., description="X position in micrometers")
    y: float = Field(..., description="Y position in micrometers")
    relative: bool = Field(False, description="Whether movement is relative")
    wait: bool = Field(True, description="Whether to wait for completion")


class ServoRequest(BaseModel):
    """Request to enable/disable servo on axes."""

    axes: List[AxisId] = Field(..., description="Axes to control")
    enabled: bool = Field(..., description="Whether to enable or disable servo")


class AlignmentRequest(BaseModel):
    """Request for optical alignment operation."""

    stage: StageId = Field(..., description="Stage to align")
    mode: AlignmentMode = Field(..., description="Alignment mode")
    parameters: Optional[dict] = Field(
        None, description="Mode-specific alignment parameters"
    )


class CalibrationRequest(BaseModel):
    """Request to set calibration data for a stage."""

    stage: StageId = Field(..., description="Stage to calibrate")
    angle_offset: float = Field(
        ..., description="Angular offset in degrees"
    )

    @field_validator("angle_offset")
    @classmethod
    def validate_angle(cls, v: float) -> float:
        """Validate angle is within ±360 degrees."""
        if abs(v) > 360:
            raise ValueError("Angle offset must be within ±360 degrees")
        return v


class HomeRequest(BaseModel):
    """Request to home axes."""

    axes: List[AxisId] = Field(..., description="Axes to home")
    wait: bool = Field(True, description="Whether to wait for homing to complete")
