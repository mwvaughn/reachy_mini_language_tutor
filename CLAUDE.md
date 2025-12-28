# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Conversational AI application for the Reachy Mini robot integrating OpenAI's realtime API, vision processing, and choreographed motion. The app enables real-time audio conversations with the robot while coordinating dance moves, emotions, head tracking, and vision processing through a layered motion system.

## Important Resources

**ALWAYS consult the Reachy Mini Python SDK documentation for canonical information about robot implementation and design:**
- **SDK Documentation**: https://github.com/pollen-robotics/reachy_mini/blob/develop/docs/SDK/readme.md

When working on robot control, motion systems, hardware interfaces, or any Reachy Mini-specific functionality, refer to the official SDK documentation first. This is the authoritative source for:
- Robot API reference and methods
- Hardware capabilities and limitations
- Control loop best practices
- Joint limits and coordinate systems
- Official code examples and patterns

## Build & Run Commands

### Installation
```bash
# Using uv (recommended)
uv venv --python 3.12.1
source .venv/bin/activate
uv sync                              # Base install
uv sync --extra all_vision           # With all vision features
uv sync --extra reachy_mini_wireless # For wireless robot support
uv sync --group dev                  # Add dev tools (pytest, ruff, mypy)

# Using pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -e .[all_vision,dev]
```

### Running the App
```bash
reachy-mini-conversation-app                           # Console mode (default)
reachy-mini-conversation-app --gradio                  # Web UI at http://127.0.0.1:7860/
reachy-mini-conversation-app --head-tracker mediapipe # With face tracking
reachy-mini-conversation-app --local-vision            # Local SmolVLM2 vision
reachy-mini-conversation-app --wireless-version        # For wireless robot
reachy-mini-conversation-app --no-camera               # Audio-only mode
reachy-mini-conversation-app --profile <name>          # Load custom profile
```

### Development Workflow
```bash
ruff check .      # Lint and format check
ruff format .     # Auto-format code
mypy src/         # Type checking (strict mode enabled)
pytest            # Run test suite
pytest tests/test_openai_realtime.py  # Run specific test file
```

## Architecture

### Layered Motion System (Core Design)
The robot uses a **compose-based motion blending** system with primary and secondary layers:

**Primary Moves** (sequential, mutually exclusive queue in `MovementManager`):
- Dances (from `reachy_mini_dances_library`)
- Recorded emotions (Hugging Face assets)
- Goto poses (head positioning)
- Breathing (idle state fallback)

**Secondary Offsets** (additive, blended in real-time):
- Speech wobble (`HeadWobbler`) - reactive to audio stream activity
- Face tracking offsets (`CameraWorker`) - smooth interpolation with 2s fade-out when face is lost

**Control Loop**: `MovementManager` runs at **100Hz** in a dedicated thread, composing primary + secondary poses and calling `robot.set_target()`.

### Threading Model
- **Main thread**: Launches Gradio/console UI
- **MovementManager thread**: 100Hz motion control loop
- **HeadWobbler thread**: Audio-reactive motion processing (speech detection)
- **CameraWorker thread**: 30Hz+ frame capture + face tracking
- **VisionManager thread**: Periodic local VLM inference (if `--local-vision` enabled)

### Tool Dispatch Pattern
```
User audio → OpenaiRealtimeHandler (24kHz mono WebRTC)
  → LLM generates tool calls
  → dispatch_tool_call() routes to Tool subclass
  → Tool enqueues command in MovementManager
  → MovementManager executes and returns status via AdditionalOutputs
  → Response audio + motion sent to robot/user
```

### Vision Pipeline Options
- **Default (gpt-realtime)**: Camera tool sends frames to OpenAI for vision
- **Local vision (`--local-vision`)**: VisionManager processes frames with SmolVLM2 (on-device CPU/GPU/MPS)
- **Face tracking options**:
  - `--head-tracker yolo`: YOLOv8-based face detection (requires `yolo_vision` extra)
  - `--head-tracker mediapipe`: MediaPipe from `reachy_mini_toolbox` (requires `mediapipe_vision` extra, pinned to 0.10.14)

## Key File Responsibilities

| File/Directory | Purpose |
|----------------|---------|
| `main.py` | Entry point - initializes robot, managers, UI (Gradio or console) |
| `openai_realtime.py` | `OpenaiRealtimeHandler` - async WebRTC stream to OpenAI realtime API |
| `moves.py` | `MovementManager` - 100Hz motion control loop with queue management |
| `camera_worker.py` | `CameraWorker` - thread-safe frame buffering + face tracking offset calculation |
| `audio/head_wobbler.py` | Speech-reactive head wobble (additive motion from audio stream) |
| `tools/core_tools.py` | `Tool` base class + dispatch logic for LLM tool calls |
| `tools/` | Built-in tools: `move_head`, `dance`, `play_emotion`, `camera`, `head_tracking`, etc. |
| `config.py` | `Config` class - loads `.env` and manages profile settings |
| `prompts.py` | Prompt loading with `[placeholder]` syntax for reusable components |
| `console.py` | `LocalStream` - headless mode with direct audio I/O + settings routes |
| `gradio_personality.py` | `PersonalityUI` - profile selector, creator, live instruction reload |
| `vision/processors.py` | Local vision manager (SmolVLM2 initialization) |
| `vision/yolo_head_tracker.py` | YOLO-based face detection for head tracking |
| `profiles/` | Personality profiles with `instructions.txt` + `tools.txt` + optional custom tools |

## Personality/Profile System

Each profile in `src/reachy_mini_conversation_app/profiles/<name>/` contains:
- **`instructions.txt`**: System prompt (supports `[placeholder]` syntax to pull from `prompts/`)
- **`tools.txt`**: Enabled tools list (comment with `#`, one per line)
- **Optional Python files**: Custom tool implementations (subclass `Tool` from `tools/core_tools.py`)

Load profiles via:
- CLI: `--profile <name>`
- Environment: `REACHY_MINI_CUSTOM_PROFILE=<name>` in `.env`
- Gradio UI: Select and hot-reload instructions (tools require restart)

17+ pre-made profiles available in `profiles/` (detective, butler, cosmic_kitchen, mars_rover, etc.)

## Configuration (.env)

Required:
```
OPENAI_API_KEY=your_key_here
```

Optional:
```
MODEL_NAME=gpt-realtime                                   # Override realtime model
HF_HOME=./cache                                           # Local VLM cache (--local-vision)
HF_TOKEN=your_hf_token                                    # For Hugging Face models/emotions
LOCAL_VISION_MODEL=HuggingFaceTB/SmolVLM2-2.2B-Instruct  # Local vision model path
REACHY_MINI_CUSTOM_PROFILE=default                        # Profile to load
```

## Available LLM Tools

| Tool | Action | Dependencies |
|------|--------|--------------|
| `move_head` | Queue head pose change (left/right/up/down/front) | Core |
| `camera` | Capture frame and send to vision model | Camera worker |
| `head_tracking` | Enable/disable face-tracking offsets (not facial recognition) | Camera + head tracker |
| `dance` | Queue dance from `reachy_mini_dances_library` | Core |
| `stop_dance` | Clear dance queue | Core |
| `play_emotion` | Play recorded emotion clip | Core + `HF_TOKEN` |
| `stop_emotion` | Clear emotion queue | Core |
| `do_nothing` | Explicitly remain idle | Core |

## Code Style Conventions

- **Type checking**: Strict mypy enabled (`mypy src/`)
- **Formatting**: Ruff with 119-char line length
- **Docstrings**: Required for all public functions/classes (ruff `D` rules enabled)
- **Import sorting**: `isort` via ruff (local-folder: `reachy_mini_conversation_app`)
- **Quote style**: Double quotes
- **Async patterns**: Use `asyncio` for OpenAI realtime API, threading for robot control

## Development Tips

### Adding Custom Tools
1. Create Python file in `profiles/<profile_name>/` (e.g., `sweep_look.py`)
2. Subclass `reachy_mini_conversation_app.tools.core_tools.Tool`
3. Implement `name`, `description`, `parameters`, and `__call__()` method
4. Add tool name to `profiles/<profile_name>/tools.txt`
5. See `profiles/example/sweep_look.py` for reference

### Motion Control Principles
- **100Hz loop is sacred** - never block the `MovementManager` thread
- Offload heavy work to separate threads/processes
- Primary moves are queued and executed sequentially
- Secondary offsets are blended additively in real-time
- Use `BreathingMove` as idle fallback when queue is empty

**Critical SDK Constraints:**
- **65° Yaw Delta Limit**: Head yaw and body yaw cannot differ by more than 65°. The SDK auto-clamps violations, which means aggressive head tracking or wobble offsets may be silently limited if they push the combined pose beyond this constraint.
- **set_target() vs goto_target()**: This app uses `set_target()` in the 100Hz loop because it bypasses interpolation, allowing real-time composition of primary + secondary poses. Using `goto_target()` would conflict with the manual control loop since it runs its own interpolation.

### Thread Safety
- `CameraWorker` uses locks for frame buffer and tracking offsets
- `MovementManager` uses queue for command dispatch
- Never share mutable state between threads without synchronization

### Vision Processing
- Default vision goes through OpenAI's gpt-realtime (when camera tool is called)
- Local vision (`--local-vision`) runs SmolVLM2 periodically on-device
- Face tracking is separate from vision - it only tracks face position for head offsets (not recognition)

### Working with Gradio UI

**Architecture**:
- Gradio UI runs in the main thread, launched by `main.py`
- Provides web interface at `http://127.0.0.1:7860/` (default port)
- Runs alongside robot control threads (does not block motion control)
- Two main UI components:
  - `console.py`: `LocalStream` class handles audio I/O and settings routes for headless/console mode
  - `gradio_personality.py`: `PersonalityUI` class manages profile selection and live instruction reloading

**Key UI Features**:
- **Live audio streaming**: Bidirectional audio via Gradio's audio components
- **Profile management**: Hot-reload personality instructions without restart (tools require restart)
- **Settings routes**: Dynamic endpoints for UI configuration and state
- **Real-time feedback**: Status updates and conversation display

**Development Guidelines**:
- **State management**: Gradio components should not hold critical state - use `MovementManager`, `OpenaiRealtimeHandler`, or `Config` as source of truth
- **Thread safety**: UI callbacks may run in separate threads - always use proper synchronization when accessing shared resources
- **Blocking operations**: Never perform long-running operations directly in Gradio callbacks - offload to background threads/queues
- **Hot-reloading**: Changes to Gradio UI code require app restart (unlike profile instructions which can be hot-reloaded)
- **Testing**: Test UI locally with `--gradio` flag before deploying changes

**Common Patterns**:
- Use `gr.Audio()` with streaming for real-time audio I/O
- Use `gr.Dropdown()` for profile selection with dynamic refresh
- Use `gr.Button()` callbacks to trigger actions via `MovementManager` queue
- Use `gr.Textbox()` with `interactive=True` for live instruction editing
- Return updates via component `.update()` methods for reactive UI

**Gradio-Specific Considerations**:
- Gradio apps auto-reload on file changes in debug mode (use `debug=True` in `gr.Interface.launch()`)
- Share links (`share=True`) create public tunnels - avoid for production
- Custom CSS/themes can be applied via `gr.themes` or custom CSS strings
- Component visibility and interactivity can be toggled dynamically via `.update()`

**Debugging**:
- Check browser console for JavaScript errors
- Use `print()` statements in callbacks (visible in terminal output)
- Gradio exceptions are caught and displayed in UI - check both UI and terminal
- Audio issues: Verify browser permissions for microphone/speaker access

## Testing
- Tests located in `tests/`
- Key test: `test_openai_realtime.py` (AsyncStreamHandler tests)
- Audio fixtures available in `conftest.py`
- Run with `pytest` after `uv sync --group dev`

## Dependencies & Extras

| Extra | Purpose | Key Packages |
|-------|---------|--------------|
| Base | Core audio/vision/motion | `fastrtc`, `aiortc`, `openai`, `gradio`, `opencv-python`, `reachy_mini` |
| `reachy_mini_wireless` | Wireless robot support | `PyGObject`, `gst-signalling` (GStreamer) |
| `local_vision` | Local VLM processing | `torch`, `transformers`, `num2words` |
| `yolo_vision` | YOLO head tracking | `ultralytics`, `supervision` |
| `mediapipe_vision` | MediaPipe tracking | `mediapipe==0.10.14` |
| `all_vision` | All vision features | Combination of above |
| `dev` | Development tools | `pytest`, `ruff`, `mypy`, `pre-commit` |

## Common Troubleshooting

**TimeoutError on startup**: Reachy Mini daemon not running. Install and start Reachy Mini SDK.

**Vision not working**: Check that camera is connected and accessible. Use `--no-camera` to disable if not needed.

**Wireless connection issues**: Ensure `--wireless-version` flag is used and daemon started with same flag. Requires `reachy_mini_wireless` extra.

**Local vision slow**: SmolVLM2 benefits from GPU/MPS acceleration. Consider using default gpt-realtime vision if CPU-only.
