"""Custom exceptions for the Suruga Seiki EW-51 control system."""


class StationException(Exception):
    """Base exception for all station-related errors."""

    pass


class HardwareError(StationException):
    """Hardware communication or operation error."""

    pass


class ConnectionError(StationException):
    """Connection to the motion controller failed."""

    pass


class MovementError(StationException):
    """Error during axis movement operation."""

    pass


class ServoError(StationException):
    """Error during servo control operation."""

    pass


class ConfigurationError(StationException):
    """Configuration or calibration error."""

    pass


class AlignmentError(StationException):
    """Error during alignment operation."""

    pass


class TimeoutError(StationException):
    """Operation timed out."""

    pass


class AxisLimitError(StationException):
    """Axis position exceeds software or hardware limits."""

    pass


class BackendError(StationException):
    """Backend-specific error."""

    pass
