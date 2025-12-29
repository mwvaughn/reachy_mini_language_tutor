---
title: Reachy Language Partner
emoji: 🗣️
colorFrom: red
colorTo: blue
sdk: static
pinned: false
short_description: Practice languages with Reachy Mini!
tags:
 - reachy_mini
 - reachy_mini_python_app
 - language_learning
---

# Reachy Language Partner

A language learning companion for the Reachy Mini robot. Practice conversational skills in French, Spanish, and other languages through natural dialogue with an expressive robot partner. Powered by OpenAI's realtime APIs, vision pipelines, and choreographed motion libraries.

![Reachy Mini Dance](docs/assets/reachy_mini_dance.gif)

## Architecture

The app follows a layered architecture connecting the user, AI services, and robot hardware:

<p align="center">
  <img src="docs/assets/conversation_app_arch.svg" alt="Architecture Diagram" width="600"/>
</p>

## Overview
- **Language learning profiles** for French, Spanish, and a customizable default that adapts to any language.
- **Persistent memory** across sessions - the robot remembers your progress, struggles, and preferences.
- **Proactive engagement** - the robot starts conversations and helps when you're stuck.
- Real-time audio conversation loop powered by the OpenAI realtime API and `fastrtc` for low-latency streaming.
- Layered motion system queues primary moves (dances, emotions, goto poses, breathing) while blending speech-reactive wobble and face-tracking.
- Vision processing uses gpt-realtime by default (when camera tool is used), with optional local vision processing using SmolVLM2 model.

## Installation

> [!IMPORTANT]
> Before using this app, you need to install [Reachy Mini's SDK](https://github.com/pollen-robotics/reachy_mini/).<br>
> Windows support is currently experimental and has not been extensively tested. Use with caution.

### Using uv
You can set up the project quickly using [uv](https://docs.astral.sh/uv/):

```bash
uv venv --python 3.12.1  # Create a virtual environment with Python 3.12.1
source .venv/bin/activate
uv sync
```

> [!NOTE]
> To reproduce the exact dependency set from this repo's `uv.lock`, run `uv sync` with `--locked` (or `--frozen`). This ensures `uv` installs directly from the lockfile without re-resolving or updating any versions.

To include optional dependencies:
```
uv sync --extra reachy_mini_wireless # For wireless Reachy Mini with GStreamer support
uv sync --extra local_vision         # For local PyTorch/Transformers vision
uv sync --extra yolo_vision          # For YOLO-based vision
uv sync --extra mediapipe_vision     # For MediaPipe-based vision
uv sync --extra all_vision           # For all vision features
```

You can combine extras or include dev dependencies:
```
uv sync --extra all_vision --group dev
```

### Using pip

```bash
python -m venv .venv # Create a virtual environment
source .venv/bin/activate
pip install -e .
```

Install optional extras depending on the feature set you need:

```bash
# Wireless Reachy Mini support
pip install -e .[reachy_mini_wireless]

# Vision stacks (choose at least one if you plan to run face tracking)
pip install -e .[local_vision]
pip install -e .[yolo_vision]
pip install -e .[mediapipe_vision]
pip install -e .[all_vision]        # installs every vision extra

# Tooling for development workflows
pip install -e .[dev]
```

Some wheels (e.g. PyTorch) are large and require compatible CUDA or CPU builds—make sure your platform matches the binaries pulled in by each extra.

## Optional dependency groups

| Extra | Purpose | Notes |
|-------|---------|-------|
| `reachy_mini_wireless` | Wireless Reachy Mini with GStreamer support. | Required for wireless versions of Reachy Mini, includes GStreamer dependencies.
| `local_vision` | Run the local VLM (SmolVLM2) through PyTorch/Transformers. | GPU recommended; ensure compatible PyTorch builds for your platform.
| `yolo_vision` | YOLOv8 tracking via `ultralytics` and `supervision`. | CPU friendly; supports the `--head-tracker yolo` option.
| `mediapipe_vision` | Lightweight landmark tracking with MediaPipe. | Works on CPU; enables `--head-tracker mediapipe`.
| `all_vision` | Convenience alias installing every vision extra. | Install when you want the flexibility to experiment with every provider.
| `dev` | Developer tooling (`pytest`, `ruff`). | Add on top of either base or `all_vision` environments.

## Configuration

1. Copy `.env.example` to `.env`.
2. Fill in the required values, notably the OpenAI API key.

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Required. Grants access to the OpenAI realtime endpoint.
| `REACHY_MINI_CUSTOM_PROFILE` | Language profile to use (e.g., `french_tutor`, `spanish_tutor`). Defaults to `default`.
| `SUPERMEMORY_API_KEY` | Optional. Enables persistent memory across sessions for language tutors.
| `MODEL_NAME` | Override the realtime model (defaults to `gpt-realtime`). Used for both conversation and vision (unless `--local-vision` flag is used).
| `HF_HOME` | Cache directory for local Hugging Face downloads (only used with `--local-vision` flag, defaults to `./cache`).
| `HF_TOKEN` | Optional token for Hugging Face models (only used with `--local-vision` flag, falls back to `huggingface-cli login`).
| `LOCAL_VISION_MODEL` | Hugging Face model path for local vision processing (only used with `--local-vision` flag, defaults to `HuggingFaceTB/SmolVLM2-2.2B-Instruct`).

## Running the app

Activate your virtual environment, ensure the Reachy Mini robot (or simulator) is reachable, then launch:

```bash
reachy-mini-conversation-app
```

By default, the app runs in console mode for direct audio interaction. Use the `--gradio` flag to launch a web UI served locally at http://127.0.0.1:7860/ (required when running in simulation mode). With a camera attached, vision is handled by the gpt-realtime model when the camera tool is used. For local vision processing, use the `--local-vision` flag to process frames periodically using the SmolVLM2 model. Additionally, you can enable face tracking via YOLO or MediaPipe pipelines depending on the extras you installed.

### CLI options

| Option | Default | Description |
|--------|---------|-------------|
| `--profile <name>` | `default` | Language profile to use (e.g., `french_tutor`, `spanish_tutor`). |
| `--head-tracker {yolo,mediapipe}` | `None` | Select a face-tracking backend when a camera is available. YOLO is implemented locally, MediaPipe comes from the `reachy_mini_toolbox` package. Requires the matching optional extra. |
| `--no-camera` | `False` | Run without camera capture or face tracking. |
| `--local-vision` | `False` | Use local vision model (SmolVLM2) for periodic image processing instead of gpt-realtime vision. Requires `local_vision` extra to be installed. |
| `--gradio` | `False` | Launch the Gradio web UI. Without this flag, runs in console mode. Required when running in simulation mode. |
| `--debug` | `False` | Enable verbose logging for troubleshooting. |
| `--wireless-version` | `False` | Use GStreamer backend for wireless version of the robot. Requires `reachy_mini_wireless` extra to be installed.


### Examples
- Run on hardware with MediaPipe face tracking:

  ```bash
  reachy-mini-conversation-app --head-tracker mediapipe
  ```

- Run with local vision processing (requires `local_vision` extra):

  ```bash
  reachy-mini-conversation-app --local-vision
  ```

- Run with wireless support (requires `reachy_mini_wireless` extra and daemon started with `--wireless-version`):

  ```bash
  reachy-mini-conversation-app --wireless-version
  ```

- Disable the camera pipeline (audio-only conversation):

  ```bash
  reachy-mini-conversation-app --no-camera
  ```

### Troubleshooting

- Timeout error:
If you get an error like this:
  ```bash
  TimeoutError: Timeout while waiting for connection with the server.
  ```
It probably means that the Reachy Mini's daemon isn't running. Install [Reachy Mini's SDK](https://github.com/pollen-robotics/reachy_mini/) and start the daemon.

## LLM tools exposed to the assistant

| Tool | Action | Dependencies |
|------|--------|--------------|
| `move_head` | Queue a head pose change (left/right/up/down/front). | Core install only. |
| `camera` | Capture the latest camera frame and send it to gpt-realtime for vision analysis. | Requires camera worker; uses gpt-realtime vision by default. |
| `head_tracking` | Enable or disable face-tracking offsets (not facial recognition - only detects and tracks face position). | Camera worker with configured head tracker. |
| `dance` | Queue a dance from `reachy_mini_dances_library`. | Core install only. |
| `stop_dance` | Clear queued dances. | Core install only. |
| `play_emotion` | Play a recorded emotion clip via Hugging Face assets. | Needs `HF_TOKEN` for the recorded emotions dataset. |
| `stop_emotion` | Clear queued emotions. | Core install only. |
| `do_nothing` | Explicitly remain idle. | Core install only. |
| `recall` | Search persistent memory for learner information. | Requires `SUPERMEMORY_API_KEY`. |
| `remember` | Store observations about learner for future sessions. | Requires `SUPERMEMORY_API_KEY`. |

## Language Profiles

The app includes language tutor profiles with proactive engagement and persistent memory:

| Profile | Description |
|---------|-------------|
| `default` | Generic language partner that adapts to any language you want to practice |
| `french_tutor` | Delphine, a French conversation partner with cultural context |
| `spanish_tutor` | Sofia, a Mexican Spanish conversation partner |

Set `REACHY_MINI_CUSTOM_PROFILE=<name>` to load a profile (see `.env.example`). For example:

```bash
reachy-mini-conversation-app --profile french_tutor
```

## Creating Custom Profiles

Create custom profiles with dedicated instructions and enabled tools.

Each profile lives in `src/reachy_mini_conversation_app/profiles/<name>/` and requires:
- `instructions.txt` - The system prompt
- `tools.txt` - List of enabled tools (one per line)

Optional files:
- `proactive.txt` - Set to `true` for proactive greetings
- `language.txt` - ISO language code for transcription (e.g., `es`, `fr`)
- `voice.txt` - Voice name (e.g., `coral`, `sage`)

### Custom instructions
Write plain-text prompts in `instructions.txt`. To reuse shared prompt pieces, add lines like:
```
[identities/basic_info]
[behaviors/silent_robot]
```
Each placeholder pulls the matching file under `src/reachy_mini_conversation_app/prompts/` (nested paths allowed). See `french_tutor` or `spanish_tutor` profiles for reference.

### Enabling tools
List enabled tools in `tools.txt`, one per line; prefix with `#` to comment out. Language tutors typically enable:

```
dance
play_emotion
camera
head_tracking
move_head
recall
remember
do_nothing
```

Tools are resolved first from Python files in the profile folder (custom tools), then from the shared library `src/reachy_mini_conversation_app/tools/`.

### Custom tools
You can implement custom tools specific to your profile by adding Python files in the profile folder.
Custom tools must subclass `reachy_mini_conversation_app.tools.core_tools.Tool`. See `french_tutor/recall.py` and `french_tutor/remember.py` for examples of memory tools.

### Edit personalities from the UI
When running with `--gradio`, open the “Personality” accordion:
- Select among available profiles (folders under `src/reachy_mini_conversation_app/profiles/`) or the built‑in default.
- Click “Apply” to update the current session instructions live.
- Create a new personality by entering a name and instructions text; it stores files under `profiles/<name>/` and copies `tools.txt` from the `default` profile.

Note: The “Personality” panel updates the conversation instructions. Tool sets are loaded at startup from `tools.txt` and are not hot‑reloaded.




## Development workflow
- Install the dev group extras: `uv sync --group dev` or `pip install -e .[dev]`.
- Run formatting and linting: `ruff check .`.
- Execute the test suite: `pytest`.
- When iterating on robot motions, keep the control loop responsive => offload blocking work using the helpers in `tools.py`.

## License
Apache 2.0
