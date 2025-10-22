"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from suruga_seiki_ew51.models import (
    AxisId,
    StageId,
    Position,
    MovementRequest,
    ServoRequest,
    AxisStatus,
)


class TestModels:
    """Test suite for Pydantic models."""

    def test_position_model(self):
        """Test Position model."""
        pos = Position(axis=AxisId.X1, value=1000.0)
        assert pos.axis == AxisId.X1
        assert pos.value == 1000.0

        # Test immutability (frozen model)
        with pytest.raises(ValidationError):
            pos.value = 2000.0

    def test_movement_request_validation(self):
        """Test MovementRequest validation."""
        # Valid request
        req = MovementRequest(axis=AxisId.X1, target=1000.0)
        assert req.axis == AxisId.X1
        assert req.target == 1000.0
        assert not req.relative
        assert req.wait

        # Invalid target (too large)
        with pytest.raises(ValidationError):
            MovementRequest(axis=AxisId.X1, target=2_000_000.0)

    def test_servo_request(self):
        """Test ServoRequest model."""
        req = ServoRequest(axes=[AxisId.X1, AxisId.Y1], enabled=True)
        assert len(req.axes) == 2
        assert req.enabled

    def test_axis_status(self):
        """Test AxisStatus model."""
        status = AxisStatus(
            axis=AxisId.X1,
            position=1000.0,
            servo_enabled=True,
            is_moving=False,
            is_homed=True,
        )
        assert status.axis == AxisId.X1
        assert status.position == 1000.0
        assert status.servo_enabled
        assert not status.is_moving
        assert status.is_homed

    def test_axis_id_enum(self):
        """Test AxisId enum."""
        # Test left stage axes
        assert AxisId.X1.value == 1
        assert AxisId.Y1.value == 2
        assert AxisId.Z1.value == 3

        # Test right stage axes
        assert AxisId.X2.value == 7
        assert AxisId.Y2.value == 8
        assert AxisId.Z2.value == 9

    def test_stage_id_enum(self):
        """Test StageId enum."""
        assert StageId.LEFT.value == 1
        assert StageId.RIGHT.value == 2
