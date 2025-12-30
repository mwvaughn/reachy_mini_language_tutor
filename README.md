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

Practice conversational skills in French, Spanish, German, Italian, Portuguese, or any language through natural dialogue with an expressive robot companion. Your robot partner remembers your progress across sessions, celebrates your successes with dances and expressions, and helps when you get stuck.

![Reachy Mini Dance](docs/assets/reachy_mini_dance.gif)

## Features

### Core Experience
- **Natural conversation practice** - Speak freely and get real-time responses adapted to your level
- **Persistent memory** - The robot remembers your progress, struggles, and preferences across sessions
- **Proactive engagement** - Your robot starts conversations and offers help when you're stuck
- **Expressive feedback** - Dances and emotions celebrate your progress and keep practice fun

### Enhanced Feedback System
- **Grammar deep-dives** - Ask "why?" anytime and get complete grammar lessons with rules, examples, and memory tricks
- **Error pattern tracking** - Your tutor remembers specific mistakes and proactively reviews them in future sessions
- **Session summaries** - End each session with a spoken recap of topics covered, highlights, and areas to focus on next

## Language Profiles

| Profile | Description |
|---------|-------------|
| `default` | Generic language partner that adapts to any language |
| `french_tutor` | Delphine, a French conversation partner with cultural context |
| `spanish_tutor` | Sofia, a Mexican Spanish conversation partner |
| `german_tutor` | Lukas, a German tutor teaching Standard German (Hochdeutsch) |
| `italian_tutor` | Chiara, an Italian tutor from Florence with cultural insights |
| `portuguese_tutor` | Rafael, a Brazilian Portuguese tutor from São Paulo |

## Quick Start

### Prerequisites

1. Install [Reachy Mini SDK](https://github.com/pollen-robotics/reachy_mini/)
2. Have an OpenAI API key

### Installation

```bash
git clone https://github.com/pollen-robotics/reachy_mini_language_tutor.git
cd reachy_mini_language_tutor

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

**Persistent Memory**: The `SUPERMEMORY_API_KEY` enables your tutor to remember you across sessions—your name, skill level, common mistakes, and learning progress. Get a free API key at [supermemory.ai](https://supermemory.ai).

### Start Practicing

```bash
# Practice French
reachy-mini-language-tutor --profile french_tutor

# Practice Spanish
reachy-mini-language-tutor --profile spanish_tutor

# Practice any language (robot will ask what you want to learn)
reachy-mini-language-tutor
```

Add `--gradio` for a web interface with live transcripts at http://127.0.0.1:7860/

## How It Works

1. **Greet** - Your robot greets you by name (if returning) and reviews any past struggles
2. **Converse** - Speak naturally; the robot adapts to your level automatically
3. **Learn** - Mistakes are gently corrected; ask "why?" for detailed grammar explanations
4. **Celebrate** - The robot dances and shows emotions when you make progress
5. **Review** - End with a session summary highlighting what you learned
6. **Remember** - Your progress, struggles, and breakthroughs are saved for next time

## Creating New Language Profiles

Want to practice Japanese, Mandarin, or another language? Create a new profile:

1. Copy an existing profile folder (e.g., `profiles/french_tutor/`)
2. Rename it (e.g., `profiles/german_tutor/`)
3. Edit `instructions.txt` with language-specific guidance
4. Optionally set `language.txt` to the ISO code (e.g., `de`) for transcription

See `french_tutor` and `spanish_tutor` for examples of well-structured language profiles.

## License

Apache 2.0
