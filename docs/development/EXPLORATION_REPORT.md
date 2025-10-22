# Comprehensive Exploration Report: Suruga Seiki EW-51 Hardware Integration

## Executive Summary

This report documents the existing implementation patterns from the **Suruga Seiki EW-51 sample program** and the **reachy_mini** reference architecture, designed to guide the migration of hardware control code into the `suruga_seiki_ew51` modular architecture.

Since the original `probe-station-api` repository is not available, this analysis focuses on:
1. The existing Suruga sample program (raw hardware integration)
2. The reachy_mini architecture (best practice reference)
3. The planned suruga_seiki_ew51 modular structure

---

## Part 1: Existing Hardware Integration (suruga_sample_program.py)

### 1.1 DLL Loading and Initialization

**Current Implementation:**
```python
import pythonnet
pythonnet.load("coreclr")
import clr
clr.AddReference("srgmc")
import SurugaSeiki.Motion
```

**Key Classes:**
- `System.Instance` - Global system singleton for controller connection
- `AxisComponents(axisNumber)` - Individual axis objects (axes 1-12)
- `Axis2D(axis1, axis2)` - Multi-axis grouping (e.g., axes 7-8)
- `Alignment()` - Alignment control system
- `Alignment.FlatParameter()` - Flat alignment configuration
- `Alignment.FocusParameter()` - Focus alignment configuration

**Connection Flow:**
1. Get System instance
2. Call `SetAddress("IP.ADDRESS.X.Y")` for ADS connection
3. Check `Connected` property in polling loop
4. Initialize AxisComponents for all axes

### 1.2 Axis Control Operations

**Core Operations:**

| Operation | Method | Returns |
|-----------|--------|---------|
| Position Query | `GetActualPosition()` | float (micrometers) |
| Absolute Move | `MoveAbsolute(position)` | Error code or None |
| Get Status | `GetStatus()` | "InPosition" or other state |
| Servo Control | `IsServoOn()` / `TurnOnServo()` | bool / None |
| System Version | `SystemVersion` | string |
| DLL Version | `DllVersion` | string |

**Movement Pattern:**
```python
# 1. Ensure servo is on
if not AxisComponent.IsServoOn():
    AxisComponent.TurnOnServo()

# 2. Issue movement command
error = AxisComponent.MoveAbsolute(target_position)

# 3. Poll for completion
time.sleep(0.1)
while AxisComponent.GetStatus() != "InPosition":
    position = AxisComponent.GetActualPosition()
    time.sleep(polling_interval)
```

**Critical Observations:**
- Movement is asynchronous (returns immediately)
- Status polling required to detect completion
- Servo must be explicitly enabled
- Error handling via return codes (string "None" vs actual errors)

### 1.3 Axis Numbering Scheme

**Hardware Configuration:**
- **12 Total Axes:** 6 per stage (2 stages)
- **Left Stage (Axes 1-6):** X1, Y1, Z1, TX1, TY1, TZ1
- **Right Stage (Axes 7-12):** X2, Y2, Z2, TX2, TY2, TZ2

**3D/2D Grouping:**
- 2D movements via `Axis2D(7, 8)` for XY stage control
- Supports `Point()` objects with X, Y coordinates

### 1.4 Alignment System

**Flat Alignment (XY in-plane):**
- Parameter object: `FlatAlignmentParameter`
- Key settings:
  - `mainStageNumberX`, `mainStageNumberY` - Axes to move
  - `pmCh` - Power meter channel (1-based)
  - `fieldSearchThreshold`, `peakSearchThreshold` - Search parameters
  - `searchRangeX/Y`, `fieldSearchPitchX/Y` - Movement parameters
  - `searchSpeedX/Y`, `peakSearchSpeedX/Y` - Speed control
  - `pmAutoRangeUpOn`, `pmInitRange` - Power meter settings
  - `smoothingRangeX/Y`, `convergentRangeX/Y` - Convergence tuning
  - `maxRepeatCount` - Retry limit

**Focus Alignment (Z-axis scan):**
- Parameter object: `FocusAlignmentParameter`
- Additional field: `zMode` enum (e.g., `ZMode.Round`)
- Same parameter structure as flat alignment

**Alignment Workflow:**
```python
# 1. Configure parameters
SetFlatAlignmentParameter(FlatAlignmentParameter)
Alignment.SetFlat(FlatAlignmentParameter)
Alignment.SetMeasurementWaveLength(pmCh, wavelength_nm)

# 2. Start alignment
Alignment.StartFlat()

# 3. Poll for status
while Alignment.GetStatus() == "Aligning":
    status = Alignment.GetAligningStatus()  # "FieldSearching", "PeakSearchingX", etc.
    time.sleep(0.5)

# 4. Retrieve results on success
if Alignment.GetStatus() == "Success":
    optical_power = Alignment.GetPower(pmCh)
```

**Alignment Status States:**
- `"Aligning"` - In progress
- `"Success"` - Completed successfully
- `"FieldSearching"` - Phase 1 (field peak search)
- `"PeakSearchingX"` - Phase 2 (X-axis fine search)
- `"PeakSearchingY"` - Phase 3 (Y-axis fine search)

**Profile Data Retrieval:**
```python
profileDataType = Alignment.ProfileDataType.FieldSearch
packetSumIndex = Alignment.GetProfilePacketSumIndex(profileDataType)
for packetNumber in range(1, packetSumIndex + 1):
    profileData = Alignment.RequestProfileData(
        profileDataType, 
        packetNumber, 
        False  # preserveData flag
    )
    # Access: profileData.mainPositionList, profileData.signalCh1List
```

### 1.5 Error Handling Patterns

**Current Approach:**
- Movement commands return error code or `"None"` (string)
- Status checking: `str(AxisComponent.GetStatus())`
- Error axis ID available: `Alignment.GetErrorAxisID()`
- No explicit exceptions; relies on polling and string comparisons

**Issues with Current Pattern:**
- String-based error codes are fragile
- No exception hierarchy for clean error handling
- Polling-based approach creates timing dependencies
- Limited error context (e.g., which axis failed)

---

## Part 2: Architecture Reference (reachy_mini)

### 2.1 Daemon-Backend-SDK Split

**Three-Layer Architecture:**

```
┌─────────────────────────────────────┐
│  SDK (reachy_mini.py)               │
│  High-level Python client API       │
└──────────────┬──────────────────────┘
               │ Zenoh Pub/Sub
┌──────────────▼──────────────────────┐
│  Daemon (daemon.py)                 │
│  Lifecycle + status management      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Backend (abstract.py + impls)      │
│  Hardware abstraction layer         │
│  - Real hardware (RobotBackend)     │
│  - Simulation (MujocoBackend)       │
└─────────────────────────────────────┘
```

**Advantages:**
- Clear separation of concerns
- Can swap backends without changing API
- Daemon can run independently
- SDK doesn't need direct hardware access

### 2.2 Backend Abstraction Pattern

**Abstract Base (abstract.py):**
```python
class Backend:
    """Base class for all backends."""
    
    def run(self) -> None:
        """Main control loop (blocking)."""
        
    def close(self) -> None:
        """Cleanup."""
        
    def get_status(self) -> BackendStatus:
        """Current state snapshot."""
        
    # Target setting
    def set_target_head_joint_positions(positions) -> None:
    def set_target_antenna_joint_positions(positions) -> None:
    
    # State query
    def get_present_head_joint_positions() -> NDArray[float]:
    def get_present_antenna_joint_positions() -> NDArray[float]:
    
    # Movement primitives
    async def goto_target(...) -> None:
    async def goto_joint_positions(...) -> None:
```

**Implementation Approach:**
- Abstract methods throw `NotImplementedError`
- Subclasses (RealBackend, MujocoBackend) implement all methods
- Backend runs in dedicated thread with main control loop
- State updates published via Zenoh

**For Suruga Seiki, Analogous Pattern:**
```python
class Backend:  # Abstract
    def enable_servo(axis_id: int) -> None:
    def disable_servo(axis_id: int) -> None:
    def move_absolute(axis_id: int, position: float) -> None:
    def move_relative(axis_id: int, delta: float) -> None:
    def get_position(axis_id: int) -> float:
    def get_status(axis_id: int) -> AxisStatus:
    def start_alignment(params: AlignmentParams) -> None:
    def get_alignment_status() -> AlignmentStatus:
```

### 2.3 Daemon Lifecycle Management

**Daemon Class (daemon.py):**
```python
class Daemon:
    async def start(sim=False, serialport="auto", ...) -> DaemonState:
        # 1. Setup backend
        # 2. Start server (Zenoh)
        # 3. Start backend thread
        # 4. Wait for backend.ready event
        # 5. Return state
        
    async def stop(goto_sleep_on_stop=True) -> DaemonState:
        # 1. Signal backend to stop
        # 2. Wait for thread (timeout: 5s)
        # 3. Close backend
        # 4. Return state
        
    def status() -> DaemonStatus:
        # Returns current state, backend status, error info
```

**State Machine:**
```
NOT_INITIALIZED → STARTING → RUNNING
                                ↓
                             STOPPING → STOPPED
                             ↗
                          ERROR (from any state)
```

### 2.4 FastAPI Application Structure

**Main App (app/main.py):**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage daemon startup/shutdown with FastAPI app lifecycle."""
    args = app.state.args
    await app.state.daemon.start(...)
    yield
    await app.state.daemon.stop(...)

app = FastAPI(lifespan=lifespan)
app.state.daemon = Daemon(...)
app.state.app_manager = AppManager()

# Add middleware, routers
router = APIRouter(prefix="/api")
router.include_router(move.router)  # Movement endpoints
router.include_router(state.router)  # State query endpoints
router.include_router(motors.router)  # Motor control endpoints
```

**Router Pattern (routers/*.py):**
```python
router = APIRouter(prefix="/move")

@router.post("/goto")
async def goto_endpoint(
    request: GotoRequest,
    backend: Backend = Depends(get_backend)
) -> MovementResult:
    """Move to target position."""
    await backend.goto_target(...)
    return MovementResult(...)

@router.websocket("/ws/stream")
async def stream_endpoint(websocket: WebSocket):
    """Stream movement updates."""
    backend = ws_get_backend(websocket)
    await websocket.accept()
    try:
        while True:
            state = backend.get_status()
            await websocket.send_json(state)
    except WebSocketDisconnect:
        pass
```

**CLI Integration:**
```bash
reachy-mini-daemon --sim --scene empty --headless
reachy-mini-daemon -p /dev/ttyUSB0  # Real robot
```

### 2.5 Error Handling Pattern

**Exception Hierarchy:**
```python
class BackendError(Exception):
    """Base for all backend errors."""
    
class HardwareError(BackendError):
    """Hardware communication failure."""
    
class CollisionError(BackendError):
    """Kinematics collision detected."""
    
class TimeoutError(BackendError):
    """Operation exceeded timeout."""
```

**Graceful Degradation:**
```python
try:
    await backend.goto_target(...)
except CollisionError as e:
    logger.error(f"Path blocked: {e}")
    # SDK can retry or user handles
except HardwareError as e:
    logger.error(f"Hardware failure: {e}")
    daemon.status.state = DaemonState.ERROR
```

**HTTP Error Mapping:**
```python
@app.exception_handler(BackendError)
async def handle_backend_error(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )

@app.exception_handler(TimeoutError)
async def handle_timeout(request, exc):
    return JSONResponse(status_code=408, content={"detail": str(exc)})
```

### 2.6 Testing Strategy

**Test Markers:**
```bash
pytest -m "not hardware"  # Skip hardware-dependent tests
pytest -m "hardware"      # Run hardware tests only
```

**Backend Abstraction Benefits for Testing:**
```python
# Test with MujocoBackend (simulation)
@pytest.fixture
def sim_backend():
    return MujocoBackend(...)

# Test with RealBackend (real hardware)
@pytest.mark.hardware
@pytest.fixture
def real_backend():
    return RobotBackend(port="/dev/ttyUSB0")

# Same tests run against both
def test_goto_movement(backend):
    # Works for both sim and real
    await backend.goto_target(...)
    assert backend.get_status().moving == False
```

---

## Part 3: Key Implementation Insights for Suruga Seiki

### 3.1 Hardware-Specific Challenges

**Challenge 1: Asynchronous Movement**
- Problem: DLL operations return immediately; completion detected via polling
- Solution: Backend control loop polls axis status, publishes updates via event/callback
- Pattern:
  ```python
  async def move_absolute(axis_id, position):
      # Issue command
      self.dll.MoveAbsolute(axis_id, position)
      # Poll in background control loop
      # Signal completion via event/semaphore
  ```

**Challenge 2: Servo State Management**
- Problem: Servo must be explicitly enabled before movement
- Solution: Track servo state, auto-enable on movement requests, disable on timeout
- Pattern:
  ```python
  async def move_absolute(axis_id, position):
      if not self.servo_enabled[axis_id]:
          self._enable_servo(axis_id)
          await self._wait_servo_ready(axis_id, timeout=2.0)
      # Then issue movement
  ```

**Challenge 3: Multi-Axis Coordination**
- Problem: Suruga has separate AxisComponent objects; no native grouped control
- Solution: Backend manages Axis2D objects, coordinates multi-axis moves
- Pattern:
  ```python
  async def move_2d_relative(axes=(7, 8), delta=(dx, dy)):
      # Create Point object
      point = self.dll.Axis2D.Point()
      point.X, point.Y = delta
      error = self.axis_2d.MoveRelative(point)
      # Poll axis_2d.GetStatus()
  ```

**Challenge 4: Alignment Parameter Complexity**
- Problem: 30+ parameters per alignment type
- Solution: Use Pydantic models, nested configuration objects
- Pattern:
  ```python
  class FlatAlignmentParams(BaseModel):
      main_stage_x: int
      main_stage_y: int
      pm_channel: int
      search_range_x: float
      search_range_y: float
      # ... 25 more fields
      
      def to_dll_params(self) -> DLLAlignmentParams:
          # Convert to DLL format
  ```

### 3.2 Proposed Backend Interface

**Core Axis Operations:**
```python
class Backend:
    # Servo control
    async def enable_servo(self, axis_id: AxisId) -> None:
        """Enable servo for axis."""
        
    async def disable_servo(self, axis_id: AxisId) -> None:
        """Disable servo for axis."""
        
    def is_servo_enabled(self, axis_id: AxisId) -> bool:
        """Query servo state."""
    
    # Movement primitives
    async def move_absolute(
        self, 
        axis_id: AxisId, 
        position: float,
        timeout: float = 30.0
    ) -> None:
        """Move to absolute position (micrometers)."""
        
    async def move_relative(
        self,
        axis_id: AxisId,
        delta: float,
        timeout: float = 30.0
    ) -> None:
        """Move relative to current position."""
    
    async def move_2d(
        self,
        axes: tuple[AxisId, AxisId],
        position: tuple[float, float],
        timeout: float = 30.0
    ) -> None:
        """2D coordinated move (e.g., XY stage)."""
    
    # State query
    def get_position(self, axis_id: AxisId) -> float:
        """Current position (micrometers)."""
        
    def get_status(self, axis_id: AxisId) -> AxisStatus:
        """Detailed axis status."""
    
    # Alignment
    async def start_alignment(
        self,
        params: Union[FlatAlignmentParams, FocusAlignmentParams],
        timeout: float = 300.0
    ) -> AlignmentResult:
        """Run alignment procedure."""
        
    def get_alignment_status(self) -> AlignmentStatus:
        """Query alignment progress."""
        
    def get_alignment_profile_data(
        self,
        data_type: ProfileDataType,
        packet_number: int
    ) -> ProfileData:
        """Retrieve alignment scan data."""
```

### 3.3 Proposed Models

```python
from enum import Enum
from pydantic import BaseModel, Field

class AxisId(int):
    """Axis identifier (1-12)."""
    pass

class AxisStatus(str, Enum):
    IN_POSITION = "in_position"
    MOVING = "moving"
    ERROR = "error"
    SERVO_OFF = "servo_off"

class Position(BaseModel):
    axis_id: AxisId
    position_um: float
    status: AxisStatus
    servo_enabled: bool

class FlatAlignmentParams(BaseModel):
    """Flat (XY) alignment configuration."""
    main_stage_x: int = Field(ge=1, le=12)
    main_stage_y: int = Field(ge=1, le=12)
    pm_channel: int = Field(ge=1)
    field_search_threshold: float
    peak_search_threshold: float
    search_range_x_um: float
    search_range_y_um: float
    search_speed_um_s: float
    peak_search_speed_um_s: float
    wavelength_nm: float = 1310.0

class AlignmentStatus(str, Enum):
    IDLE = "idle"
    ALIGNING = "aligning"
    FIELD_SEARCHING = "field_searching"
    PEAK_SEARCHING_X = "peak_searching_x"
    PEAK_SEARCHING_Y = "peak_searching_y"
    SUCCESS = "success"
    ERROR = "error"

class AlignmentResult(BaseModel):
    success: bool
    final_position_x_um: float
    final_position_y_um: float
    optical_power_dbm: float
    field_search_data: Optional[List[float]]
    peak_search_x_data: Optional[List[float]]
    peak_search_y_data: Optional[List[float]]
```

### 3.4 Real vs Mock Backend Comparison

**RealBackend (pythonnet + srgmc.dll):**
```python
class RealBackend(Backend):
    def __init__(self, dll_path, controller_ip):
        pythonnet.load("coreclr")
        clr.AddReference(dll_path)
        self.system = SurugaSeiki.Motion.System.Instance
        self.system.SetAddress(controller_ip)
        self.axes = {i: SurugaSeiki.Motion.AxisComponents(i) for i in range(1, 13)}
        
    async def move_absolute(self, axis_id, position, timeout):
        if not self.servo_enabled[axis_id]:
            self._enable_servo(axis_id)
        error = self.axes[axis_id].MoveAbsolute(position)
        if str(error) != "None":
            raise HardwareError(f"Axis {axis_id} move failed: {error}")
        # Poll for completion
        t0 = time.time()
        while time.time() - t0 < timeout:
            status = str(self.axes[axis_id].GetStatus())
            if status == "InPosition":
                return
            await asyncio.sleep(0.1)
        raise TimeoutError(f"Axis {axis_id} move exceeded {timeout}s")
```

**MockBackend (simulation):**
```python
class MockBackend(Backend):
    def __init__(self):
        self.positions = {i: 0.0 for i in range(1, 13)}
        self.servo_enabled = {i: False for i in range(1, 13)}
        
    async def move_absolute(self, axis_id, position, timeout):
        if not self.servo_enabled[axis_id]:
            raise ServoDisabledError(f"Servo {axis_id} is off")
        # Simulate movement
        start = self.positions[axis_id]
        speed = 1000.0  # um/s
        distance = abs(position - start)
        duration = distance / speed
        await asyncio.sleep(min(duration, timeout))
        self.positions[axis_id] = position
```

---

## Part 4: API Endpoint Design

### 4.1 Movement Endpoints

```
POST /ew51/axes/{axis_id}/move-absolute
{
    "position_um": 1000.5,
    "timeout_s": 30.0
}

POST /ew51/axes/{axis_id}/move-relative
{
    "delta_um": 100.0,
    "timeout_s": 30.0
}

GET /ew51/axes/{axis_id}/position

POST /ew51/move-2d
{
    "axes": [7, 8],
    "x_um": 1000.0,
    "y_um": 2000.0,
    "timeout_s": 30.0
}
```

### 4.2 Servo Control Endpoints

```
POST /ew51/axes/{axis_id}/servo/enable

POST /ew51/axes/{axis_id}/servo/disable

GET /ew51/axes/{axis_id}/servo/status
→ {"enabled": true, "axis_id": 7}
```

### 4.3 Alignment Endpoints

```
POST /ew51/alignment/start-flat
{
    "main_stage_x": 7,
    "main_stage_y": 8,
    "pm_channel": 1,
    "search_range_x_um": 500.0,
    "search_range_y_um": 500.0,
    "timeout_s": 300.0
}

GET /ew51/alignment/status
→ {"status": "field_searching", "progress": 0.35}

GET /ew51/alignment/profile-data
{
    "data_type": "field_search",
    "packet_number": 1
}

POST /ew51/alignment/stop
```

### 4.4 Status/Config Endpoints

```
GET /ew51/status
→ {
    "system_version": "1.2.3",
    "dll_version": "2.0.0",
    "connected": true,
    "axes": [
        {"id": 1, "position": 100.0, "servo_enabled": true, ...},
        ...
    ]
}

GET /ew51/config
→ {
    "controller_ip": "5.107.162.80.1.1",
    "stage_count": 2,
    "calibration": {...}
}
```

---

## Part 5: Summary of Key Patterns

### 5.1 Architecture Checklist

- [ ] **Daemon-Backend-SDK Split**
  - Daemon manages lifecycle and backend
  - Backend abstracts hardware communication
  - SDK provides high-level client API

- [ ] **Backend Abstraction**
  - Abstract base class with methods for all hardware operations
  - Real backend wraps DLL calls
  - Mock backend for testing

- [ ] **Async Control Loop**
  - Backend runs in dedicated thread
  - State updates published regularly
  - Non-blocking operation handling

- [ ] **FastAPI Application**
  - Lifespan context manager for daemon lifecycle
  - Router-based endpoint organization
  - Dependency injection for backend/daemon access

- [ ] **Error Handling**
  - Custom exception hierarchy
  - HTTP error mapping
  - Graceful timeout/retry logic

### 5.2 Implementation Order

1. **Phase 1: Core Infrastructure**
   - Backend abstract class
   - Daemon lifecycle management
   - FastAPI app setup with routers

2. **Phase 2: Basic Hardware Integration**
   - RealBackend: Servo enable/disable
   - RealBackend: Absolute/relative movement
   - RealBackend: Position query

3. **Phase 3: Mock Backend & Testing**
   - MockBackend implementation
   - Unit tests for movement primitives
   - Integration tests with FastAPI

4. **Phase 4: Advanced Features**
   - 2D coordinated movement
   - Alignment system integration
   - Profile data retrieval

5. **Phase 5: SDK & Polish**
   - High-level SDK client
   - Example scripts
   - Comprehensive error handling

### 5.3 File Structure Reference

```
src/suruga_seiki_ew51/
├── daemon/
│   ├── __init__.py
│   ├── daemon.py              # Daemon class with lifecycle
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app creation + CLI
│   │   ├── dependencies.py    # Dependency injection
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── movement.py    # /ew51/move/* endpoints
│   │       ├── servo.py       # /ew51/servo/* endpoints
│   │       ├── alignment.py   # /ew51/alignment/* endpoints
│   │       └── status.py      # /ew51/status/* endpoints
│   └── backend/
│       ├── __init__.py
│       ├── abstract.py        # Backend ABC
│       ├── real/
│       │   ├── __init__.py
│       │   └── backend.py     # RealBackend (DLL integration)
│       └── mock/
│           ├── __init__.py
│           └── backend.py     # MockBackend (simulation)
├── sdk/
│   ├── __init__.py
│   └── client.py              # High-level SDK
├── io/
│   ├── __init__.py
│   ├── dll/
│   │   └── srgmc.dll         # Place DLL here
│   └── communication.py       # Generic I/O utilities
├── models/
│   ├── __init__.py
│   ├── axis.py               # AxisId, Position, AxisStatus
│   ├── alignment.py          # AlignmentParams, AlignmentResult
│   └── requests.py           # API request models
├── config/
│   ├── __init__.py
│   └── settings.py           # Global configuration
├── exceptions.py             # Custom exception hierarchy
└── utils/
    ├── __init__.py
    └── helpers.py            # Shared utilities
```

---

## Conclusion

The Suruga Seiki EW-51 hardware integration should follow the **reachy_mini architectural pattern** while accommodating:

1. **Asynchronous hardware operations** requiring polling-based completion detection
2. **Complex alignment system** with 30+ configurable parameters
3. **Multi-stage coordination** (12 axes across 2 stages)
4. **Servo state management** requiring explicit enable/disable

The existing sample program demonstrates:
- DLL loading via pythonnet
- Basic movement/status polling patterns
- Alignment workflow with profile data retrieval
- Error detection through status strings

By mapping these patterns onto the reachy_mini architecture, you can achieve:
- Clean modular code structure
- Testable backend abstraction
- Production-quality FastAPI daemon
- Comprehensive error handling
- Easy-to-use SDK for client applications

---

## References

**Key Files Analyzed:**
- `/Users/lucas/Documents/git/github/suruga_seiki_ew51/suruga_sample_program.py` - Hardware integration reference
- `/Users/lucas/Documents/git/github/reachy_mini/src/reachy_mini/daemon/daemon.py` - Daemon lifecycle pattern
- `/Users/lucas/Documents/git/github/reachy_mini/src/reachy_mini/daemon/backend/abstract.py` - Backend abstraction
- `/Users/lucas/Documents/git/github/reachy_mini/src/reachy_mini/daemon/app/main.py` - FastAPI setup
- `/Users/lucas/Documents/git/github/suruga_seiki_ew51/CLAUDE.md` - Project requirements

