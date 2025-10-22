"""Main daemon class for the EW-51 motion control service."""

import logging
from typing import Optional

from suruga_seiki_ew51.models import DaemonState, StationStatus, StageId
from suruga_seiki_ew51.daemon.backend import AbstractBackend, MockBackend, RealBackend
from suruga_seiki_ew51.utils import ConnectionError

logger = logging.getLogger(__name__)


class EW51Daemon:
    """Main daemon for Suruga Seiki EW-51 motion control.

    The daemon manages the lifecycle of the backend (hardware or mock)
    and provides a high-level interface for the FastAPI application.
    """

    def __init__(self, use_mock: bool = False, dll_path: Optional[str] = None):
        """Initialize the daemon.

        Args:
            use_mock: If True, use mock backend instead of real hardware.
            dll_path: Path to srgmc.dll (only used for real backend).
        """
        self._use_mock = use_mock
        self._dll_path = dll_path
        self._state = DaemonState.STOPPED
        self._backend: Optional[AbstractBackend] = None

        logger.info(f"Daemon initialized (mock={use_mock})")

    @property
    def state(self) -> DaemonState:
        """Get current daemon state."""
        return self._state

    @property
    def backend(self) -> AbstractBackend:
        """Get the backend instance.

        Returns:
            The backend instance.

        Raises:
            RuntimeError: If daemon is not started.
        """
        if self._backend is None:
            raise RuntimeError("Daemon not started - backend not available")
        return self._backend

    @property
    def is_mock(self) -> bool:
        """Check if daemon is using mock backend."""
        return self._use_mock

    async def start(self) -> None:
        """Start the daemon and connect to the backend.

        Raises:
            ConnectionError: If backend connection fails.
        """
        if self._state != DaemonState.STOPPED:
            logger.warning(f"Daemon already in state {self._state}, cannot start")
            return

        logger.info("Starting daemon...")
        self._state = DaemonState.STARTING

        try:
            # Create backend
            if self._use_mock:
                logger.info("Using mock backend")
                self._backend = MockBackend()
            else:
                logger.info("Using real hardware backend")
                self._backend = RealBackend(dll_path=self._dll_path)

            # Connect to backend
            await self._backend.connect()

            self._state = DaemonState.READY
            logger.info("Daemon started and ready")

        except Exception as e:
            logger.error(f"Failed to start daemon: {e}")
            self._state = DaemonState.ERROR
            raise ConnectionError(f"Daemon startup failed: {e}")

    async def stop(self) -> None:
        """Stop the daemon and disconnect from the backend."""
        if self._state == DaemonState.STOPPED:
            logger.warning("Daemon already stopped")
            return

        logger.info("Stopping daemon...")
        self._state = DaemonState.STOPPING

        try:
            if self._backend:
                await self._backend.disconnect()
                self._backend = None

            self._state = DaemonState.STOPPED
            logger.info("Daemon stopped")

        except Exception as e:
            logger.error(f"Error during daemon shutdown: {e}")
            self._state = DaemonState.ERROR
            raise

    async def get_status(self) -> StationStatus:
        """Get complete station status.

        Returns:
            Complete station status including all axes and stages.

        Raises:
            RuntimeError: If daemon is not ready.
        """
        if self._state != DaemonState.READY:
            raise RuntimeError(f"Daemon not ready (state: {self._state})")

        # Get status for both stages
        left_stage = await self._backend.get_stage_status(StageId.LEFT)
        right_stage = await self._backend.get_stage_status(StageId.RIGHT)

        return StationStatus(
            daemon_state=self._state,
            left_stage=left_stage,
            right_stage=right_stage,
            is_mock=self._backend.is_mock,
            connection_established=self._backend.is_connected,
        )

    async def emergency_stop(self) -> None:
        """Trigger emergency stop on all axes."""
        logger.warning("Emergency stop triggered")
        if self._backend:
            await self._backend.emergency_stop()
