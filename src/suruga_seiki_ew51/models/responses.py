"""Response models for API endpoints."""

from typing import Optional, List

from pydantic import BaseModel, Field

from .enums import AxisId, MovementStatus
from .base import Position, AxisStatus, StationStatus


class MovementResponse(BaseModel):
    """Response for movement operations."""

    axis: AxisId = Field(..., description="Axis that was moved")
    status: MovementStatus = Field(..., description="Movement status")
    current_position: float = Field(..., description="Current position in micrometers")
    target_position: float = Field(..., description="Target position in micrometers")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class MultiAxisMovementResponse(BaseModel):
    """Response for multi-axis movement operations."""

    movements: List[MovementResponse] = Field(
        ..., description="Results for each axis movement"
    )
    overall_status: MovementStatus = Field(
        ..., description="Overall status (error if any axis failed)"
    )


class ServoResponse(BaseModel):
    """Response for servo control operations."""

    axis: AxisId = Field(..., description="Axis controlled")
    enabled: bool = Field(..., description="Current servo state")
    success: bool = Field(..., description="Whether operation succeeded")


class PositionResponse(BaseModel):
    """Response for position query."""

    positions: List[Position] = Field(..., description="Positions of requested axes")


class StatusResponse(BaseModel):
    """Response for status queries."""

    station: StationStatus = Field(..., description="Complete station status")


class AlignmentResponse(BaseModel):
    """Response for alignment operations."""

    success: bool = Field(..., description="Whether alignment succeeded")
    message: str = Field(..., description="Result message")
    final_position: Optional[Position] = Field(
        None, description="Final position after alignment"
    )


class ConnectionResponse(BaseModel):
    """Response for connection operations."""

    connected: bool = Field(..., description="Whether connection is established")
    is_mock: bool = Field(..., description="Whether using mock backend")
    message: str = Field(..., description="Connection status message")


class HealthResponse(BaseModel):
    """Response for health check endpoint."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Software version")
    is_mock: bool = Field(..., description="Whether using mock backend")
