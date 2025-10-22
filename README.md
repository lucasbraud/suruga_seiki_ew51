# Suruga Seiki EW-51 Motion Control API

A modular Python API and daemon service for controlling the **Suruga Seiki EW-51 motion control system**, used for precision positioning in photonics and chip characterization setups.

This project provides clean modularity, clear hardware abstraction, and a split between **daemon (server)** and **SDK (client)** layers for flexible integration. All necessary DLL files for hardware control are included in the package.

## Features

- **Modular Architecture**: Clean separation between daemon, SDK, backend, and hardware layers
- **Hardware Abstraction**: Switch seamlessly between real hardware and mock simulation
- **REST API**: FastAPI-based REST endpoints for all motion control operations
- **Python SDK**: High-level async/sync client library for easy integration
- **12-Axis Control**: Support for dual 6-axis stages (X, Y, Z, TX, TY, TZ per stage)
- **Mock Backend**: Full simulation mode for development and testing without hardware
- **Type Safety**: Full type hints and Pydantic models throughout
- **Bundled DLLs**: All required hardware control DLLs are included in the package

## Architecture

```
src/suruga_seiki_ew51/
├── daemon/              # Background API service (FastAPI)
│   ├── app/            # FastAPI application & routers
│   ├── backend/        # Hardware abstraction layer
│   └── daemon.py       # Daemon main class
├── sdk/                 # High-level Python client (for scripts)
├── io/                  # Communication & I/O handling (.NET DLL, serial, etc.)
├── motion/              # Axis, trajectory, and servo control
├── alignment/           # Optical and angular alignment modules
├── config/              # System configuration (stages, calibration, etc.)
├── models/              # Pydantic models for API schemas
└── utils/               # Common utilities
```

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md) - Get up and running quickly
- [Development Documentation](docs/development/) - Detailed development resources:
  - [Project Status](docs/development/PROJECT_STATUS.md)
  - [Analysis Index](docs/development/ANALYSIS_INDEX.md)
  - [Exploration Report](docs/development/EXPLORATION_REPORT.md)
  - [Development Notes](docs/development/CLAUDE.md)

## Installation

### Development Setup

```bash
# Create conda environment (Python 3.11+ recommended)
conda create -n suruga python=3.11
conda activate suruga

# Install in development mode (includes hardware support by default)
pip install -e "."  # Use quotes to prevent zsh glob expansion

# For development tools (optional)
pip install -e ".[dev]"  # Adds testing and code quality tools

# Install pre-commit hooks (recommended for development)
pre-commit install
```

Note: Hardware support (including .NET runtime integration and DLL files) is included by default.

## Quick Start

### Running the Daemon

Start the daemon in mock mode (no hardware required):

```bash
suruga-ew51-daemon --mock
```

Or start with real hardware:

```bash
suruga-ew51-daemon
```

Options:
- `--mock`: Use mock backend (default: False)
- `--host`: Host to bind to (default: 127.0.0.1)
- `--port`: Port to bind to (default: 8000)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--reload`: Enable auto-reload for development

### Using the SDK

```python
from suruga_seiki_ew51.sdk import EW51Client
from suruga_seiki_ew51.models import AxisId

# Connect to daemon
client = EW51Client(base_url="http://localhost:8000")

# Enable servo for an axis
await client.enable_servo([AxisId.X1])

# Move axis
await client.move_axis(AxisId.X1, target=1000.0, wait=True)

# Get current position
position = await client.get_position(AxisId.X1)
print(f"Current position: {position} µm")

# Disable servo
await client.disable_servo([AxisId.X1])
```

### Using the REST API

The daemon exposes REST endpoints at `http://localhost:8000`:

- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /health` - Health check
- `GET /ew51/status` - Get complete station status
- `POST /ew51/servo/enable` - Enable servo on axes
- `POST /ew51/move` - Move single axis
- `POST /ew51/move/multi` - Move multiple axes simultaneously
- `GET /ew51/positions` - Get all axis positions

See `/docs` for complete API documentation.

## Development

### Running Tests

```bash
# Run all non-hardware tests
pytest -vv -m "not hardware"

# Run with mock backend
pytest -vv --mock

# Run with coverage
pytest -vv --cov=suruga_seiki_ew51 --cov-report=html
```

### Code Quality

```bash
# Run pre-commit checks
pre-commit run --all-files

# Type checking
mypy -v

# Linting
ruff check --select I --select D
```

## Hardware Integration

The real backend integrates with the Suruga Seiki motion controller using the included DLL files and `pythonnet`.

**Requirements:**
- Install pythonnet: Included with `.[hardware]` extras
- Ensure .NET runtime is available on the system
- All required DLLs are included in the package

**Axis Numbering:**
- Left stage: 1-6 → X1, Y1, Z1, TX1, TY1, TZ1
- Right stage: 7-12 → X2, Y2, Z2, TX2, TY2, TZ2

**Servo Control:**
- Servo must be enabled before movement
- Disable servo when idle to save power

## License

MIT License

## Contributing

This project follows Google-style docstrings (D212 compliant) and uses Ruff and mypy for code quality.
