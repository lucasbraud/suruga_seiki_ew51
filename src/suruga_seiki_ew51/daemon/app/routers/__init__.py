"""FastAPI routers for the EW-51 daemon."""

from .daemon import router as daemon_router
from .servo import router as servo_router
from .movement import router as movement_router
from .status import router as status_router
from .alignment import router as alignment_router

__all__ = [
    "daemon_router",
    "servo_router",
    "movement_router",
    "status_router",
    "alignment_router",
]
