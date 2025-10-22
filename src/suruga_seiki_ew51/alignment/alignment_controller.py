"""Alignment controller for optical alignment operations.

This module provides a high-level Python interface to the DLL alignment system.
"""

import asyncio
import logging
from typing import Optional, List

from suruga_seiki_ew51.models.alignment import (
    FlatAlignmentParameters,
    FocusAlignmentParameters,
    AlignmentStatus,
    AligningStatus,
    ProfileDataType,
    ProfileData,
    AlignmentStatusResponse,
    AlignmentResultResponse,
)
from suruga_seiki_ew51.utils import AlignmentError

logger = logging.getLogger(__name__)


class AlignmentController:
    """Controller for optical alignment operations.

    This class wraps the DLL Alignment object and provides async Python methods
    for alignment configuration and execution.
    """

    def __init__(self, dll_alignment: any):
        """Initialize alignment controller.

        Args:
            dll_alignment: DLL Alignment instance from backend.
        """
        self._alignment = dll_alignment
        self._dll_module = None  # Will be set by backend

    def set_dll_module(self, dll_module: any) -> None:
        """Set the DLL module reference for creating parameter objects.

        Args:
            dll_module: SurugaSeiki.Motion module.
        """
        self._dll_module = dll_module

    def _to_dll_flat_params(
        self, params: FlatAlignmentParameters
    ) -> any:
        """Convert Python flat alignment parameters to DLL object.

        Args:
            params: Python FlatAlignmentParameters model.

        Returns:
            DLL FlatParameter object.
        """
        if not self._dll_module:
            raise AlignmentError("DLL module not set")

        dll_params = self._dll_module.Alignment.FlatParameter()

        dll_params.mainStageNumberX = params.main_stage_number_x
        dll_params.mainStageNumberY = params.main_stage_number_y
        dll_params.subStageNumberXY = params.sub_stage_number_xy
        dll_params.subAngleX = params.sub_angle_x
        dll_params.subAngleY = params.sub_angle_y

        dll_params.pmCh = params.pm_ch
        dll_params.analogCh = params.analog_ch
        dll_params.pmAutoRangeUpOn = params.pm_auto_range_up_on
        dll_params.pmInitRangeSettingOn = params.pm_init_range_setting_on
        dll_params.pmInitRange = params.pm_init_range

        dll_params.fieldSearchThreshold = params.field_search_threshold
        dll_params.peakSearchThreshold = params.peak_search_threshold

        dll_params.searchRangeX = params.search_range_x
        dll_params.searchRangeY = params.search_range_y

        dll_params.fieldSearchPitchX = params.field_search_pitch_x
        dll_params.fieldSearchPitchY = params.field_search_pitch_y
        dll_params.fieldSearchFirstPitchX = params.field_search_first_pitch_x

        dll_params.fieldSearchSpeedX = params.field_search_speed_x
        dll_params.fieldSearchSpeedY = params.field_search_speed_y

        dll_params.peakSearchSpeedX = params.peak_search_speed_x
        dll_params.peakSearchSpeedY = params.peak_search_speed_y

        dll_params.smoothingRangeX = params.smoothing_range_x
        dll_params.smoothingRangeY = params.smoothing_range_y

        dll_params.centroidThresholdX = params.centroid_threshold_x
        dll_params.centroidThresholdY = params.centroid_threshold_y

        dll_params.convergentRangeX = params.convergent_range_x
        dll_params.convergentRangeY = params.convergent_range_y

        dll_params.comparisonCount = params.comparison_count
        dll_params.maxRepeatCount = params.max_repeat_count

        return dll_params

    def _to_dll_focus_params(
        self, params: FocusAlignmentParameters
    ) -> any:
        """Convert Python focus alignment parameters to DLL object.

        Args:
            params: Python FocusAlignmentParameters model.

        Returns:
            DLL FocusParameter object.
        """
        if not self._dll_module:
            raise AlignmentError("DLL module not set")

        dll_params = self._dll_module.Alignment.FocusParameter()

        # Set Z mode
        dll_params.zMode = (
            self._dll_module.Alignment.ZMode.Round
            if params.z_mode.value == "Round"
            else self._dll_module.Alignment.ZMode.Linear
        )

        dll_params.mainStageNumberX = params.main_stage_number_x
        dll_params.mainStageNumberY = params.main_stage_number_y
        dll_params.subStageNumberXY = params.sub_stage_number_xy
        dll_params.subAngleX = params.sub_angle_x
        dll_params.subAngleY = params.sub_angle_y

        dll_params.pmCh = params.pm_ch
        dll_params.analogCh = params.analog_ch
        dll_params.pmAutoRangeUpOn = params.pm_auto_range_up_on
        dll_params.pmInitRangeSettingOn = params.pm_init_range_setting_on
        dll_params.pmInitRange = params.pm_init_range

        dll_params.fieldSearchThreshold = params.field_search_threshold
        dll_params.peakSearchThreshold = params.peak_search_threshold

        dll_params.searchRangeX = params.search_range_x
        dll_params.searchRangeY = params.search_range_y

        dll_params.fieldSearchPitchX = params.field_search_pitch_x
        dll_params.fieldSearchPitchY = params.field_search_pitch_y
        dll_params.fieldSearchFirstPitchX = params.field_search_first_pitch_x

        dll_params.fieldSearchSpeedX = params.field_search_speed_x
        dll_params.fieldSearchSpeedY = params.field_search_speed_y

        dll_params.peakSearchSpeedX = params.peak_search_speed_x
        dll_params.peakSearchSpeedY = params.peak_search_speed_y

        dll_params.smoothingRangeX = params.smoothing_range_x
        dll_params.smoothingRangeY = params.smoothing_range_y

        dll_params.centroidThresholdX = params.centroid_threshold_x
        dll_params.centroidThresholdY = params.centroid_threshold_y

        dll_params.convergentRangeX = params.convergent_range_x
        dll_params.convergentRangeY = params.convergent_range_y

        dll_params.comparisonCount = params.comparison_count
        dll_params.maxRepeatCount = params.max_repeat_count

        return dll_params

    async def configure_flat_alignment(
        self, params: FlatAlignmentParameters, wavelength: Optional[int] = None
    ) -> None:
        """Configure flat alignment parameters.

        Args:
            params: Flat alignment parameters.
            wavelength: Measurement wavelength in nm (e.g., 1310, 1550).

        Raises:
            AlignmentError: If configuration fails.
        """
        try:
            dll_params = self._to_dll_flat_params(params)
            self._alignment.SetFlat(dll_params)

            if wavelength:
                self._alignment.SetMeasurementWaveLength(params.pm_ch, wavelength)

            logger.info(f"Configured flat alignment with wavelength {wavelength}nm")

        except Exception as e:
            logger.error(f"Failed to configure flat alignment: {e}")
            raise AlignmentError(f"Failed to configure flat alignment: {e}")

    async def configure_focus_alignment(
        self, params: FocusAlignmentParameters, wavelength: Optional[int] = None
    ) -> None:
        """Configure focus alignment parameters.

        Args:
            params: Focus alignment parameters.
            wavelength: Measurement wavelength in nm (e.g., 1310, 1550).

        Raises:
            AlignmentError: If configuration fails.
        """
        try:
            dll_params = self._to_dll_focus_params(params)
            self._alignment.SetFocus(dll_params)

            if wavelength:
                self._alignment.SetMeasurementWaveLength(params.pm_ch, wavelength)

            logger.info(f"Configured focus alignment with wavelength {wavelength}nm")

        except Exception as e:
            logger.error(f"Failed to configure focus alignment: {e}")
            raise AlignmentError(f"Failed to configure focus alignment: {e}")

    async def start_flat_alignment(self) -> None:
        """Start flat alignment execution.

        Raises:
            AlignmentError: If start fails.
        """
        try:
            self._alignment.StartFlat()
            await asyncio.sleep(0.1)  # Give alignment time to start
            logger.info("Started flat alignment")

        except Exception as e:
            logger.error(f"Failed to start flat alignment: {e}")
            raise AlignmentError(f"Failed to start flat alignment: {e}")

    async def start_focus_alignment(self) -> None:
        """Start focus alignment execution.

        Raises:
            AlignmentError: If start fails.
        """
        try:
            self._alignment.StartFocus()
            await asyncio.sleep(0.1)  # Give alignment time to start
            logger.info("Started focus alignment")

        except Exception as e:
            logger.error(f"Failed to start focus alignment: {e}")
            raise AlignmentError(f"Failed to start focus alignment: {e}")

    async def stop_alignment(self) -> None:
        """Stop alignment execution.

        Raises:
            AlignmentError: If stop fails.
        """
        try:
            self._alignment.Stop()
            logger.info("Stopped alignment")

        except Exception as e:
            logger.error(f"Failed to stop alignment: {e}")
            raise AlignmentError(f"Failed to stop alignment: {e}")

    def get_status(self) -> AlignmentStatus:
        """Get current alignment status.

        Returns:
            Current alignment status.
        """
        status_str = str(self._alignment.GetStatus())
        try:
            return AlignmentStatus(status_str)
        except ValueError:
            logger.warning(f"Unknown alignment status: {status_str}")
            return AlignmentStatus.ERROR

    def get_aligning_status(self) -> Optional[AligningStatus]:
        """Get detailed status during alignment.

        Returns:
            Detailed aligning status or None if not aligning.
        """
        if self.get_status() != AlignmentStatus.ALIGNING:
            return None

        status_str = str(self._alignment.GetAligningStatus())
        try:
            return AligningStatus(status_str)
        except ValueError:
            logger.warning(f"Unknown aligning status: {status_str}")
            return None

    def get_error_axis_id(self) -> int:
        """Get axis ID where error occurred.

        Returns:
            Axis ID (0 if no error).
        """
        return int(self._alignment.GetErrorAxisID())

    def get_optical_power(self, pm_channel: int) -> float:
        """Get current optical power reading.

        Args:
            pm_channel: Power meter channel (1-4).

        Returns:
            Optical power in dBm.
        """
        return float(self._alignment.GetPower(pm_channel))

    async def get_status_info(self, pm_channel: Optional[int] = None) -> AlignmentStatusResponse:
        """Get complete alignment status information.

        Args:
            pm_channel: Power meter channel to read (None = don't read power).

        Returns:
            Complete alignment status response.
        """
        status = self.get_status()
        aligning_status = self.get_aligning_status()
        error_axis = self.get_error_axis_id()

        optical_power = None
        if pm_channel is not None:
            try:
                optical_power = self.get_optical_power(pm_channel)
            except Exception as e:
                logger.warning(f"Failed to get optical power: {e}")

        return AlignmentStatusResponse(
            status=status,
            aligning_status=aligning_status,
            error_axis_id=error_axis,
            optical_power=optical_power,
        )

    def get_profile_packet_count(self, profile_type: ProfileDataType) -> int:
        """Get number of profile data packets available.

        Args:
            profile_type: Type of profile data.

        Returns:
            Number of packets.
        """
        # Map Python enum to DLL enum
        if not self._dll_module:
            raise AlignmentError("DLL module not set")

        dll_type_map = {
            ProfileDataType.FIELD_SEARCH: self._dll_module.Alignment.ProfileDataType.FieldSearch,
            ProfileDataType.PEAK_SEARCH_X: self._dll_module.Alignment.ProfileDataType.PeakSearchX,
            ProfileDataType.PEAK_SEARCH_Y: self._dll_module.Alignment.ProfileDataType.PeakSearchY,
        }

        dll_type = dll_type_map[profile_type]
        return int(self._alignment.GetProfilePacketSumIndex(dll_type))

    def get_profile_data(
        self, profile_type: ProfileDataType, packet_number: int
    ) -> ProfileData:
        """Get profile data packet.

        Args:
            profile_type: Type of profile data.
            packet_number: Packet number (1-indexed).

        Returns:
            Profile data packet.
        """
        if not self._dll_module:
            raise AlignmentError("DLL module not set")

        dll_type_map = {
            ProfileDataType.FIELD_SEARCH: self._dll_module.Alignment.ProfileDataType.FieldSearch,
            ProfileDataType.PEAK_SEARCH_X: self._dll_module.Alignment.ProfileDataType.PeakSearchX,
            ProfileDataType.PEAK_SEARCH_Y: self._dll_module.Alignment.ProfileDataType.PeakSearchY,
        }

        dll_type = dll_type_map[profile_type]
        profile = self._alignment.RequestProfileData(dll_type, packet_number, False)

        return ProfileData(
            packet_index=int(profile.packetIndex),
            data_count=int(profile.dataCount),
            main_position_list=list(profile.mainPositionList),
            signal_ch1_list=list(profile.signalCh1List),
        )

    async def wait_for_completion(
        self, timeout: float = 300.0, poll_interval: float = 0.5
    ) -> AlignmentResultResponse:
        """Wait for alignment to complete.

        Args:
            timeout: Maximum time to wait in seconds.
            poll_interval: Polling interval in seconds.

        Returns:
            Alignment result response.

        Raises:
            AlignmentError: If alignment fails or times out.
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            status = self.get_status()

            if status == AlignmentStatus.SUCCESS:
                logger.info("Alignment completed successfully")
                return await self._build_result_response(success=True)

            if status in [AlignmentStatus.FAILURE, AlignmentStatus.ERROR]:
                logger.error(f"Alignment failed with status: {status}")
                return await self._build_result_response(success=False)

            if status == AlignmentStatus.STOPPED:
                logger.warning("Alignment was stopped")
                return await self._build_result_response(success=False, message="Stopped by user")

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise AlignmentError(f"Alignment did not complete within {timeout}s")

            await asyncio.sleep(poll_interval)

    async def _build_result_response(
        self, success: bool, message: Optional[str] = None
    ) -> AlignmentResultResponse:
        """Build alignment result response.

        Args:
            success: Whether alignment succeeded.
            message: Optional custom message.

        Returns:
            Alignment result response.
        """
        status = self.get_status()

        # Get final positions (axis 7 and 8) - will be provided by backend
        final_x = 0.0
        final_y = 0.0

        # Get optical power if available
        optical_power = None
        try:
            optical_power = self.get_optical_power(1)  # Default to channel 1
        except Exception:
            pass

        if message is None:
            message = "Success" if success else f"Failed with status {status.value}"

        return AlignmentResultResponse(
            success=success,
            status=status,
            final_position_x=final_x,
            final_position_y=final_y,
            optical_power=optical_power,
            message=message,
        )
