"""Common dependencies for FastAPI routes."""

from typing import Optional
from fastapi import HTTPException

from suruga_seiki_ew51.daemon.daemon import EW51Daemon

# Global daemon instance
daemon: Optional[EW51Daemon] = None


def get_daemon() -> EW51Daemon:
    """Dependency to get the daemon instance.

    Returns:
        The global daemon instance.

    Raises:
        HTTPException: If daemon is not initialized.
    """
    if daemon is None:
        raise HTTPException(status_code=500, detail="Daemon not initialized")
    return daemon