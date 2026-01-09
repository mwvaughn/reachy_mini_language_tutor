# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project Overview
Reachy Language Partner - language learning companion for Reachy Mini robot with multi-language support (French, Spanish, German, Italian, Portuguese). Features persistent memory, error tracking, grammar deep-dives, and expressive robot feedback. Powered by OpenAI realtime API, vision processing, and choreographed motion.

## Important Resources
**SDK Documentation**: https://github.com/pollen-robotics/reachy_mini/blob/develop/docs/SDK/readme.md - Consult for robot control, motion systems, hardware interfaces, API reference, and best practices.

## Commands

**Setup**: `uv sync` (base), `uv sync --extra all_vision` (with vision), `uv sync --group dev` (dev tools)

**Run**: `reachy-mini-language-tutor` (console), `--gradio` (web UI), `--profile <name>` (custom profile), `--source-language <lang>` + `--target-language <lang>` (dynamic language pair), `--local-vision`, `--wireless-version`, `--no-camera`

**Dev**: Always use `uv run` prefix: `uv run ruff check .`, `uv run ruff format .`, `uv run mypy reachy_mini_language_tutor/`, `uv run pytest`

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
Main (UI), MovementManager (100Hz control), HeadWobbler (audio-reactive), CameraWorker (30Hz capture/tracking), VisionManager (local VLM if `--local-vision`)

### Tool Dispatch
User audio → OpenaiRealtimeHandler → LLM tool calls → dispatch_tool_call() → Tool subclass → MovementManager queue → robot execution

### Vision
Default: OpenAI gpt-realtime | Local: SmolVLM2 (`--local-vision`) | Face tracking: yolo/mediapipe (`--head-tracker`)

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

## Language Profiles

Six preset tutor profiles in `profiles/`: `default`, `french_tutor`, `spanish_tutor`, `german_tutor`, `italian_tutor`, `portuguese_tutor`

**Dynamic Language Pairs**: Use `--source-language <lang> --target-language <lang>` for any language combination. Profiles are generated dynamically using OpenAI and cached in `generated_profiles/`.

**Profile structure** (`profiles/<name>/`):
- `instructions.txt`: System prompt with `[placeholder]` syntax (shared prompts from `prompts/language_tutoring/` + unique content)
- `tools.txt`: Enabled tools (one per line, `#` comments)
- `proactive.txt`, `language.txt`, `voice.txt`: Behavioral config
- Optional Python files: Custom tools (subclass `Tool` from `tools/core_tools.py`)

**Load**: `--profile <name>`, `--source-language + --target-language`, `REACHY_MINI_CUSTOM_PROFILE=<name>` in `.env`, or Gradio UI

## Tutor Behavior

Tutors use grammar explanation mode (pause for English deep-dives), error pattern tracking (`remember` tool, category: `struggle`), and session summaries (category: `progress`). See profile `instructions.txt` for methodology details.

## Configuration (.env)

**Required**: `OPENAI_API_KEY`

**Optional**: `REACHY_MINI_CUSTOM_PROFILE`, `SUPERMEMORY_API_KEY` (persistent memory, powers `recall`/`remember` tools), `MODEL_NAME`, `HF_HOME`, `HF_TOKEN`, `LOCAL_VISION_MODEL`

**Privacy**: Memory stores first names, general region, occupation, interests, learning data. Excludes age, specific location, family names, sensitive details.

## Available LLM Tools

`move_head`, `camera`, `head_tracking`, `dance`, `stop_dance`, `play_emotion`, `stop_emotion`, `do_nothing`, `recall` (requires `SUPERMEMORY_API_KEY`), `remember` (requires `SUPERMEMORY_API_KEY`)

## Code Style

Strict mypy, Ruff (119-char lines), docstrings required, double quotes, `asyncio` for OpenAI API, threading for robot control. Always use `uv run` for dev tools.

## Development Tips

**Custom Tools**: Subclass `Tool` from `tools/core_tools.py`, implement `name`/`description`/`parameters`/`__call__()`, add to `tools.txt`. See `tools/recall.py` for example.

**Motion Control**: Never block 100Hz `MovementManager` thread. Primary moves queue sequentially, secondary offsets blend additively. Use `set_target()` (not `goto_target()` which has own interpolation). **Critical**: 65° yaw delta limit (head-body), SDK auto-clamps violations.

**Thread Safety**: Use locks (`CameraWorker`) or queues (`MovementManager`). Never share mutable state without synchronization.

**Gradio UI**: Runs in main thread (`main.py`), port 7860. Components: `console.py` (`LocalStream`), `gradio_personality.py` (`PersonalityUI`). Never block callbacks - offload to threads/queues. State in `MovementManager`/`OpenaiRealtimeHandler`/`Config`, not UI. Instructions hot-reload, code/tools need restart.

## Testing & Dependencies

**Tests**: `tests/` (key: `test_openai_realtime.py`). Run with `uv run pytest`.

**Extras**: `all_vision` (all features), `reachy_mini_wireless`, `local_vision`, `yolo_vision`, `mediapipe_vision`, `dev`

## Troubleshooting

TimeoutError: Start Reachy Mini daemon | Vision issues: Check camera or use `--no-camera` | Wireless: Use `--wireless-version` + `reachy_mini_wireless` extra | Slow local vision: Use GPU/MPS or default gpt-realtime
