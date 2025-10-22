"""Mock backend for development and testing without hardware."""

import asyncio
import logging
from typing import Dict, Optional

from suruga_seiki_ew51.models import AxisId, AxisStatus, StageStatus, StageId
from suruga_seiki_ew51.utils import (
    HardwareError,
    MovementError,
    ServoError,
    TimeoutError,
)
from ..abstract import AbstractBackend

logger = logging.getLogger(__name__)


class MockBackend(AbstractBackend):
    """Mock backend simulating the Suruga Seiki EW-51 motion controller.

    This backend simulates hardware behavior without requiring physical
    hardware or the .NET DLL. It's useful for:
    - Development without hardware access
    - CI/CD testing
    - SDK development and testing
    - Demonstration purposes
    """

    def __init__(self):
        """Initialize mock backend with simulated state."""
        super().__init__()

        # Simulated axis positions (in micrometers)
        self._positions: Dict[AxisId, float] = {axis: 0.0 for axis in AxisId}

        # Simulated servo states
        self._servo_enabled: Dict[AxisId, bool] = {axis: False for axis in AxisId}

        # Simulated homing states
        self._is_homed: Dict[AxisId, bool] = {axis: False for axis in AxisId}

        # Simulated motion states
        self._is_moving: Dict[AxisId, bool] = {axis: False for axis in AxisId}

        # Movement simulation tasks
        self._motion_tasks: Dict[AxisId, Optional[asyncio.Task]] = {
            axis: None for axis in AxisId
        }

        # Default movement speed (um/s)
        self._default_speed = 1000.0

        logger.info("Mock backend initialized")

    @property
    def is_mock(self) -> bool:
        """Check if this is a mock backend."""
        return True

    async def connect(self) -> None:
        """Establish mock connection."""
        logger.info("Connecting to mock backend...")
        await asyncio.sleep(0.1)  # Simulate connection delay
        self._connected = True
        logger.info("Mock backend connected")

    async def disconnect(self) -> None:
        """Close mock connection."""
        logger.info("Disconnecting mock backend...")

        # Cancel any ongoing motion tasks
        for axis, task in self._motion_tasks.items():
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._connected = False
        logger.info("Mock backend disconnected")

    async def get_axis_position(self, axis: AxisId) -> float:
        """Get current position of an axis."""
        if not self._connected:
            raise HardwareError("Backend not connected")
        return self._positions[axis]

    async def get_all_positions(self) -> Dict[AxisId, float]:
        """Get positions of all axes."""
        if not self._connected:
            raise HardwareError("Backend not connected")
        return self._positions.copy()

    async def _simulate_motion(
        self, axis: AxisId, start: float, target: float, speed: float
    ) -> None:
        """Simulate gradual axis motion.

        Args:
            axis: Axis to move.
            start: Starting position.
            target: Target position.
            speed: Movement speed in um/s.
        """
        distance = abs(target - start)
        duration = distance / speed if speed > 0 else 0
        steps = max(int(duration * 10), 1)  # 10 updates per second

        self._is_moving[axis] = True

        try:
            for i in range(steps + 1):
                progress = i / steps
                self._positions[axis] = start + (target - start) * progress
                await asyncio.sleep(duration / steps)

            self._positions[axis] = target
        finally:
            self._is_moving[axis] = False
            self._motion_tasks[axis] = None

    async def move_axis(
        self,
        axis: AxisId,
        target: float,
        relative: bool = False,
        speed: Optional[float] = None,
    ) -> None:
        """Move an axis to target position."""
        if not self._connected:
            raise HardwareError("Backend not connected")

        if not self._servo_enabled[axis]:
            raise ServoError(f"Servo not enabled for axis {axis.name}")

        # Cancel any existing motion for this axis
        if self._motion_tasks[axis] and not self._motion_tasks[axis].done():
            self._motion_tasks[axis].cancel()
            try:
                await self._motion_tasks[axis]
            except asyncio.CancelledError:
                pass

        # Calculate actual target
        start_pos = self._positions[axis]
        actual_target = start_pos + target if relative else target

        # Validate target is within reasonable bounds (±500mm)
        if abs(actual_target) > 500_000:
            raise MovementError(
                f"Target position {actual_target} exceeds bounds for axis {axis.name}"
            )

        # Start motion simulation
        motion_speed = speed if speed is not None else self._default_speed
        self._motion_tasks[axis] = asyncio.create_task(
            self._simulate_motion(axis, start_pos, actual_target, motion_speed)
        )

        logger.debug(
            f"Moving axis {axis.name} from {start_pos:.2f} to {actual_target:.2f} "
            f"at {motion_speed:.2f} um/s"
        )

    async def is_axis_moving(self, axis: AxisId) -> bool:
        """Check if an axis is currently moving."""
        if not self._connected:
            raise HardwareError("Backend not connected")
        return self._is_moving[axis]

    async def wait_for_motion_complete(
        self, axis: AxisId, timeout: float = 30.0
    ) -> None:
        """Wait for axis motion to complete."""
        if not self._connected:
            raise HardwareError("Backend not connected")

        task = self._motion_tasks[axis]
        if task is None or task.done():
            return  # No motion in progress

        try:
            await asyncio.wait_for(task, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Motion did not complete within {timeout}s for axis {axis.name}"
            )

    async def enable_servo(self, axis: AxisId) -> None:
        """Enable servo control for an axis."""
        if not self._connected:
            raise HardwareError("Backend not connected")

        self._servo_enabled[axis] = True
        logger.debug(f"Servo enabled for axis {axis.name}")

    async def disable_servo(self, axis: AxisId) -> None:
        """Disable servo control for an axis."""
        if not self._connected:
            raise HardwareError("Backend not connected")

        # Stop any ongoing motion before disabling servo
        if self._is_moving[axis]:
            task = self._motion_tasks[axis]
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._servo_enabled[axis] = False
        logger.debug(f"Servo disabled for axis {axis.name}")

    async def is_servo_enabled(self, axis: AxisId) -> bool:
        """Check if servo is enabled for an axis."""
        if not self._connected:
            raise HardwareError("Backend not connected")
        return self._servo_enabled[axis]

    async def home_axis(self, axis: AxisId) -> None:
        """Home an axis (move to position 0)."""
        if not self._connected:
            raise HardwareError("Backend not connected")

        if not self._servo_enabled[axis]:
            raise ServoError(f"Servo not enabled for axis {axis.name}")

        # Move to home position (0)
        await self.move_axis(axis, 0.0, relative=False)
        await self.wait_for_motion_complete(axis)
        self._is_homed[axis] = True
        logger.info(f"Axis {axis.name} homed")

    async def get_axis_status(self, axis: AxisId) -> AxisStatus:
        """Get complete status information for an axis."""
        if not self._connected:
            raise HardwareError("Backend not connected")

        return AxisStatus(
            axis=axis,
            position=self._positions[axis],
            servo_enabled=self._servo_enabled[axis],
            is_moving=self._is_moving[axis],
            is_homed=self._is_homed[axis],
        )

    async def get_stage_status(self, stage: StageId) -> StageStatus:
        """Get complete status for a stage (all its axes)."""
        if not self._connected:
            raise HardwareError("Backend not connected")

        # Determine which axes belong to this stage
        if stage == StageId.LEFT:
            axes = [AxisId.X1, AxisId.Y1, AxisId.Z1, AxisId.TX1, AxisId.TY1, AxisId.TZ1]
        else:  # StageId.RIGHT
            axes = [AxisId.X2, AxisId.Y2, AxisId.Z2, AxisId.TX2, AxisId.TY2, AxisId.TZ2]

        # Get status for all axes in this stage
        axes_status = [await self.get_axis_status(axis) for axis in axes]

        return StageStatus(
            stage_id=stage,
            axes=axes_status,
            angle_offset=0.0,  # Mock backend doesn't simulate angle offset
        )

    async def emergency_stop(self) -> None:
        """Emergency stop all motion."""
        logger.warning("Emergency stop triggered on mock backend")

        for axis in AxisId:
            if self._is_moving[axis]:
                task = self._motion_tasks[axis]
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

        logger.info("All motion stopped")
