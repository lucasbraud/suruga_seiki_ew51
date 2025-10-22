"""Abstract backend interface for Suruga Seiki EW-51 motion control.

This module defines the abstract interface that both real (hardware) and mock
backends must implement. This abstraction allows seamless switching between
physical hardware and simulation for development and testing.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from suruga_seiki_ew51.models import AxisId, AxisStatus, StageStatus, StageId


class AbstractBackend(ABC):
    """Abstract backend interface for motion control operations.

    All backend implementations (real hardware via DLL, mock simulation, etc.)
    must implement this interface to ensure consistent behavior across the
    daemon and SDK layers.
    """

    def __init__(self):
        """Initialize the backend."""
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Check if backend is connected and ready.

        Returns:
            True if backend is connected and operational.
        """
        return self._connected

    @property
    @abstractmethod
    def is_mock(self) -> bool:
        """Check if this is a mock backend.

        Returns:
            True if this is a mock/simulation backend.
        """
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the motion controller.

        For real backends: Initialize DLL, open network connection.
        For mock backends: Initialize simulation state.

        Raises:
            ConnectionError: If connection fails.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the motion controller.

        Should safely close all resources and connections.
        """
        pass

    @abstractmethod
    async def get_axis_position(self, axis: AxisId) -> float:
        """Get current position of an axis.

        Args:
            axis: Axis identifier.

        Returns:
            Current position in micrometers.

        Raises:
            HardwareError: If position cannot be read.
        """
        pass

    @abstractmethod
    async def get_all_positions(self) -> Dict[AxisId, float]:
        """Get positions of all axes.

        Returns:
            Dictionary mapping axis IDs to positions in micrometers.

        Raises:
            HardwareError: If positions cannot be read.
        """
        pass

    @abstractmethod
    async def move_axis(
        self,
        axis: AxisId,
        target: float,
        relative: bool = False,
        speed: Optional[float] = None,
    ) -> None:
        """Move an axis to target position.

        Args:
            axis: Axis to move.
            target: Target position in micrometers (or displacement if relative).
            relative: If True, target is relative to current position.
            speed: Movement speed (None = use default).

        Raises:
            MovementError: If movement fails.
            ServoError: If servo is not enabled.
        """
        pass

    @abstractmethod
    async def is_axis_moving(self, axis: AxisId) -> bool:
        """Check if an axis is currently moving.

        Args:
            axis: Axis to check.

        Returns:
            True if axis is moving.

        Raises:
            HardwareError: If status cannot be determined.
        """
        pass

    @abstractmethod
    async def wait_for_motion_complete(
        self, axis: AxisId, timeout: float = 30.0
    ) -> None:
        """Wait for axis motion to complete.

        Args:
            axis: Axis to wait for.
            timeout: Maximum time to wait in seconds.

        Raises:
            TimeoutError: If motion does not complete within timeout.
            MovementError: If motion fails.
        """
        pass

    @abstractmethod
    async def enable_servo(self, axis: AxisId) -> None:
        """Enable servo control for an axis.

        Args:
            axis: Axis to enable.

        Raises:
            ServoError: If servo cannot be enabled.
        """
        pass

    @abstractmethod
    async def disable_servo(self, axis: AxisId) -> None:
        """Disable servo control for an axis.

        Args:
            axis: Axis to disable.

        Raises:
            ServoError: If servo cannot be disabled.
        """
        pass

    @abstractmethod
    async def is_servo_enabled(self, axis: AxisId) -> bool:
        """Check if servo is enabled for an axis.

        Args:
            axis: Axis to check.

        Returns:
            True if servo is enabled.

        Raises:
            HardwareError: If servo state cannot be determined.
        """
        pass

    @abstractmethod
    async def home_axis(self, axis: AxisId) -> None:
        """Home an axis (move to home position).

        Args:
            axis: Axis to home.

        Raises:
            MovementError: If homing fails.
        """
        pass

    @abstractmethod
    async def get_axis_status(self, axis: AxisId) -> AxisStatus:
        """Get complete status information for an axis.

        Args:
            axis: Axis to query.

        Returns:
            Complete axis status.

        Raises:
            HardwareError: If status cannot be retrieved.
        """
        pass

    @abstractmethod
    async def get_stage_status(self, stage: StageId) -> StageStatus:
        """Get complete status for a stage (all its axes).

        Args:
            stage: Stage identifier.

        Returns:
            Complete stage status.

        Raises:
            HardwareError: If status cannot be retrieved.
        """
        pass

    async def emergency_stop(self) -> None:
        """Emergency stop all motion.

        This is optional to implement but recommended for safety.
        Default implementation does nothing.
        """
        pass
