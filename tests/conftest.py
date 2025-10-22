"""Pytest configuration and fixtures."""

import pytest

from suruga_seiki_ew51.daemon.backend.mock import MockBackend
from suruga_seiki_ew51.models import AxisId


@pytest.fixture
async def mock_backend():
    """Provide a connected mock backend for testing.

    Yields:
        MockBackend: Connected mock backend instance.
    """
    backend = MockBackend()
    await backend.connect()
    yield backend
    await backend.disconnect()


@pytest.fixture
def axis():
    """Provide a default axis for testing.

    Returns:
        AxisId: Default axis (X1).
    """
    return AxisId.X1
