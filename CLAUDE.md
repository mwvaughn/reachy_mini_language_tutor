# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Reachy Language Partner - a language learning companion for the Reachy Mini robot. Practice conversational skills in French, Spanish, German, Italian, Portuguese, and other languages through natural dialogue with an expressive robot partner.

**Key Features:**
- Persistent memory across sessions (tracks progress, struggles, preferences)
- Proactive engagement and gentle correction through recasting
- Grammar deep-dive mode with complete explanations on demand
- Error pattern tracking with proactive review at session start
- Session summaries with highlights and next-steps recommendations
- Expressive robot feedback (dances, emotions, celebrations)

Powered by OpenAI's realtime API, vision processing, and choreographed motion.

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
reachy-mini-language-tutor                           # Console mode (default)
reachy-mini-language-tutor --gradio                  # Web UI at http://127.0.0.1:7860/
reachy-mini-language-tutor --head-tracker mediapipe # With face tracking
reachy-mini-language-tutor --local-vision            # Local SmolVLM2 vision
reachy-mini-language-tutor --wireless-version        # For wireless robot
reachy-mini-language-tutor --no-camera               # Audio-only mode
reachy-mini-language-tutor --profile <name>          # Load custom profile
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

## Language Profile System

Six language tutor profiles available in `profiles/`:
- **`default`**: Generic language partner that adapts to any language
- **`french_tutor`**: Delphine, a French conversation partner with cultural context
- **`spanish_tutor`**: Sofia, a Mexican Spanish conversation partner
- **`german_tutor`**: Lukas, a German tutor teaching Standard German (Hochdeutsch)
- **`italian_tutor`**: Chiara, an Italian tutor from Florence with cultural insights
- **`portuguese_tutor`**: Rafael, a Brazilian Portuguese tutor from São Paulo

Each profile in `src/reachy_mini_language_tutor/profiles/<name>/` contains:
- **`instructions.txt`**: System prompt (uses `[placeholder]` syntax to compose from shared + unique content)
- **`tools.txt`**: Enabled tools list (comment with `#`, one per line)
- **`proactive.txt`**: Set to `true` for proactive greeting mode
- **`language.txt`**: ISO language code for transcription (e.g., `es`, `fr`)
- **`voice.txt`**: Voice name (e.g., `coral`, `sage`)
- **Optional Python files**: Custom tool implementations (subclass `Tool` from `tools/core_tools.py`)

### Template-Based Instruction Design

Tutor `instructions.txt` files compose from **shared prompts** (in `prompts/language_tutoring/`) + **unique content**:

**Shared prompts** (13 files, ~165 lines total):
- `[language_tutoring/proactive_engagement]` - Session start, memory recall, collecting personal info
- `[language_tutoring/language_behavior]` - English-first instruction approach
- `[language_tutoring/adaptive_support]` - Detecting and responding to learner struggle
- `[language_tutoring/correction_style]` - Recasting and error handling
- `[language_tutoring/grammar_explanation_structure]` - Framework for "why?" deep-dives
- `[language_tutoring/conversation_topics]` - Topic guidance
- `[language_tutoring/robot_expressiveness]` - Using robot capabilities for teaching
- `[language_tutoring/response_guidelines]` - Response format guidance
- `[language_tutoring/vocabulary_teaching]` - New word introduction pattern
- `[language_tutoring/memory_usage]` - Recall/remember tool usage
- `[language_tutoring/error_pattern_tracking]` - Specific error tracking with context
- `[language_tutoring/session_wrap_up]` - End-of-session summary protocol
- `[language_tutoring/final_notes]` - Core teaching philosophy

**Unique content per tutor** (~100-150 lines):
- IDENTITY (tutor name, personality, background)
- Grammar explanation example (language-specific concept)
- Language-specific teaching approach (e.g., MEXICAN SPANISH SPECIFICS)
- Example interactions (dialogue in target language)
- Cultural topics (region-specific insights)

**Benefits**: Tutors are 64-85% smaller. Shared methodology updates propagate to all tutors automatically. New language profiles focus only on unique content.

Load profiles via:
- CLI: `--profile <name>`
- Environment: `REACHY_MINI_CUSTOM_PROFILE=<name>` in `.env`
- Gradio UI: Select and hot-reload instructions (tools require restart)

## Enhanced Feedback System

The tutors implement a multi-layered feedback approach designed for effective language learning:

### Grammar Explanation Mode
When learners ask "why?", "explain that", or show confusion, tutors:
1. Pause practice entirely
2. Switch to full English explanation mode
3. Provide complete grammar lessons with rules, examples, and memory tricks
4. Have learners practice the concept immediately
5. Store the explanation in memory for future reference

Each tutor includes language-specific examples:
- **French**: Passé composé with être, DR MRS VANDERTRAMP mnemonic
- **Spanish**: Ser vs estar distinction, preterite vs imperfect
- **German**: Akkusativ case changes, "AKK-use" mnemonic for direct objects
- **Italian**: Gender agreement with O/A/I/E ending patterns
- **Portuguese**: Ser vs estar, gerund usage (Brazilian vs European)

### Error Pattern Tracking
Tutors store errors with specific context using the `remember` tool (category: `struggle`):
- **Specificity**: "Confused 'ser' vs 'estar' describing emotions" not just "verb issues"
- **Context**: "Used 'j'ai allé' instead of 'je suis allé' in past tense narrative"
- **Frequency**: "Third time confusing gender of 'table'"

At session start, tutors recall past struggles and incorporate review naturally.

### Session Summaries
When sessions end, tutors provide spoken recaps:
1. Topics/vocabulary covered
2. One highlight (something done well)
3. One area to focus on next time
4. Store summary in memory (category: `progress`)
5. End with encouragement and celebratory dance

## Configuration (.env)

Required:
```
OPENAI_API_KEY=your_key_here
```

Optional:
```
REACHY_MINI_CUSTOM_PROFILE=french_tutor                   # Language profile to load
SUPERMEMORY_API_KEY=your_key_here                         # Persistent memory for tutors
MODEL_NAME=gpt-realtime                                   # Override realtime model
HF_HOME=./cache                                           # Local VLM cache (--local-vision)
HF_TOKEN=your_hf_token                                    # For Hugging Face models/emotions
LOCAL_VISION_MODEL=HuggingFaceTB/SmolVLM2-2.2B-Instruct  # Local vision model path
```

**Persistent Memory**: `SUPERMEMORY_API_KEY` enables cross-session memory via [supermemory.ai](https://supermemory.ai). When configured, tutors remember learner names, skill levels, error patterns, and progress. Powers the `recall` and `remember` tools.

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
| `recall` | Search persistent memory for learner information | `SUPERMEMORY_API_KEY` |
| `remember` | Store observations about learner for future sessions | `SUPERMEMORY_API_KEY` |

## Code Style Conventions

- **Type checking**: Strict mypy enabled (`mypy src/`)
- **Formatting**: Ruff with 119-char line length
- **Docstrings**: Required for all public functions/classes (ruff `D` rules enabled)
- **Import sorting**: `isort` via ruff (local-folder: `reachy_mini_language_tutor`)
- **Quote style**: Double quotes
- **Async patterns**: Use `asyncio` for OpenAI realtime API, threading for robot control

## Development Tips

### Adding Custom Tools
1. Create Python file in `profiles/<profile_name>/` (e.g., `my_tool.py`)
2. Subclass `reachy_mini_language_tutor.tools.core_tools.Tool`
3. Implement `name`, `description`, `parameters`, and `__call__()` method
4. Add tool name to `profiles/<profile_name>/tools.txt`
5. See `profiles/french_tutor/recall.py` and `profiles/french_tutor/remember.py` for examples

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
