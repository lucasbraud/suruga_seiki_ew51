# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **production-ready** modular Python API and daemon service for controlling the Suruga Seiki EW-51 motion control system (12-axis precision positioning for photonics/chip characterization). The project features clean separation between daemon (FastAPI server), SDK (Python client), and backend layers (real hardware via DLL or mock simulation).

**Key characteristics:**
- Full hardware abstraction with switchable backends (real/mock)
- Complete optical alignment system (flat and focus modes)
- Type-safe throughout with Pydantic models
- Async/await design pattern
- All DLL files bundled in the package

## Common Commands

### Development Setup

```bash
# Install in development mode (includes hardware support by default)
pip install -e "."

# Install with dev tools (testing, linting)
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running the Daemon

```bash
conda activate suruga

# Start with mock backend (no hardware required)
suruga-ew51-daemon --mock

# Start with real hardware backend
suruga-ew51-daemon

# Development mode with auto-reload and debug logging
suruga-ew51-daemon --mock --reload --log-level DEBUG

# Custom host/port
suruga-ew51-daemon --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests excluding hardware tests
pytest -vv -m "not hardware"

# Run only mock backend tests
pytest -vv -m "mock"

# Run specific test file
pytest -vv tests/unit/test_mock_backend.py

# Run with coverage report
pytest -vv --cov=suruga_seiki_ew51 --cov-report=html
```

### Code Quality

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Linting only
ruff check .

# Format code
ruff format .

# Type checking
mypy src/
```

## Architecture

### Layer Separation

The codebase has a clear 3-layer architecture:

1. **Daemon Layer** (`daemon/`): FastAPI server providing REST API endpoints
2. **SDK Layer** (`sdk/`): High-level Python client for easy integration
3. **Backend Layer** (`daemon/backend/`): Hardware abstraction with mock/real implementations

This design allows:
- Daemon to run on hardware machine, SDK to connect remotely
- Development without hardware using mock backend
- Easy testing and CI/CD integration
- Clean separation of concerns

### Backend Abstraction

**Critical concept**: All backends implement `AbstractBackend` interface (`daemon/backend/abstract.py`). This defines 20+ abstract methods that both `MockBackend` and `RealBackend` must implement.

**Real Backend** (`daemon/backend/real/real_backend.py`):
- Uses `pythonnet` to load .NET DLL (`srgmc.dll`)
- Configures ADS address (default: `5.146.68.190.1.1`)
- Creates 12 `AxisComponent` instances (axes 1-12)
- Manages servo control, positioning, and alignment system
- Hardware communication is synchronous, wrapped in async methods

**Mock Backend** (`daemon/backend/mock/mock_backend.py`):
- Pure Python simulation for development/testing
- Realistic motion simulation with configurable speed
- Full feature parity with real backend API
- No external dependencies

### Axis and Stage Organization

**12 axes organized as 2 stages:**
- Stage 1 (LEFT): Axes 1-6 → X1, Y1, Z1, TX1, TY1, TZ1
- Stage 2 (RIGHT): Axes 7-12 → X2, Y2, Z2, TX2, TY2, TZ2

**AxisId enum** (`models/enums.py`): Provides type-safe axis references throughout codebase. Use `AxisId.X1` not integer `1`.

### Optical Alignment System

**Two alignment modes:**

1. **Flat Alignment** (2D XY fiber coupling):
   - Field Search: Coarse spiral/grid scan to locate optical signal
   - Peak Search X: Fine optimization along X-axis
   - Peak Search Y: Fine optimization along Y-axis
   - Iterative convergence

2. **Focus Alignment** (Z-axis optimization):
   - Same as flat alignment plus Z-axis optimization
   - Two Z modes: Round (circular search) or Linear (linear search)

**Configuration**: 30+ parameters per alignment mode via `FlatAlignmentParameters` and `FocusAlignmentParameters` models. Includes search ranges, speeds, thresholds, power meter config, stage angles.

**Profile Data**: Alignment system collects scan data (positions + signals) retrievable as `ProfileData` objects. Use `get_profile_packet_count()` and `get_profile_data()` to retrieve.

### Request Flow

Typical flow for hardware operation:

1. **Client** (user code) calls SDK method → `client.move_axis(AxisId.X1, 1000.0)`
2. **SDK** (`sdk/client.py`) sends HTTP request to daemon → `POST /ew51/move`
3. **Router** (`daemon/app/routers/movement.py`) validates request via Pydantic model
4. **Daemon** (`daemon/daemon.py`) delegates to backend → `backend.move_axis()`
5. **Backend** (mock or real) executes operation
6. Response flows back through the same layers

### FastAPI Router Organization

5 routers in `daemon/app/routers/`:

- **daemon.py**: Health checks, connection status, emergency stop
- **servo.py**: Servo enable/disable operations
- **movement.py**: Single/multi-axis movement, positioning, homing
- **status.py**: System status queries (axis, stage, full station)
- **alignment.py**: Optical alignment configuration, execution, monitoring, profile data

All routers are registered in `daemon/app/main.py` with `/ew51` prefix.

## Development Guidelines

### Type Safety

- Full type hints required (enforced by mypy strict mode)
- All API models use Pydantic for validation
- Use `AxisId` enum, never raw integers for axis references
- Backend methods return typed Pydantic models (`AxisStatus`, `StageStatus`, etc.)

### Async/Await Pattern

- All backend methods are async (even if hardware communication is synchronous)
- SDK client methods are async
- Use `async with EW51Client() as client:` pattern for automatic cleanup
- Use `asyncio.run()` when calling SDK from sync context

### Error Handling

Custom exceptions in `utils/exceptions.py`:
- `HardwareError`: Hardware communication failures
- `MovementError`: Movement operation failures
- `ServoError`: Servo control failures
- Always wrap backend exceptions appropriately

### Testing Strategy

- **Unit tests**: Use mock backend exclusively (`pytest -m "mock"`)
- **Hardware tests**: Mark with `@pytest.mark.hardware`, deselect by default
- Mock backend provides full simulation, no mocking libraries needed
- Test fixtures in `tests/conftest.py`

### Docstring Convention

Uses **Google-style docstrings** (D212 compliant, enforced by ruff):

```python
def example_function(param: int) -> str:
    """Short description on first line.

    Longer description can follow after a blank line.

    Args:
        param: Description of parameter.

    Returns:
        Description of return value.

    Raises:
        ValueError: When parameter is invalid.
    """
```

## Key Files to Know

### Core Application Files

- `daemon/daemon.py`: Main daemon class managing backend lifecycle
- `daemon/app/main.py`: FastAPI application creation and router registration
- `daemon/cli.py`: CLI entry point for `suruga-ew51-daemon` command
- `daemon/backend/abstract.py`: Backend interface definition (20+ abstract methods)

### Backend Implementations

- `daemon/backend/real/real_backend.py`: Real hardware via pythonnet + DLL (563 lines)
- `daemon/backend/mock/mock_backend.py`: Mock simulation (350+ lines)

### Models (Pydantic)

- `models/enums.py`: AxisId, StageId, ServoState, MovementStatus, etc.
- `models/base.py`: Position, AxisStatus, StageStatus, StationStatus
- `models/requests.py`: Request models for API endpoints
- `models/responses.py`: Response models for API endpoints
- `models/alignment.py`: Alignment parameters and status models (470 lines)

### SDK

- `sdk/client.py`: High-level async client (24+ methods)

### Alignment System

- `alignment/alignment_controller.py`: Wraps DLL alignment system (450 lines)

## Hardware Integration Notes

### DLL Integration

**Location**: `src/suruga_seiki_ew51/io/dll/srgmc.dll` (plus dependencies)

**Loading Process** (critical for pythonnet):
1. Load pythonnet with coreclr runtime: `pythonnet.load("coreclr")`
2. Add DLL directory to PATH: `os.environ["PATH"] = dll_dir + os.pathsep + PATH`
3. Import clr: `import clr`
4. Add reference with full path: `clr.AddReference(str(dll_file_path))`
5. Import namespace: `import SurugaSeiki.Motion`

**Why PATH is critical**: The .NET runtime needs to find dependency DLLs (TwinCAT.Ads.dll, System.Reactive.dll, etc.). Adding the DLL directory to PATH allows .NET to resolve these dependencies.

**Requirements**:
- pythonnet package (included with default install)
- .NET Core runtime on system
- All DLL files in same directory

### Axis Components

Real backend creates 12 `AxisComponent` instances (from DLL):
```python
self._axes = [
    AxisComponent(ads_address, i) for i in range(1, 13)
]
```

Access by index: `self._axes[axis.value - 1]` (AxisId is 1-indexed)

### Servo Control Flow

**Important**: Servo must be enabled before any movement:
1. Enable servo: `TurnOnServo()`
2. Move axis: `MoveAbsolute()` or `MoveRelative()`
3. Wait for completion: `GetStatus()` until `InPosition`
4. Disable servo when idle: `TurnOffServo()` (saves power)

## API Documentation

When daemon is running, access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Interactive documentation shows all 30+ endpoints with schemas and try-it-out functionality.

## Testing Against Real Hardware

To test with real hardware:

1. Ensure DLL is present: `src/suruga_seiki_ew51/io/dll/srgmc.dll`
2. Verify .NET runtime installed
3. Hardware connected and powered
4. Run daemon without `--mock` flag: `suruga-ew51-daemon`
5. Use `examples/example_client.py` as reference

Hardware tests should be marked: `@pytest.mark.hardware`

## Common Patterns

### Moving an axis via SDK

```python
from suruga_seiki_ew51.sdk import EW51Client
from suruga_seiki_ew51.models import AxisId

async with EW51Client("http://localhost:8000") as client:
    await client.enable_servo([AxisId.X1])
    await client.move_axis(AxisId.X1, target=1000.0, wait=True)
    position = await client.get_position(AxisId.X1)
    await client.disable_servo([AxisId.X1])
```

### Running optical alignment

```python
from suruga_seiki_ew51.models import FlatAlignmentParameters

params = FlatAlignmentParameters(
    main_stage_number_x=7,
    main_stage_number_y=8,
    search_range_x=500.0,
    # ... 27 more parameters
)

await client.configure_flat_alignment(params, wavelength=1310)
await client.start_flat_alignment()
result = await client.wait_for_alignment_completion(timeout=300)
```

### Adding a new backend method

1. Add abstract method to `AbstractBackend`
2. Implement in `MockBackend` with simulation logic
3. Implement in `RealBackend` with DLL calls
4. Add router endpoint if exposing via API
5. Add SDK client method if needed
6. Write unit tests using mock backend

## Project Status

**Status: Production Ready**

- ✅ 100% of vendor sample program functionality integrated
- ✅ All 12 axes supported with full motion control
- ✅ Complete optical alignment system (flat + focus)
- ✅ 30+ REST API endpoints
- ✅ 24+ SDK methods
- ✅ 40+ Pydantic models
- ✅ Type-safe with mypy strict mode
- ✅ Mock backend for development/testing
- ✅ Documentation and examples

See `docs/development/PROJECT_STATUS.md` for detailed metrics and feature list.
