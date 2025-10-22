"""Enumerations for the Suruga Seiki EW-51 motion control system."""

from enum import IntEnum, Enum


class AxisId(IntEnum):
    """Axis identifiers for the 12-axis motion controller.

    Left stage (1-6):
        - X1, Y1, Z1: Linear axes
        - TX1, TY1, TZ1: Rotational axes

    Right stage (7-12):
        - X2, Y2, Z2: Linear axes
        - TX2, TY2, TZ2: Rotational axes
    """

    # Left stage
    X1 = 1
    Y1 = 2
    Z1 = 3
    TX1 = 4
    TY1 = 5
    TZ1 = 6

    # Right stage
    X2 = 7
    Y2 = 8
    Z2 = 9
    TX2 = 10
    TY2 = 11
    TZ2 = 12


class StageId(IntEnum):
    """Stage identifiers."""

    LEFT = 1
    RIGHT = 2


class ServoState(str, Enum):
    """Servo state for axis control."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class MovementStatus(str, Enum):
    """Status of movement operations."""

    IDLE = "idle"
    MOVING = "moving"
    COMPLETED = "completed"
    ERROR = "error"


class AlignmentMode(str, Enum):
    """Alignment mode for optical positioning."""

    FLAT = "flat"
    FOCUS = "focus"
    DISABLED = "disabled"


class DaemonState(str, Enum):
    """Daemon lifecycle states."""

    STARTING = "starting"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
