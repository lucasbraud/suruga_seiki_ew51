"""Real hardware backend using srgmc.dll via pythonnet.

This module integrates with the Suruga Seiki motion controller hardware
via the .NET DLL (srgmc.dll) using pythonnet (Python.NET).
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Optional

from suruga_seiki_ew51.models import AxisId, AxisStatus, StageStatus, StageId
from suruga_seiki_ew51.utils import (
    HardwareError,
    ConnectionError,
    MovementError,
    ServoError,
    TimeoutError,
)
from suruga_seiki_ew51.alignment import AlignmentController
from ..abstract import AbstractBackend

logger = logging.getLogger(__name__)


class RealBackend(AbstractBackend):
    """Real hardware backend for Suruga Seiki EW-51 motion controller.

    This backend communicates with the actual hardware via srgmc.dll.
    It requires:
    - pythonnet package installed
    - srgmc.dll in the correct location
    - Physical hardware connected and powered on
    """

    def __init__(
        self,
        dll_path: Optional[str] = None,
        ads_address: str = "5.107.162.80.1.1",
    ):
        """Initialize real hardware backend.

        Args:
            dll_path: Path to srgmc.dll (if None, looks in io/dll/ directory).
            ads_address: ADS network address for the controller.
        """
        super().__init__()
        self._dll_path = dll_path
        self._ads_address = ads_address
        self._system = None
        self._axis_components: Dict[int, any] = {}
        self._axis_2d = None
        self._alignment = None
        self._alignment_controller: Optional[AlignmentController] = None

        # Homing state tracking
        self._is_homed: Dict[AxisId, bool] = {axis: False for axis in AxisId}

        logger.info(f"Real backend initialized with ADS address: {ads_address}")

    @property
    def is_mock(self) -> bool:
        """Check if this is a mock backend."""
        return False

    def _load_dll(self) -> None:
        """Load the srgmc.dll library via pythonnet.

        Raises:
            ConnectionError: If DLL cannot be loaded.
        """
        try:
            import pythonnet
            import clr

            # Load .NET Core
            pythonnet.load("coreclr")

            # Determine DLL path
            if self._dll_path:
                dll_location = Path(self._dll_path).parent
            else:
                # Default to io/dll/ directory
                dll_location = (
                    Path(__file__).parent.parent.parent / "io" / "dll"
                )

            if not dll_location.exists():
                raise ConnectionError(
                    f"DLL directory not found: {dll_location}"
                )

            # Add DLL reference
            logger.info(f"Loading DLL from: {dll_location}")
            os.chdir(dll_location)
            clr.AddReference("srgmc")

            # Import DLL namespace
            import SurugaSeiki.Motion

            self._dll_module = SurugaSeiki.Motion
            logger.info("DLL loaded successfully")
            logger.info(f"DLL Version: {SurugaSeiki.Motion.System.Instance.DllVersion}")

        except Exception as e:
            logger.error(f"Failed to load DLL: {e}")
            raise ConnectionError(f"Failed to load srgmc.dll: {e}")

    async def connect(self) -> None:
        """Establish connection to the motion controller hardware.

        Raises:
            ConnectionError: If connection fails.
        """
        logger.info("Connecting to real hardware...")

        try:
            # Load DLL
            self._load_dll()

            # Get System instance
            self._system = self._dll_module.System.Instance

            # Create AxisComponents for all 12 axes
            for axis_num in range(1, 13):
                self._axis_components[axis_num] = self._dll_module.AxisComponents(
                    axis_num
                )
            logger.info("Created axis components for 12 axes")

            # Create Axis2D instance for stage 2 (axes 7, 8)
            self._axis_2d = self._dll_module.Axis2D(7, 8)

            # Create Alignment instance
            self._alignment = self._dll_module.Alignment()

            # Create alignment controller
            self._alignment_controller = AlignmentController(self._alignment)
            self._alignment_controller.set_dll_module(self._dll_module)

            # Set ADS address
            self._system.SetAddress(self._ads_address)
            logger.info(f"Set ADS address: {self._ads_address}")

            # Wait for connection
            max_retries = 10
            for i in range(max_retries):
                await asyncio.sleep(0.5)
                if self._system.Connected:
                    break
                logger.debug(f"Waiting for connection... ({i+1}/{max_retries})")
            else:
                raise ConnectionError(
                    f"Failed to connect after {max_retries} attempts"
                )

            # Connection successful
            self._connected = True
            logger.info(f"Connected to hardware. System version: {self._system.SystemVersion}")

            # Turn on servo for all axes
            for axis_num, component in self._axis_components.items():
                if not component.IsServoOn():
                    component.TurnOnServo()
                    logger.debug(f"Enabled servo for axis {axis_num}")

        except Exception as e:
            logger.error(f"Failed to connect to hardware: {e}")
            raise ConnectionError(f"Hardware connection failed: {e}")

    async def disconnect(self) -> None:
        """Close connection to the motion controller hardware."""
        logger.info("Disconnecting from real hardware...")

        try:
            if self._axis_components:
                # Disable servo on all axes before disconnecting
                for axis_num, component in self._axis_components.items():
                    try:
                        if component.IsServoOn():
                            component.TurnOffServo()
                            logger.debug(f"Disabled servo for axis {axis_num}")
                    except Exception as e:
                        logger.warning(f"Error disabling servo for axis {axis_num}: {e}")

            self._axis_components = {}
            self._axis_2d = None
            self._alignment = None
            self._system = None
            self._connected = False

            logger.info("Real backend disconnected")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            raise

    def _get_axis_component(self, axis: AxisId) -> any:
        """Get the DLL axis component for an axis ID.

        Args:
            axis: Axis identifier.

        Returns:
            DLL AxisComponents instance.

        Raises:
            HardwareError: If axis component not available.
        """
        if not self._connected:
            raise HardwareError("Backend not connected")

        component = self._axis_components.get(axis.value)
        if component is None:
            raise HardwareError(f"Axis component not found for {axis.name}")

        return component

    async def get_axis_position(self, axis: AxisId) -> float:
        """Get current position of an axis.

        Args:
            axis: Axis identifier.

        Returns:
            Current position in micrometers.

        Raises:
            HardwareError: If position cannot be read.
        """
        try:
            component = self._get_axis_component(axis)
            position = component.GetActualPosition()
            return float(position)
        except Exception as e:
            logger.error(f"Failed to get position for axis {axis.name}: {e}")
            raise HardwareError(f"Failed to get position: {e}")

    async def get_all_positions(self) -> Dict[AxisId, float]:
        """Get positions of all axes.

        Returns:
            Dictionary mapping axis IDs to positions in micrometers.

        Raises:
            HardwareError: If positions cannot be read.
        """
        if not self._connected:
            raise HardwareError("Backend not connected")

        positions = {}
        for axis in AxisId:
            try:
                positions[axis] = await self.get_axis_position(axis)
            except Exception as e:
                logger.error(f"Failed to get position for axis {axis.name}: {e}")
                raise HardwareError(f"Failed to get all positions: {e}")

        return positions

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
            speed: Movement speed (not implemented in DLL API).

        Raises:
            MovementError: If movement fails.
            ServoError: If servo is not enabled.
        """
        try:
            component = self._get_axis_component(axis)

            # Check servo is enabled
            if not component.IsServoOn():
                raise ServoError(f"Servo not enabled for axis {axis.name}")

            # Execute movement
            if relative:
                error = component.MoveRelative(float(target))
            else:
                error = component.MoveAbsolute(float(target))

            # Check for error
            if str(error) != "None":
                raise MovementError(
                    f"Movement failed for axis {axis.name}: {error}"
                )

            logger.debug(
                f"Started {'relative' if relative else 'absolute'} movement "
                f"for axis {axis.name} to {target}"
            )

        except (MovementError, ServoError):
            raise
        except Exception as e:
            logger.error(f"Failed to move axis {axis.name}: {e}")
            raise MovementError(f"Movement failed: {e}")

    async def is_axis_moving(self, axis: AxisId) -> bool:
        """Check if an axis is currently moving.

        Args:
            axis: Axis to check.

        Returns:
            True if axis is moving.

        Raises:
            HardwareError: If status cannot be determined.
        """
        try:
            component = self._get_axis_component(axis)
            status = str(component.GetStatus())
            # DLL returns "InPosition" when stopped
            return status != "InPosition"
        except Exception as e:
            logger.error(f"Failed to check if axis {axis.name} is moving: {e}")
            raise HardwareError(f"Failed to check motion status: {e}")

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
        component = self._get_axis_component(axis)

        start_time = asyncio.get_event_loop().time()
        poll_interval = 0.1

        while True:
            status = str(component.GetStatus())

            if status == "InPosition":
                logger.debug(f"Axis {axis.name} reached target position")
                return

            if status == "Error":
                raise MovementError(f"Movement error for axis {axis.name}")

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Motion did not complete within {timeout}s for axis {axis.name}"
                )

            await asyncio.sleep(poll_interval)

    async def enable_servo(self, axis: AxisId) -> None:
        """Enable servo control for an axis.

        Args:
            axis: Axis to enable.

        Raises:
            ServoError: If servo cannot be enabled.
        """
        try:
            component = self._get_axis_component(axis)
            component.TurnOnServo()
            logger.debug(f"Servo enabled for axis {axis.name}")
        except Exception as e:
            logger.error(f"Failed to enable servo for axis {axis.name}: {e}")
            raise ServoError(f"Failed to enable servo: {e}")

    async def disable_servo(self, axis: AxisId) -> None:
        """Disable servo control for an axis.

        Args:
            axis: Axis to disable.

        Raises:
            ServoError: If servo cannot be disabled.
        """
        try:
            component = self._get_axis_component(axis)
            component.TurnOffServo()
            logger.debug(f"Servo disabled for axis {axis.name}")
        except Exception as e:
            logger.error(f"Failed to disable servo for axis {axis.name}: {e}")
            raise ServoError(f"Failed to disable servo: {e}")

    async def is_servo_enabled(self, axis: AxisId) -> bool:
        """Check if servo is enabled for an axis.

        Args:
            axis: Axis to check.

        Returns:
            True if servo is enabled.

        Raises:
            HardwareError: If servo state cannot be determined.
        """
        try:
            component = self._get_axis_component(axis)
            return bool(component.IsServoOn())
        except Exception as e:
            logger.error(f"Failed to check servo state for axis {axis.name}: {e}")
            raise HardwareError(f"Failed to check servo state: {e}")

    async def home_axis(self, axis: AxisId) -> None:
        """Home an axis (move to position 0).

        Args:
            axis: Axis to home.

        Raises:
            MovementError: If homing fails.
        """
        try:
            # Move to position 0
            await self.move_axis(axis, 0.0, relative=False)
            await self.wait_for_motion_complete(axis, timeout=60.0)

            self._is_homed[axis] = True
            logger.info(f"Axis {axis.name} homed successfully")

        except Exception as e:
            logger.error(f"Failed to home axis {axis.name}: {e}")
            raise MovementError(f"Homing failed: {e}")

    async def get_axis_status(self, axis: AxisId) -> AxisStatus:
        """Get complete status information for an axis.

        Args:
            axis: Axis to query.

        Returns:
            Complete axis status.

        Raises:
            HardwareError: If status cannot be retrieved.
        """
        try:
            position = await self.get_axis_position(axis)
            servo_enabled = await self.is_servo_enabled(axis)
            is_moving = await self.is_axis_moving(axis)

            return AxisStatus(
                axis=axis,
                position=position,
                servo_enabled=servo_enabled,
                is_moving=is_moving,
                is_homed=self._is_homed[axis],
            )

        except Exception as e:
            logger.error(f"Failed to get status for axis {axis.name}: {e}")
            raise HardwareError(f"Failed to get axis status: {e}")

    async def get_stage_status(self, stage: StageId) -> StageStatus:
        """Get complete status for a stage (all its axes).

        Args:
            stage: Stage identifier.

        Returns:
            Complete stage status.

        Raises:
            HardwareError: If status cannot be retrieved.
        """
        if not self._connected:
            raise HardwareError("Backend not connected")

        try:
            # Determine which axes belong to this stage
            if stage == StageId.LEFT:
                axes = [
                    AxisId.X1,
                    AxisId.Y1,
                    AxisId.Z1,
                    AxisId.TX1,
                    AxisId.TY1,
                    AxisId.TZ1,
                ]
            else:  # StageId.RIGHT
                axes = [
                    AxisId.X2,
                    AxisId.Y2,
                    AxisId.Z2,
                    AxisId.TX2,
                    AxisId.TY2,
                    AxisId.TZ2,
                ]

            # Get status for all axes in this stage
            axes_status = [await self.get_axis_status(axis) for axis in axes]

            return StageStatus(
                stage_id=stage,
                axes=axes_status,
                angle_offset=0.0,  # TODO: Implement angle offset tracking
            )

        except Exception as e:
            logger.error(f"Failed to get stage status for {stage.name}: {e}")
            raise HardwareError(f"Failed to get stage status: {e}")

    async def emergency_stop(self) -> None:
        """Emergency stop all motion.

        Stops all axes immediately.
        """
        logger.warning("Emergency stop triggered on real hardware")

        if not self._connected:
            return

        try:
            # Turn off servo on all axes to stop motion
            for axis_num, component in self._axis_components.items():
                try:
                    if component.IsServoOn():
                        component.TurnOffServo()
                        logger.debug(f"Emergency stopped axis {axis_num}")
                except Exception as e:
                    logger.error(f"Failed to stop axis {axis_num}: {e}")

            logger.info("Emergency stop completed")

        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
            raise HardwareError(f"Emergency stop failed: {e}")

    def get_alignment_controller(self) -> AlignmentController:
        """Get the alignment controller.

        Returns:
            AlignmentController instance.

        Raises:
            HardwareError: If alignment system not available.
        """
        if not self._connected:
            raise HardwareError("Backend not connected")

        if self._alignment_controller is None:
            raise HardwareError("Alignment system not initialized")

        return self._alignment_controller
