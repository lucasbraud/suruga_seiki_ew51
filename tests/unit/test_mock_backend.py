"""Tests for the mock backend."""

import pytest

from suruga_seiki_ew51.models import AxisId, StageId
from suruga_seiki_ew51.utils import HardwareError, ServoError


@pytest.mark.mock
class TestMockBackend:
    """Test suite for MockBackend."""

    async def test_connection(self, mock_backend):
        """Test backend connection."""
        assert mock_backend.is_connected
        assert mock_backend.is_mock

    async def test_get_axis_position(self, mock_backend, axis):
        """Test getting axis position."""
        position = await mock_backend.get_axis_position(axis)
        assert position == 0.0  # Initial position

    async def test_get_all_positions(self, mock_backend):
        """Test getting all positions."""
        positions = await mock_backend.get_all_positions()
        assert len(positions) == len(AxisId)
        assert all(pos == 0.0 for pos in positions.values())

    async def test_servo_enable_disable(self, mock_backend, axis):
        """Test servo enable/disable."""
        # Initially disabled
        assert not await mock_backend.is_servo_enabled(axis)

        # Enable
        await mock_backend.enable_servo(axis)
        assert await mock_backend.is_servo_enabled(axis)

        # Disable
        await mock_backend.disable_servo(axis)
        assert not await mock_backend.is_servo_enabled(axis)

    async def test_move_axis_without_servo(self, mock_backend, axis):
        """Test that movement fails without servo enabled."""
        with pytest.raises(ServoError):
            await mock_backend.move_axis(axis, 1000.0)

    async def test_move_axis_absolute(self, mock_backend, axis):
        """Test absolute axis movement."""
        await mock_backend.enable_servo(axis)

        target = 1000.0
        await mock_backend.move_axis(axis, target, relative=False)
        await mock_backend.wait_for_motion_complete(axis, timeout=5.0)

        position = await mock_backend.get_axis_position(axis)
        assert abs(position - target) < 0.1  # Allow small tolerance

    async def test_move_axis_relative(self, mock_backend, axis):
        """Test relative axis movement."""
        await mock_backend.enable_servo(axis)

        # Move to 1000
        await mock_backend.move_axis(axis, 1000.0, relative=False)
        await mock_backend.wait_for_motion_complete(axis, timeout=5.0)

        # Move relative +500
        await mock_backend.move_axis(axis, 500.0, relative=True)
        await mock_backend.wait_for_motion_complete(axis, timeout=5.0)

        position = await mock_backend.get_axis_position(axis)
        assert abs(position - 1500.0) < 0.1

    async def test_is_axis_moving(self, mock_backend, axis):
        """Test checking if axis is moving."""
        await mock_backend.enable_servo(axis)

        # Not moving initially
        assert not await mock_backend.is_axis_moving(axis)

        # Start movement (don't wait)
        await mock_backend.move_axis(axis, 10000.0, relative=False)

        # Should be moving (or might have already completed if very fast)
        # We'll just check it doesn't raise an error
        moving = await mock_backend.is_axis_moving(axis)
        assert isinstance(moving, bool)

        # Wait for completion
        await mock_backend.wait_for_motion_complete(axis, timeout=10.0)

        # Should be done moving
        assert not await mock_backend.is_axis_moving(axis)

    async def test_home_axis(self, mock_backend, axis):
        """Test homing an axis."""
        await mock_backend.enable_servo(axis)

        # Move away from home
        await mock_backend.move_axis(axis, 1000.0, relative=False)
        await mock_backend.wait_for_motion_complete(axis, timeout=5.0)

        # Home axis
        await mock_backend.home_axis(axis)
        await mock_backend.wait_for_motion_complete(axis, timeout=5.0)

        # Should be at position 0
        position = await mock_backend.get_axis_position(axis)
        assert abs(position) < 0.1

    async def test_get_axis_status(self, mock_backend, axis):
        """Test getting axis status."""
        await mock_backend.enable_servo(axis)

        status = await mock_backend.get_axis_status(axis)

        assert status.axis == axis
        assert status.servo_enabled
        assert not status.is_moving
        assert status.position == 0.0

    async def test_get_stage_status(self, mock_backend):
        """Test getting stage status."""
        status = await mock_backend.get_stage_status(StageId.LEFT)

        assert status.stage_id == StageId.LEFT
        assert len(status.axes) == 6  # Left stage has 6 axes
        assert all(not axis.servo_enabled for axis in status.axes)

    async def test_emergency_stop(self, mock_backend, axis):
        """Test emergency stop."""
        await mock_backend.enable_servo(axis)

        # Start long movement
        await mock_backend.move_axis(axis, 100000.0, relative=False)

        # Emergency stop
        await mock_backend.emergency_stop()

        # Movement should be stopped
        assert not await mock_backend.is_axis_moving(axis)

    async def test_disconnect_stops_motion(self, mock_backend, axis):
        """Test that disconnecting stops all motion."""
        await mock_backend.enable_servo(axis)

        # Start movement
        await mock_backend.move_axis(axis, 100000.0, relative=False)

        # Disconnect
        await mock_backend.disconnect()

        # Should not be connected
        assert not mock_backend.is_connected

    async def test_operations_fail_when_disconnected(self):
        """Test that operations fail when backend is disconnected."""
        backend = MockBackend()  # Not connected

        with pytest.raises(HardwareError):
            await backend.get_axis_position(AxisId.X1)

        with pytest.raises(HardwareError):
            await backend.enable_servo(AxisId.X1)
