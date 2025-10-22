"""Pydantic models for alignment parameters and responses."""

from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field


class ZMode(str, Enum):
    """Z-axis mode for focus alignment."""

    ROUND = "Round"
    LINEAR = "Linear"


class AlignmentStatus(str, Enum):
    """Alignment operation status."""

    IDLE = "Idle"
    ALIGNING = "Aligning"
    SUCCESS = "Success"
    FAILURE = "Failure"
    STOPPED = "Stopped"
    ERROR = "Error"


class AligningStatus(str, Enum):
    """Detailed status during alignment execution."""

    FIELD_SEARCHING = "FieldSearching"
    PEAK_SEARCHING_X = "PeakSearchingX"
    PEAK_SEARCHING_Y = "PeakSearchingY"
    CONVERGING = "Converging"


class ProfileDataType(str, Enum):
    """Type of profile data for alignment."""

    FIELD_SEARCH = "FieldSearch"
    PEAK_SEARCH_X = "PeakSearchX"
    PEAK_SEARCH_Y = "PeakSearchY"


class FlatAlignmentParameters(BaseModel):
    """Parameters for flat alignment mode."""

    main_stage_number_x: int = Field(
        7, description="Main stage X axis number (typically 7)"
    )
    main_stage_number_y: int = Field(
        8, description="Main stage Y axis number (typically 8)"
    )
    sub_stage_number_xy: int = Field(
        0, description="Sub stage XY axis number (0 if not used)"
    )
    sub_angle_x: float = Field(
        0.0, description="Sub stage angle X in degrees"
    )
    sub_angle_y: float = Field(
        -8.0, description="Sub stage angle Y in degrees"
    )

    pm_ch: int = Field(1, description="Power meter channel (1-4)")
    analog_ch: int = Field(1, description="Analog channel (1-4)")
    pm_auto_range_up_on: bool = Field(
        True, description="Enable auto-range up for power meter"
    )
    pm_init_range_setting_on: bool = Field(
        True, description="Enable initial range setting"
    )
    pm_init_range: float = Field(
        -10.0, description="Initial power meter range in dBm"
    )

    field_search_threshold: float = Field(
        0.1, description="Field search threshold in dBm"
    )
    peak_search_threshold: float = Field(
        40.0, description="Peak search threshold percentage"
    )

    search_range_x: float = Field(
        500.0, description="Search range X in micrometers"
    )
    search_range_y: float = Field(
        500.0, description="Search range Y in micrometers"
    )

    field_search_pitch_x: float = Field(
        5.0, description="Field search pitch X in micrometers"
    )
    field_search_pitch_y: float = Field(
        5.0, description="Field search pitch Y in micrometers"
    )
    field_search_first_pitch_x: float = Field(
        0.0, description="First pitch X for field search"
    )

    field_search_speed_x: float = Field(
        1000.0, description="Field search speed X in um/s"
    )
    field_search_speed_y: float = Field(
        1000.0, description="Field search speed Y in um/s"
    )

    peak_search_speed_x: float = Field(
        5.0, description="Peak search speed X in um/s"
    )
    peak_search_speed_y: float = Field(
        5.0, description="Peak search speed Y in um/s"
    )

    smoothing_range_x: float = Field(
        50.0, description="Smoothing range X in micrometers"
    )
    smoothing_range_y: float = Field(
        50.0, description="Smoothing range Y in micrometers"
    )

    centroid_threshold_x: float = Field(
        0.0, description="Centroid threshold X"
    )
    centroid_threshold_y: float = Field(
        0.0, description="Centroid threshold Y"
    )

    convergent_range_x: float = Field(
        1.0, description="Convergence range X in micrometers"
    )
    convergent_range_y: float = Field(
        1.0, description="Convergence range Y in micrometers"
    )

    comparison_count: int = Field(
        2, description="Number of comparisons for convergence"
    )
    max_repeat_count: int = Field(
        10, description="Maximum repeat count for alignment"
    )


class FocusAlignmentParameters(BaseModel):
    """Parameters for focus alignment mode."""

    z_mode: ZMode = Field(
        ZMode.ROUND, description="Z-axis mode (Round or Linear)"
    )

    main_stage_number_x: int = Field(
        7, description="Main stage X axis number (typically 7)"
    )
    main_stage_number_y: int = Field(
        8, description="Main stage Y axis number (typically 8)"
    )
    sub_stage_number_xy: int = Field(
        0, description="Sub stage XY axis number (0 if not used)"
    )
    sub_angle_x: float = Field(
        0.0, description="Sub stage angle X in degrees"
    )
    sub_angle_y: float = Field(
        -8.0, description="Sub stage angle Y in degrees"
    )

    pm_ch: int = Field(1, description="Power meter channel (1-4)")
    analog_ch: int = Field(1, description="Analog channel (1-4)")
    pm_auto_range_up_on: bool = Field(
        True, description="Enable auto-range up for power meter"
    )
    pm_init_range_setting_on: bool = Field(
        True, description="Enable initial range setting"
    )
    pm_init_range: float = Field(
        -10.0, description="Initial power meter range in dBm"
    )

    field_search_threshold: float = Field(
        0.1, description="Field search threshold in dBm"
    )
    peak_search_threshold: float = Field(
        40.0, description="Peak search threshold percentage"
    )

    search_range_x: float = Field(
        500.0, description="Search range X in micrometers"
    )
    search_range_y: float = Field(
        500.0, description="Search range Y in micrometers"
    )

    field_search_pitch_x: float = Field(
        5.0, description="Field search pitch X in micrometers"
    )
    field_search_pitch_y: float = Field(
        5.0, description="Field search pitch Y in micrometers"
    )
    field_search_first_pitch_x: float = Field(
        0.0, description="First pitch X for field search"
    )

    field_search_speed_x: float = Field(
        1000.0, description="Field search speed X in um/s"
    )
    field_search_speed_y: float = Field(
        1000.0, description="Field search speed Y in um/s"
    )

    peak_search_speed_x: float = Field(
        5.0, description="Peak search speed X in um/s"
    )
    peak_search_speed_y: float = Field(
        5.0, description="Peak search speed Y in um/s"
    )

    smoothing_range_x: float = Field(
        50.0, description="Smoothing range X in micrometers"
    )
    smoothing_range_y: float = Field(
        50.0, description="Smoothing range Y in micrometers"
    )

    centroid_threshold_x: float = Field(
        0.0, description="Centroid threshold X"
    )
    centroid_threshold_y: float = Field(
        0.0, description="Centroid threshold Y"
    )

    convergent_range_x: float = Field(
        1.0, description="Convergence range X in micrometers"
    )
    convergent_range_y: float = Field(
        1.0, description="Convergence range Y in micrometers"
    )

    comparison_count: int = Field(
        2, description="Number of comparisons for convergence"
    )
    max_repeat_count: int = Field(
        10, description="Maximum repeat count for alignment"
    )


class ProfileData(BaseModel):
    """Profile data packet from alignment scan."""

    packet_index: int = Field(..., description="Packet index number")
    data_count: int = Field(..., description="Number of data points")
    main_position_list: List[float] = Field(
        ..., description="List of main axis positions"
    )
    signal_ch1_list: List[float] = Field(
        ..., description="List of signal values for channel 1"
    )


class AlignmentStatusResponse(BaseModel):
    """Response for alignment status query."""

    status: AlignmentStatus = Field(..., description="Current alignment status")
    aligning_status: Optional[AligningStatus] = Field(
        None, description="Detailed status during alignment"
    )
    error_axis_id: int = Field(0, description="Axis ID where error occurred (0 = none)")
    optical_power: Optional[float] = Field(
        None, description="Current optical power in dBm"
    )


class AlignmentResultResponse(BaseModel):
    """Response after alignment completion."""

    success: bool = Field(..., description="Whether alignment succeeded")
    status: AlignmentStatus = Field(..., description="Final alignment status")
    final_position_x: float = Field(..., description="Final X position in micrometers")
    final_position_y: float = Field(..., description="Final Y position in micrometers")
    optical_power: Optional[float] = Field(
        None, description="Final optical power in dBm"
    )
    message: str = Field(..., description="Result message")
