"""Dynamic language pair profile generation using OpenAI.

This module generates language tutoring profiles dynamically based on
source language (learner's native language) and target language (language to learn).
Generated profiles are cached to disk to avoid repeated API calls.
"""

import logging
from pathlib import Path
from typing import Optional

from reachy_mini_language_tutor.config import config


logger = logging.getLogger(__name__)

# Cache directory for generated profiles
CACHE_DIR = Path(__file__).parent / "generated_profiles"

# Language metadata with native names and flags
LANGUAGE_DATA = {
    "english": {"native_name": "English", "flag": "🇬🇧", "voice": "shimmer"},
    "chinese": {"native_name": "中文 (Mandarin)", "flag": "🇨🇳", "voice": "coral"},
    "spanish": {"native_name": "Español", "flag": "🇪🇸", "voice": "coral"},
    "french": {"native_name": "Français", "flag": "🇫🇷", "voice": "coral"},
    "german": {"native_name": "Deutsch", "flag": "🇩🇪", "voice": "ash"},
    "italian": {"native_name": "Italiano", "flag": "🇮🇹", "voice": "coral"},
    "portuguese": {"native_name": "Português", "flag": "🇧🇷", "voice": "coral"},
    "japanese": {"native_name": "日本語", "flag": "🇯🇵", "voice": "coral"},
    "korean": {"native_name": "한국어", "flag": "🇰🇷", "voice": "coral"},
    "arabic": {"native_name": "العربية", "flag": "🇸🇦", "voice": "coral"},
    "russian": {"native_name": "Русский", "flag": "🇷🇺", "voice": "coral"},
    "dutch": {"native_name": "Nederlands", "flag": "🇳🇱", "voice": "coral"},
    "hindi": {"native_name": "हिन्दी", "flag": "🇮🇳", "voice": "coral"},
}


def get_supported_languages() -> list[str]:
    """Get list of supported language codes."""
    return list(LANGUAGE_DATA.keys())


def get_language_display_name(lang_code: str) -> str:
    """Get display name for a language code."""
    data = LANGUAGE_DATA.get(lang_code.lower(), {})
    return data.get("native_name", lang_code.title())


def is_language_pair_configured() -> bool:
    """Check if a language pair is configured."""
    return bool(config.SOURCE_LANGUAGE and config.TARGET_LANGUAGE)


def get_dynamic_voice() -> str:
    """Get voice for the target language."""
    if not config.TARGET_LANGUAGE:
        return "coral"
    data = LANGUAGE_DATA.get(config.TARGET_LANGUAGE.lower(), {})
    return data.get("voice", "coral")


def _get_cache_path(source: str, target: str) -> Path:
    """Get cache file path for a language pair."""
    return CACHE_DIR / f"{source}_to_{target}.txt"


def has_cached_profile(source: str, target: str) -> bool:
    """Check if a cached profile exists for the language pair."""
    return _get_cache_path(source, target).exists()


def _load_cached_profile(source: str, target: str) -> Optional[str]:
    """Load cached profile if it exists."""
    cache_path = _get_cache_path(source, target)
    if cache_path.exists():
        try:
            return cache_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to load cached profile: {e}")
    return None


def _save_cached_profile(source: str, target: str, instructions: str) -> None:
    """Save generated profile to cache."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = _get_cache_path(source, target)
        cache_path.write_text(instructions, encoding="utf-8")
        logger.info(f"Cached profile saved: {cache_path}")
    except Exception as e:
        logger.warning(f"Failed to cache profile: {e}")


def _generate_with_openai(source: str, target: str) -> Optional[str]:
    """Generate profile instructions using OpenAI API."""
    if not config.OPENAI_API_KEY:
        logger.error("OpenAI API key not configured")
        return None

    source_data = LANGUAGE_DATA.get(source, {"native_name": source.title()})
    target_data = LANGUAGE_DATA.get(target, {"native_name": target.title()})
    source_name = source_data.get("native_name", source.title())
    target_name = target_data.get("native_name", target.title())

    prompt = f"""Create a language tutor profile for teaching {target_name} to native {source_name} speakers.

The profile should be a system prompt for an AI language tutor robot. Include:

1. IDENTITY: A friendly tutor persona with a name appropriate for the target language
2. LANGUAGE PAIR: Clearly state source ({source_name}) and target ({target_name}) languages
3. PROACTIVE ENGAGEMENT: How to greet learners, check memory for returning users
4. LANGUAGE BEHAVIOR: When to use {source_name} for explanations vs {target_name} for practice
5. ADAPTIVE SUPPORT: How to detect and respond to learner struggles
6. LANGUAGE-SPECIFIC CHALLENGES: Common difficulties {source_name} speakers have learning {target_name}:
   - Pronunciation challenges (sounds that don't exist in {source_name})
   - Grammar differences (structures that work differently)
   - Cultural/communication style differences
7. CORRECTION STYLE: How to gently correct mistakes
8. GRAMMAR EXPLANATION: How to explain grammar in {source_name}
9. ROBOT EXPRESSIVENESS: Use dance, emotions, head movements for engagement
10. MEMORY USAGE: Store learner name, track struggles, celebrate progress

Format as a system prompt with ## headers. Be specific about the linguistic challenges between these two languages.
Include example phrases in both languages where helpful.
The tutor should primarily explain in {source_name} while teaching {target_name} phrases."""

    try:
        import httpx

        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are an expert in language education and cross-linguistic pedagogy."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 4000,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        return None


def generate_dynamic_instructions() -> Optional[str]:
    """Generate dynamic instructions based on source/target language pair.

    First checks for cached profile, then generates with OpenAI if needed.

    Returns:
        Generated instructions string, or None if generation fails.
    """
    source = config.SOURCE_LANGUAGE
    target = config.TARGET_LANGUAGE

    if not source or not target:
        return None

    source = source.lower()
    target = target.lower()

    logger.info(f"Generating profile: {source} → {target}")

    # Check cache first
    cached = _load_cached_profile(source, target)
    if cached:
        logger.info(f"Using cached profile for {source} → {target}")
        return cached

    # Generate with OpenAI
    logger.info(f"Generating new profile with OpenAI for {source} → {target}")
    instructions = _generate_with_openai(source, target)

    if instructions:
        _save_cached_profile(source, target, instructions)
        return instructions

    # Fallback to simple template if OpenAI fails
    logger.warning("Falling back to simple template")
    source_name = LANGUAGE_DATA.get(source, {}).get("native_name", source.title())
    target_name = LANGUAGE_DATA.get(target, {}).get("native_name", target.title())

    return f"""## IDENTITY
You are a friendly {target_name} tutor for {source_name} speakers.

## LANGUAGE PAIR
- Learner's native language: {source_name}
- Language being learned: {target_name}

## APPROACH
- Explain concepts in {source_name}
- Teach {target_name} phrases with translations
- Be patient and encouraging
- Celebrate progress with dances and emotions

## MEMORY
- Remember learner's name
- Track their progress and struggles
"""
