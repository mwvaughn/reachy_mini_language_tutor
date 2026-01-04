"""Gradio admin interface for Reachy Language Partner.

This module provides a comprehensive settings interface with:
- API key configuration (OpenAI + SuperMemory)
- Language profile selection with hot reload
- Idle behavior settings
- Non-blocking integration with the core bot loop
"""

from __future__ import annotations
import os
import logging
from typing import Any, Callable, Optional
from pathlib import Path

import httpx
import gradio as gr

from reachy_mini_language_tutor.config import config
from reachy_mini_language_tutor.headless_personality import (
    DEFAULT_OPTION,
    list_personalities,
)


logger = logging.getLogger(__name__)


class GradioAdminUI:
    """Container for all admin interface components."""

    def __init__(
        self,
        instance_path: Optional[str] = None,
        on_api_key_change: Optional[Callable[[str], None]] = None,
        on_supermemory_key_change: Optional[Callable[[str], None]] = None,
        on_idle_settings_change: Optional[Callable[[bool, int], None]] = None,
        on_profile_change: Optional[Callable[[Optional[str]], None]] = None,
    ) -> None:
        """Initialize the admin UI.

        Args:
            instance_path: Path to instance directory for .env persistence.
            on_api_key_change: Callback when OpenAI API key changes.
            on_supermemory_key_change: Callback when SuperMemory key changes.
            on_idle_settings_change: Callback when idle settings change (enable, timeout).
            on_profile_change: Callback when profile changes.

        """
        self._instance_path = instance_path
        self._on_api_key_change = on_api_key_change
        self._on_supermemory_key_change = on_supermemory_key_change
        self._on_idle_settings_change = on_idle_settings_change
        self._on_profile_change = on_profile_change

        # Profile metadata
        self._metadata_path = Path(__file__).parent / "profile_metadata.json"
        self.tutor_metadata = self._load_metadata()

        # Components (initialized in create_components)
        # Layout components
        self.title_display: gr.HTML
        self.getting_started_accordion: gr.Accordion
        self.advanced_accordion: gr.Accordion

        # Profile components
        self.profile_dropdown: gr.Dropdown
        self.profile_apply_btn: gr.Button
        self.profile_status: gr.Markdown

        # API Key components
        self.openai_key_input: gr.Textbox
        self.openai_key_status: gr.Markdown
        self.openai_save_btn: gr.Button
        self.supermemory_key_input: gr.Textbox
        self.supermemory_key_status: gr.Markdown
        self.supermemory_save_btn: gr.Button

        # Idle settings components
        self.idle_enable_checkbox: gr.Checkbox
        self.idle_timeout_slider: gr.Slider
        self.idle_save_btn: gr.Button
        self.idle_status: gr.Markdown

    def _load_metadata(self) -> dict[str, Any]:
        """Load tutor metadata from JSON file."""
        import json

        try:
            with open(self._metadata_path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load tutor metadata: {e}, using defaults")
            return {
                "french_tutor": {
                    "display_name": "French Tutor",
                    "flag_emoji": "🇫🇷",
                    "accent_color": "#FF6B9D",
                },
                "spanish_tutor": {
                    "display_name": "Spanish Tutor",
                    "flag_emoji": "🇪🇸",
                    "accent_color": "#FFB347",
                },
                "german_tutor": {
                    "display_name": "German Tutor",
                    "flag_emoji": "🇩🇪",
                    "accent_color": "#7B68EE",
                },
                "italian_tutor": {
                    "display_name": "Italian Tutor",
                    "flag_emoji": "🇮🇹",
                    "accent_color": "#50C878",
                },
                "portuguese_tutor": {
                    "display_name": "Portuguese Tutor",
                    "flag_emoji": "🇧🇷",
                    "accent_color": "#FDB913",
                },
                "default": {
                    "display_name": "Language Partner",
                    "flag_emoji": "🌍",
                    "accent_color": "#4ECDC4",
                },
            }

    def _get_profile_choices(self) -> list[str]:
        """Get list of available profile choices."""
        return [DEFAULT_OPTION, *list_personalities()]

    def _get_current_profile(self) -> str:
        """Get currently active profile."""
        profile = getattr(config, "REACHY_MINI_CUSTOM_PROFILE", None)
        return profile if profile else DEFAULT_OPTION

    def _get_profile_display_name(self, profile_id: str) -> str:
        """Get display name for a profile."""
        if profile_id == DEFAULT_OPTION or not profile_id:
            meta = self.tutor_metadata.get("default", {})
            return f"{meta.get('flag_emoji', '🌍')} {meta.get('display_name', 'Language Partner')}"
        meta = self.tutor_metadata.get(profile_id, {})
        if meta:
            return f"{meta.get('flag_emoji', '')} {meta.get('display_name', profile_id)}"
        return profile_id

    def _render_title(self, profile_id: str) -> str:
        """Generate HTML for the dynamic title showing current tutor."""
        if profile_id == DEFAULT_OPTION or not profile_id:
            meta = self.tutor_metadata.get("default", {})
        else:
            meta = self.tutor_metadata.get(profile_id, {})
        if not meta:
            meta = {"display_name": profile_id, "flag_emoji": "", "accent_color": "#4ECDC4"}
        return f"""
        <h1 style="
            font-family: 'Outfit', system-ui, sans-serif;
            font-size: clamp(1.5rem, 4vw, 2.5rem);
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, {meta.get("accent_color", "#4ECDC4")} 0%, {meta.get("accent_color", "#4ECDC4")}99 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            padding: 8px 0;
            text-align: center;
        ">
            {meta.get("flag_emoji", "🌍")} {meta.get("display_name", "Language Partner")}
        </h1>
        """

    def _read_env_lines(self, env_path: Path) -> list[str]:
        """Load env file contents or a template as a list of lines."""
        inst = env_path.parent
        try:
            if env_path.exists():
                try:
                    return env_path.read_text(encoding="utf-8").splitlines()
                except Exception:
                    return []
            template_text = None
            ex = inst / ".env.example"
            if ex.exists():
                try:
                    template_text = ex.read_text(encoding="utf-8")
                except Exception:
                    template_text = None
            if template_text is None:
                try:
                    cwd_example = Path.cwd() / ".env.example"
                    if cwd_example.exists():
                        template_text = cwd_example.read_text(encoding="utf-8")
                except Exception:
                    template_text = None
            if template_text is None:
                packaged = Path(__file__).parent / ".env.example"
                if packaged.exists():
                    try:
                        template_text = packaged.read_text(encoding="utf-8")
                    except Exception:
                        template_text = None
            return template_text.splitlines() if template_text else []
        except Exception:
            return []

    def _persist_env_value(self, key: str, value: str) -> None:
        """Persist a single key=value to the instance .env file."""
        if not self._instance_path:
            return
        try:
            env_path = Path(self._instance_path) / ".env"
            lines = self._read_env_lines(env_path)
            replaced = False
            for i, ln in enumerate(lines):
                if ln.strip().startswith(f"{key}="):
                    lines[i] = f"{key}={value}"
                    replaced = True
                    break
            if not replaced:
                lines.append(f"{key}={value}")
            final_text = "\n".join(lines) + "\n"
            env_path.write_text(final_text, encoding="utf-8")
            logger.info("Persisted %s to %s", key, env_path)

            try:
                from dotenv import load_dotenv

                load_dotenv(dotenv_path=str(env_path), override=True)
            except Exception:
                pass
        except Exception as e:
            logger.warning("Failed to persist %s: %s", key, e)

    def create_components(self) -> None:
        """Create all admin UI components.

        Components are created without nested containers to ensure Gradio 5.x
        compatibility when created outside a Blocks context.
        """
        # Check current state
        has_openai_key = bool(config.OPENAI_API_KEY and str(config.OPENAI_API_KEY).strip())
        has_supermemory_key = bool(config.SUPERMEMORY_API_KEY and str(config.SUPERMEMORY_API_KEY).strip())
        current_profile = self._get_current_profile()

        # Dynamic title
        self.title_display = gr.HTML(
            value=self._render_title(current_profile),
            label="",
        )

        # Getting Started section (uses only Markdown inside, which works)
        self.getting_started_accordion = gr.Accordion(label="Getting Started", open=not has_openai_key)
        with self.getting_started_accordion:
            gr.Markdown("""### Quick Start Guide

**Step 1: Configure API Key**
Enter your OpenAI API key below (starts with `sk-`). Required for voice conversation.

**Step 2: Choose Your Language**
Select a language tutor from the dropdown. Each tutor specializes in their native language.

**Step 3: Start Talking**
Click the microphone button and start speaking! Your tutor will respond with voice and movement.

**Tips:**
- Speak naturally at a normal pace
- Ask for grammar explanations when unsure
- Request cultural context to deepen understanding""")

        # Language Profile Selector (flat, no accordion - Gradio 5.x compatible)
        self.profile_dropdown = gr.Dropdown(
            label="Select Language Tutor",
            choices=self._get_profile_choices(),
            value=current_profile,
        )
        self.profile_apply_btn = gr.Button("Apply Tutor", variant="primary")
        self.profile_status = gr.Markdown("")

        # API Key inputs (flat, no accordion wrapper)
        self.openai_key_input = gr.Textbox(
            label="OpenAI API Key (Required)",
            type="password",
            placeholder="sk-..." if not has_openai_key else "",
            value="" if not has_openai_key else "••••••••••••••••",
            interactive=not has_openai_key,
            info="Required for voice conversation",
        )
        self.openai_key_status = gr.Markdown(
            "**Status:** Configured ✓" if has_openai_key else "**Status:** Not configured"
        )
        self.openai_save_btn = gr.Button(
            "Change Key" if has_openai_key else "Save & Validate",
            variant="secondary" if has_openai_key else "primary",
        )

        self.supermemory_key_input = gr.Textbox(
            label="SuperMemory API Key (Optional)",
            type="password",
            placeholder="Enter SuperMemory key...",
            value="" if not has_supermemory_key else "••••••••••••••••",
            interactive=not has_supermemory_key,
            info="Enable persistent memory across sessions",
        )
        self.supermemory_key_status = gr.Markdown(
            "**Status:** Configured ✓" if has_supermemory_key else "**Status:** Not configured"
        )
        self.supermemory_save_btn = gr.Button(
            "Change Key" if has_supermemory_key else "Save",
            variant="secondary" if has_supermemory_key else "primary",
        )

        # Advanced Settings (uses only compatible components inside)
        self.advanced_accordion = gr.Accordion(label="Advanced Settings", open=False)
        with self.advanced_accordion:
            gr.Markdown("### Idle Behavior")
            gr.Markdown("*Disabling reduces API costs by 85-90%*")

        # These need to be outside the accordion for Gradio 5.x compatibility
        self.idle_enable_checkbox = gr.Checkbox(
            label="Enable idle animations",
            value=config.ENABLE_IDLE_SIGNALS,
            visible=False,  # Will be shown when accordion is opened via JS
        )
        self.idle_timeout_slider = gr.Slider(
            label="Idle timeout (seconds)",
            minimum=30,
            maximum=900,
            step=30,
            value=config.IDLE_SIGNAL_TIMEOUT,
            visible=False,
        )
        self.idle_save_btn = gr.Button("Save Idle Settings", visible=False)
        self.idle_status = gr.Markdown("")

    def additional_inputs_ordered(self) -> list[Any]:
        """Return components that should be passed to Stream as additional_inputs.

        Returns:
            List of Gradio components.

        """
        return [
            self.title_display,
        ]

    def wire_events(
        self,
        handler: Any,
        blocks: gr.Blocks,
    ) -> None:
        """Wire up event handlers for all admin UI components.

        Args:
            handler: OpenaiRealtimeHandler instance.
            blocks: Gradio Blocks context (stream.ui).

        """
        with blocks:
            # Track key configuration state
            self._openai_configured = bool(config.OPENAI_API_KEY and str(config.OPENAI_API_KEY).strip())
            self._supermemory_configured = bool(config.SUPERMEMORY_API_KEY and str(config.SUPERMEMORY_API_KEY).strip())

            # --- OpenAI API Key Events ---
            async def handle_openai_btn_click(
                current_value: str,
            ) -> tuple[gr.Textbox, gr.Markdown, gr.Button]:
                """Handle OpenAI button click - either validate/save or enable editing."""
                # If currently configured, switch to edit mode
                if self._openai_configured:
                    self._openai_configured = False
                    return (
                        gr.Textbox(value="", placeholder="sk-...", interactive=True),
                        gr.Markdown("**Status:** Enter new key"),
                        gr.Button("Save & Validate", variant="primary"),
                    )

                # Otherwise, validate and save the key
                key = (current_value or "").strip()
                if not key:
                    return (
                        gr.Textbox(interactive=True),
                        gr.Markdown("**Status:** Please enter a key"),
                        gr.Button("Save & Validate", variant="primary"),
                    )

                # Validate key
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        headers = {"Authorization": f"Bearer {key}"}
                        response = await client.get("https://api.openai.com/v1/models", headers=headers)
                        if response.status_code != 200:
                            return (
                                gr.Textbox(interactive=True),
                                gr.Markdown("**Status:** Invalid key ✗"),
                                gr.Button("Save & Validate", variant="primary"),
                            )
                except Exception as e:
                    logger.warning(f"API key validation failed: {e}")
                    return (
                        gr.Textbox(interactive=True),
                        gr.Markdown(f"**Status:** Validation failed - {e}"),
                        gr.Button("Save & Validate", variant="primary"),
                    )

                # Save key
                try:
                    os.environ["OPENAI_API_KEY"] = key
                    config.OPENAI_API_KEY = key
                    self._persist_env_value("OPENAI_API_KEY", key)
                    if self._on_api_key_change:
                        self._on_api_key_change(key)
                    self._openai_configured = True
                except Exception as e:
                    logger.warning(f"Failed to save API key: {e}")
                    return (
                        gr.Textbox(interactive=True),
                        gr.Markdown(f"**Status:** Save failed - {e}"),
                        gr.Button("Save & Validate", variant="primary"),
                    )

                return (
                    gr.Textbox(value="••••••••••••••••", interactive=False),
                    gr.Markdown("**Status:** Configured ✓"),
                    gr.Button("Change Key", variant="secondary"),
                )

            self.openai_save_btn.click(
                fn=handle_openai_btn_click,
                inputs=[self.openai_key_input],
                outputs=[self.openai_key_input, self.openai_key_status, self.openai_save_btn],
            )

            # --- SuperMemory API Key Events ---
            def handle_supermemory_btn_click(
                current_value: str,
            ) -> tuple[gr.Textbox, gr.Markdown, gr.Button]:
                """Handle SuperMemory button click - either save or enable editing."""
                # If currently configured, switch to edit mode
                if self._supermemory_configured:
                    self._supermemory_configured = False
                    return (
                        gr.Textbox(value="", placeholder="Enter SuperMemory key...", interactive=True),
                        gr.Markdown("**Status:** Enter new key"),
                        gr.Button("Save", variant="primary"),
                    )

                # Otherwise, save the key
                key = (current_value or "").strip()
                try:
                    os.environ["SUPERMEMORY_API_KEY"] = key
                    config.SUPERMEMORY_API_KEY = key
                    if key:
                        self._persist_env_value("SUPERMEMORY_API_KEY", key)
                        self._supermemory_configured = True
                    if self._on_supermemory_key_change:
                        self._on_supermemory_key_change(key)
                except Exception as e:
                    logger.warning(f"Failed to save SuperMemory key: {e}")
                    return (
                        gr.Textbox(interactive=True),
                        gr.Markdown(f"**Status:** Failed - {e}"),
                        gr.Button("Save", variant="primary"),
                    )

                if key:
                    return (
                        gr.Textbox(value="••••••••••••••••", interactive=False),
                        gr.Markdown("**Status:** Configured ✓"),
                        gr.Button("Change Key", variant="secondary"),
                    )
                return (
                    gr.Textbox(interactive=True),
                    gr.Markdown("**Status:** Cleared"),
                    gr.Button("Save", variant="primary"),
                )

            self.supermemory_save_btn.click(
                fn=handle_supermemory_btn_click,
                inputs=[self.supermemory_key_input],
                outputs=[self.supermemory_key_input, self.supermemory_key_status, self.supermemory_save_btn],
            )

            # --- Profile Events ---
            async def apply_profile(profile_name: str) -> tuple[str, str]:
                """Apply a language profile immediately."""
                try:
                    # Convert to internal name
                    sel = None if profile_name == DEFAULT_OPTION else profile_name
                    status = await handler.apply_personality(sel)

                    if self._on_profile_change:
                        self._on_profile_change(sel)

                    new_title = self._render_title(profile_name)
                    return new_title, f"Applied: {status}"
                except Exception as e:
                    logger.error(f"Error applying profile: {e}", exc_info=True)
                    return self._render_title(self._get_current_profile()), f"Error: {e}"

            self.profile_apply_btn.click(
                fn=apply_profile,
                inputs=[self.profile_dropdown],
                outputs=[self.title_display, self.profile_status],
            )

            # --- Idle Settings Events ---
            def save_idle_settings(enable: bool, timeout: int) -> str:
                """Save idle behavior settings."""
                try:
                    # Validate timeout
                    if not (30 <= timeout <= 900):
                        return "Error: Timeout must be between 30 and 900 seconds"

                    # Update config
                    config.ENABLE_IDLE_SIGNALS = enable
                    config.IDLE_SIGNAL_TIMEOUT = timeout

                    # Update env
                    os.environ["ENABLE_IDLE_SIGNALS"] = str(enable).lower()
                    os.environ["IDLE_SIGNAL_TIMEOUT"] = str(timeout)

                    # Persist
                    self._persist_env_value("ENABLE_IDLE_SIGNALS", str(enable).lower())
                    self._persist_env_value("IDLE_SIGNAL_TIMEOUT", str(timeout))

                    if self._on_idle_settings_change:
                        self._on_idle_settings_change(enable, timeout)

                    return f"Saved: Idle {'enabled' if enable else 'disabled'}, timeout {timeout}s"
                except Exception as e:
                    logger.warning(f"Failed to save idle settings: {e}")
                    return f"Error: {e}"

            self.idle_save_btn.click(
                fn=save_idle_settings,
                inputs=[self.idle_enable_checkbox, self.idle_timeout_slider],
                outputs=[self.idle_status],
            )
