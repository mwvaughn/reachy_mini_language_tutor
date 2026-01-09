import os
import logging

from dotenv import find_dotenv, load_dotenv


logger = logging.getLogger(__name__)

# Locate .env file (search upward from current working directory)
dotenv_path = find_dotenv(usecwd=True)

if dotenv_path:
    # Load .env and override environment variables
    load_dotenv(dotenv_path=dotenv_path, override=True)
    logger.info(f"Configuration loaded from {dotenv_path}")
else:
    logger.warning("No .env file found, using environment variables")


class Config:
    """Configuration class for Reachy Language Partner."""

    # Required
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # The key is downloaded in console.py if needed

    # Optional
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-realtime")
    HF_HOME = os.getenv("HF_HOME", "./cache")
    LOCAL_VISION_MODEL = os.getenv("LOCAL_VISION_MODEL", "HuggingFaceTB/SmolVLM2-2.2B-Instruct")
    HF_TOKEN = os.getenv("HF_TOKEN")  # Optional, falls back to hf auth login if not set

    # Memory (SuperMemory.AI)
    SUPERMEMORY_API_KEY = os.getenv("SUPERMEMORY_API_KEY")

    logger.debug(f"Model: {MODEL_NAME}, HF_HOME: {HF_HOME}, Vision Model: {LOCAL_VISION_MODEL}")

    REACHY_MINI_CUSTOM_PROFILE = os.getenv("REACHY_MINI_CUSTOM_PROFILE")
    logger.debug(f"Custom Profile: {REACHY_MINI_CUSTOM_PROFILE}")

    # Language pair configuration (for dynamic language selection)
    SOURCE_LANGUAGE = os.getenv("REACHY_SOURCE_LANGUAGE")  # Learner's native language
    TARGET_LANGUAGE = os.getenv("REACHY_TARGET_LANGUAGE")  # Language to learn

    # Idle signal configuration (cost optimization)
    ENABLE_IDLE_SIGNALS = os.getenv("ENABLE_IDLE_SIGNALS", "true").lower() == "true"
    IDLE_SIGNAL_TIMEOUT = int(os.getenv("IDLE_SIGNAL_TIMEOUT", "300"))  # Default 5 minutes


config = Config()


def set_custom_profile(profile: str | None) -> None:
    """Update the selected custom profile at runtime and expose it via env.

    This ensures modules that read `config` and code that inspects the
    environment see a consistent value.
    """
    try:
        config.REACHY_MINI_CUSTOM_PROFILE = profile
    except Exception:
        pass
    try:
        import os as _os

        if profile:
            _os.environ["REACHY_MINI_CUSTOM_PROFILE"] = profile
        else:
            # Remove to reflect default
            _os.environ.pop("REACHY_MINI_CUSTOM_PROFILE", None)
    except Exception:
        pass


def set_language_pair(source_language: str | None, target_language: str | None) -> None:
    """Update the source and target language pair at runtime.

    Args:
        source_language: The learner's native language (e.g., "chinese", "spanish")
        target_language: The language being learned (e.g., "english", "french")
    """
    try:
        config.SOURCE_LANGUAGE = source_language
        config.TARGET_LANGUAGE = target_language
    except Exception as e:
        logger.warning(f"Failed to update config for language pair: {e}")
    try:
        import os as _os

        if source_language:
            _os.environ["REACHY_SOURCE_LANGUAGE"] = source_language
        else:
            _os.environ.pop("REACHY_SOURCE_LANGUAGE", None)

        if target_language:
            _os.environ["REACHY_TARGET_LANGUAGE"] = target_language
        else:
            _os.environ.pop("REACHY_TARGET_LANGUAGE", None)
    except Exception as e:
        logger.warning(f"Failed to update env vars for language pair: {e}")
