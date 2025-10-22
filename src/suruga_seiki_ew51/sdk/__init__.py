"""SDK client library for controlling the EW-51 motion system.

Provides high-level Python client API for scripts and applications to
communicate with the daemon via HTTP or WebSocket.
"""

from .client import EW51Client

__all__ = ["EW51Client"]
