"""Suruga Seiki EW-51 Motion Control API.

A modular Python API and daemon service for controlling the Suruga Seiki EW-51
motion control system, used for precision positioning in photonics and chip
characterization setups.

This package follows the architectural patterns of the reachy_mini repository,
providing a clean separation between daemon (server) and SDK (client) layers
with full hardware abstraction.
"""

__version__ = "0.1.0"
__author__ = "Lucas"
__all__ = [
    "__version__",
    "__author__",
]
