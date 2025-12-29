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

Practice conversational skills in French, Spanish, or any language through natural dialogue with an expressive robot companion. Your robot partner remembers your progress across sessions, celebrates your successes with dances and expressions, and helps when you get stuck.

![Reachy Mini Dance](docs/assets/reachy_mini_dance.gif)

## Features

- **Natural conversation practice** - Speak freely and get real-time responses adapted to your level
- **Persistent memory** - The robot remembers your progress, struggles, and preferences across sessions
- **Proactive engagement** - Your robot starts conversations and offers help when you're stuck
- **Gentle correction** - Learn through natural "recasting" without breaking conversation flow
- **Expressive feedback** - Dances and emotions celebrate your progress and keep practice fun

## Language Profiles

| Profile | Description |
|---------|-------------|
| `default` | Generic language partner that adapts to any language |
| `french_tutor` | Delphine, a French conversation partner with cultural context |
| `spanish_tutor` | Sofia, a Mexican Spanish conversation partner |

## Quick Start

### Prerequisites

1. Install [Reachy Mini SDK](https://github.com/pollen-robotics/reachy_mini/)
2. Have an OpenAI API key

### Installation

```bash
git clone https://github.com/pollen-robotics/reachy_mini_conversation_app.git
cd reachy_mini_conversation_app

# Using uv (recommended)
uv venv --python 3.12.1
source .venv/bin/activate
uv sync

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Configuration

Copy `.env.example` to `.env` and add your keys:

```bash
OPENAI_API_KEY=sk-...                    # Required
REACHY_MINI_CUSTOM_PROFILE=french_tutor  # Choose your language
SUPERMEMORY_API_KEY=...                  # Optional, for persistent memory
```

### Start Practicing

```bash
# Practice French
reachy-mini-conversation-app --profile french_tutor

# Practice Spanish
reachy-mini-conversation-app --profile spanish_tutor

# Practice any language (robot will ask what you want to learn)
reachy-mini-conversation-app
```

Add `--gradio` for a web interface with live transcripts at http://127.0.0.1:7860/

## How It Works

1. **Greet** - Your robot greets you in your target language and invites you to practice
2. **Converse** - Speak naturally; the robot adapts to your level automatically
3. **Learn** - Mistakes are gently corrected through natural conversation
4. **Celebrate** - The robot dances and shows emotions when you make progress
5. **Remember** - Your progress is saved for the next session

## Creating New Language Profiles

Want to practice German, Japanese, or another language? Create a new profile:

1. Copy an existing profile folder (e.g., `profiles/french_tutor/`)
2. Rename it (e.g., `profiles/german_tutor/`)
3. Edit `instructions.txt` with language-specific guidance
4. Optionally set `language.txt` to the ISO code (e.g., `de`) for transcription

See `french_tutor` and `spanish_tutor` for examples of well-structured language profiles.

## License

Apache 2.0
