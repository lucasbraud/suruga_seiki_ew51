"""SDK client for the Suruga Seiki EW-51 motion control API."""

import logging
from typing import List, Optional

import httpx

from suruga_seiki_ew51.models import (
    AxisId,
    StageId,
    MovementRequest,
    MovementResponse,
    MultiAxisMovementRequest,
    MultiAxisMovementResponse,
    ServoRequest,
    ServoResponse,
    Position,
    PositionResponse,
    StatusResponse,
    AxisStatus,
    StageStatus,
    HomeRequest,
    HealthResponse,
    FlatAlignmentParameters,
    FocusAlignmentParameters,
    AlignmentStatusResponse,
    AlignmentResultResponse,
    ProfileDataType,
    ProfileData,
)

logger = logging.getLogger(__name__)


class EW51Client:
    """High-level client for the EW-51 motion control API.

    This client provides a clean Python interface to control the motion
    system via the daemon's REST API.

    Example:
        ```python
        async with EW51Client("http://localhost:8000") as client:
            await client.enable_servo([AxisId.X1])
            await client.move_axis(AxisId.X1, 1000.0, wait=True)
            position = await client.get_position(AxisId.X1)
        ```
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
    ):
        """Initialize the client.

        Args:
            base_url: Base URL of the daemon API.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client.

        Returns:
            The async HTTP client.

        Raises:
            RuntimeError: If client is not initialized.
        """
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return self._client

    async def health(self) -> HealthResponse:
        """Get health status of the daemon.

        Returns:
            Health status response.
        """
        response = await self.client.get("/ew51/health")
        response.raise_for_status()
        return HealthResponse(**response.json())

    async def get_status(self) -> StatusResponse:
        """Get complete station status.

        Returns:
            Complete status including all axes and stages.
        """
        response = await self.client.get("/ew51/status")
        response.raise_for_status()
        return StatusResponse(**response.json())

    async def get_axis_status(self, axis: AxisId) -> AxisStatus:
        """Get status for a specific axis.

        Args:
            axis: Axis identifier.

        Returns:
            Status of the specified axis.
        """
        response = await self.client.get(f"/ew51/status/axis/{axis.value}")
        response.raise_for_status()
        return AxisStatus(**response.json())

    async def get_stage_status(self, stage: StageId) -> StageStatus:
        """Get status for a specific stage.

        Args:
            stage: Stage identifier.

        Returns:
            Status of the specified stage.
        """
        response = await self.client.get(f"/ew51/status/stage/{stage.value}")
        response.raise_for_status()
        return StageStatus(**response.json())

    async def enable_servo(self, axes: List[AxisId]) -> List[ServoResponse]:
        """Enable servo on specified axes.

        Args:
            axes: List of axes to enable servo on.

        Returns:
            List of servo responses for each axis.
        """
        request = ServoRequest(axes=axes, enabled=True)
        response = await self.client.post(
            "/ew51/servo/enable",
            json=request.model_dump(),
        )
        response.raise_for_status()
        return [ServoResponse(**r) for r in response.json()]

    async def disable_servo(self, axes: List[AxisId]) -> List[ServoResponse]:
        """Disable servo on specified axes.

        Args:
            axes: List of axes to disable servo on.

        Returns:
            List of servo responses for each axis.
        """
        request = ServoRequest(axes=axes, enabled=False)
        response = await self.client.post(
            "/ew51/servo/disable",
            json=request.model_dump(),
        )
        response.raise_for_status()
        return [ServoResponse(**r) for r in response.json()]

    async def move_axis(
        self,
        axis: AxisId,
        target: float,
        relative: bool = False,
        speed: Optional[float] = None,
        wait: bool = True,
    ) -> MovementResponse:
        """Move a single axis.

        Args:
            axis: Axis to move.
            target: Target position in micrometers (or displacement if relative).
            relative: If True, target is relative to current position.
            speed: Movement speed (None = use default).
            wait: If True, wait for movement to complete.

        Returns:
            Movement response with final status and position.
        """
        request = MovementRequest(
            axis=axis,
            target=target,
            relative=relative,
            speed=speed,
            wait=wait,
        )
        response = await self.client.post(
            "/ew51/move",
            json=request.model_dump(),
        )
        response.raise_for_status()
        return MovementResponse(**response.json())

    async def move_multiple_axes(
        self,
        movements: List[MovementRequest],
        wait: bool = True,
    ) -> MultiAxisMovementResponse:
        """Move multiple axes simultaneously.

        Args:
            movements: List of movement requests.
            wait: If True, wait for all movements to complete.

        Returns:
            Multi-axis movement response.
        """
        request = MultiAxisMovementRequest(movements=movements, wait=wait)
        response = await self.client.post(
            "/ew51/move/multi",
            json=request.model_dump(),
        )
        response.raise_for_status()
        return MultiAxisMovementResponse(**response.json())

    async def get_position(self, axis: AxisId) -> float:
        """Get current position of an axis.

        Args:
            axis: Axis identifier.

        Returns:
            Current position in micrometers.
        """
        response = await self.client.get(f"/ew51/position/{axis.value}")
        response.raise_for_status()
        position = Position(**response.json())
        return position.value

    async def get_all_positions(self) -> PositionResponse:
        """Get positions of all axes.

        Returns:
            Positions of all axes.
        """
        response = await self.client.get("/ew51/positions")
        response.raise_for_status()
        return PositionResponse(**response.json())

    async def home_axes(
        self,
        axes: List[AxisId],
        wait: bool = True,
    ) -> dict:
        """Home specified axes.

        Args:
            axes: List of axes to home.
            wait: If True, wait for homing to complete.

        Returns:
            Homing results dictionary.
        """
        request = HomeRequest(axes=axes, wait=wait)
        response = await self.client.post(
            "/ew51/home",
            json=request.model_dump(),
        )
        response.raise_for_status()
        return response.json()

    async def emergency_stop(self) -> dict:
        """Trigger emergency stop on all axes.

        Returns:
            Emergency stop response.
        """
        response = await self.client.post("/ew51/emergency-stop")
        response.raise_for_status()
        return response.json()

    # Alignment methods

    async def configure_flat_alignment(
        self,
        params: FlatAlignmentParameters,
        wavelength: Optional[int] = None,
    ) -> dict:
        """Configure flat alignment parameters.

        Args:
            params: Flat alignment parameters.
            wavelength: Optional measurement wavelength in nm (e.g., 1310, 1550).

        Returns:
            Configuration confirmation.
        """
        url = "/ew51/alignment/flat/configure"
        if wavelength:
            url = f"{url}?wavelength={wavelength}"

        response = await self.client.post(url, json=params.model_dump())
        response.raise_for_status()
        return response.json()

    async def configure_focus_alignment(
        self,
        params: FocusAlignmentParameters,
        wavelength: Optional[int] = None,
    ) -> dict:
        """Configure focus alignment parameters.

        Args:
            params: Focus alignment parameters.
            wavelength: Optional measurement wavelength in nm (e.g., 1310, 1550).

        Returns:
            Configuration confirmation.
        """
        url = "/ew51/alignment/focus/configure"
        if wavelength:
            url = f"{url}?wavelength={wavelength}"

        response = await self.client.post(url, json=params.model_dump())
        response.raise_for_status()
        return response.json()

    async def start_flat_alignment(self) -> dict:
        """Start flat alignment execution.

        Returns:
            Start confirmation.
        """
        response = await self.client.post("/ew51/alignment/flat/start")
        response.raise_for_status()
        return response.json()

    async def start_focus_alignment(self) -> dict:
        """Start focus alignment execution.

        Returns:
            Start confirmation.
        """
        response = await self.client.post("/ew51/alignment/focus/start")
        response.raise_for_status()
        return response.json()

    async def stop_alignment(self) -> dict:
        """Stop alignment execution.

        Returns:
            Stop confirmation.
        """
        response = await self.client.post("/ew51/alignment/stop")
        response.raise_for_status()
        return response.json()

    async def get_alignment_status(
        self, pm_channel: Optional[int] = None
    ) -> AlignmentStatusResponse:
        """Get current alignment status.

        Args:
            pm_channel: Optional power meter channel (1-4) to read optical power.

        Returns:
            Current alignment status.
        """
        url = "/ew51/alignment/status"
        if pm_channel:
            url = f"{url}?pm_channel={pm_channel}"

        response = await self.client.get(url)
        response.raise_for_status()
        return AlignmentStatusResponse(**response.json())

    async def wait_for_alignment_completion(
        self, timeout: float = 300.0
    ) -> AlignmentResultResponse:
        """Wait for alignment to complete.

        Args:
            timeout: Maximum time to wait in seconds (default: 300).

        Returns:
            Alignment result after completion.
        """
        response = await self.client.post(
            f"/ew51/alignment/wait?timeout={timeout}"
        )
        response.raise_for_status()
        return AlignmentResultResponse(**response.json())

    async def get_profile_packet_count(
        self, profile_type: ProfileDataType
    ) -> int:
        """Get number of profile data packets available.

        Args:
            profile_type: Type of profile data.

        Returns:
            Number of packets available.
        """
        response = await self.client.get(
            f"/ew51/alignment/profile/{profile_type.value}/count"
        )
        response.raise_for_status()
        return response.json()["packet_count"]

    async def get_profile_data(
        self, profile_type: ProfileDataType, packet_number: int
    ) -> ProfileData:
        """Get specific profile data packet.

        Args:
            profile_type: Type of profile data.
            packet_number: Packet number to retrieve (1-indexed).

        Returns:
            Profile data packet.
        """
        response = await self.client.get(
            f"/ew51/alignment/profile/{profile_type.value}/{packet_number}"
        )
        response.raise_for_status()
        return ProfileData(**response.json())
