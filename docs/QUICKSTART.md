# Quick Start Guide

## Installation

### 1. Create Environment

```bash
# Using conda (recommended)
conda create -n suruga python=3.11
conda activate suruga

# Or using venv
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Package

```bash
# Development installation
pip install -e ".[dev]"  # Use quotes to prevent zsh glob expansion

# For hardware support (requires .NET runtime)
pip install -e ".[hardware]"  # Use quotes to prevent zsh glob expansion
```

### 3. Install Pre-commit Hooks (Optional)

```bash
pre-commit install
```

## Running the Daemon

### Mock Mode (No Hardware)

```bash
# Start daemon with mock backend
suruga-ew51-daemon --mock

# With auto-reload for development
suruga-ew51-daemon --mock --reload --log-level DEBUG
```

The daemon will start at `http://localhost:8000`

### Real Hardware Mode

```bash
# Start with hardware backend
suruga-ew51-daemon

# Custom host and port
suruga-ew51-daemon --host 0.0.0.0 --port 9000
```

The DLL files are included in the package at `suruga_seiki_ew51/io/dll/`, so you don't need to specify their location.

## Using the API

### Interactive Documentation

Once the daemon is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example REST Calls

```bash
# Health check
curl http://localhost:8000/ew51/health

# Get full status
curl http://localhost:8000/ew51/status

# Enable servo for X1
curl -X POST http://localhost:8000/ew51/servo/enable \
  -H "Content-Type: application/json" \
  -d '{"axes": [1], "enabled": true}'

# Move X1 to 1000 μm
curl -X POST http://localhost:8000/ew51/move \
  -H "Content-Type: application/json" \
  -d '{"axis": 1, "target": 1000.0, "relative": false, "wait": true}'

# Get current position
curl http://localhost:8000/ew51/position/1
```

## Using the SDK

### Basic Example

```python
import asyncio
from suruga_seiki_ew51.sdk import EW51Client
from suruga_seiki_ew51.models import AxisId

async def main():
    async with EW51Client("http://localhost:8000") as client:
        # Check health
        health = await client.health()
        print(f"Status: {health.status}, Mock: {health.is_mock}")

        # Enable servo
        await client.enable_servo([AxisId.X1])

        # Move axis
        response = await client.move_axis(
            AxisId.X1,
            target=1000.0,
            wait=True
        )
        print(f"Final position: {response.current_position} μm")

        # Get position
        position = await client.get_position(AxisId.X1)
        print(f"Current position: {position} μm")

        # Disable servo
        await client.disable_servo([AxisId.X1])

if __name__ == "__main__":
    asyncio.run(main())
```

### Run the Example

```bash
# Make sure daemon is running first
suruga-ew51-daemon --mock

# In another terminal
python examples/example_client.py
```

## Testing

### Run All Tests

```bash
# Run all non-hardware tests
pytest -vv -m "not hardware"

# Run specific test file
pytest -vv tests/unit/test_mock_backend.py

# Run with coverage
pytest -vv --cov=suruga_seiki_ew51 --cov-report=html
```

### Run Code Quality Checks

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Individual checks
ruff check .           # Linting
ruff format .          # Formatting
mypy src/              # Type checking
```

## Development

### Project Structure

```
src/suruga_seiki_ew51/
├── daemon/          # FastAPI daemon service
│   ├── app/        # FastAPI app and routers
│   ├── backend/    # Hardware abstraction (mock/real)
│   └── cli.py      # CLI entry point
├── sdk/            # Client SDK
├── models/         # Pydantic models
├── utils/          # Utilities and exceptions
├── io/             # I/O handling (DLL, serial)
├── motion/         # Motion control primitives
├── alignment/      # Alignment modules
└── config/         # Configuration management
```

## Troubleshooting

### Daemon won't start

```bash
# Check if port is already in use
lsof -i :8000

# Try different port
suruga-ew51-daemon --mock --port 8001
```

### Import errors

```bash
# Make sure package is installed
pip install -e .

# Verify installation
python -c "from suruga_seiki_ew51 import __version__; print(__version__)"
```

### Tests failing

```bash
# Install dev dependencies
pip install -e ".[dev]"  # Use quotes to prevent zsh glob expansion

# Run with verbose output
pytest -vv -s
```

## Additional Resources

- **Full Documentation**: See `README.md`
- **Project Status**: See `PROJECT_STATUS.md`
- **Architecture Guide**: See `CLAUDE.md`
- **API Docs**: http://localhost:8000/docs (when daemon is running)

## Support

For issues or questions:
1. Check the documentation
2. Review the example scripts in `examples/`
3. Check the exploration reports for implementation details
