"""Gradio tutor selector UI for language learning focus.

This module provides a simplified, language-learning-focused UI with visual
tutor cards instead of the developer-oriented personality management interface.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import gradio as gr

from .config import config

logger = logging.getLogger(__name__)


class TutorSelectorUI:
    """Container for language tutor selection UI components."""

    def __init__(self) -> None:
        """Initialize the TutorSelectorUI instance."""
        # Paths
        self._metadata_path = Path(__file__).parent / "profile_metadata.json"

        # Components (initialized in create_components)
        self.tutor_cards: gr.Dataset
        self.api_key_textbox: gr.Textbox
        self.status_md: gr.Markdown

        # Tutor metadata
        self.tutor_metadata = self._load_metadata()
        self.tutor_profiles = [
            {**data, "id": profile_id}
            for profile_id, data in self.tutor_metadata.items()
        ]

    def _load_metadata(self) -> dict[str, Any]:
        """Load tutor metadata from JSON file.

        Returns:
            Dictionary of tutor profiles with display metadata.
            Falls back to empty dict if file not found.

        """
        try:
            with open(self._metadata_path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load tutor metadata: {e}, using defaults")
            # Fallback: minimal defaults
            return {
                "french_tutor": {
                    "display_name": "French Tutor",
                    "language": "French",
                    "flag_emoji": "🇫🇷",
                    "short_description": "Practice French",
                    "level": "All levels",
                    "accent_color": "#FF6B9D",
                },
                "spanish_tutor": {
                    "display_name": "Spanish Tutor",
                    "language": "Spanish",
                    "flag_emoji": "🇪🇸",
                    "short_description": "Practice Spanish",
                    "level": "All levels",
                    "accent_color": "#FFB347",
                },
                "default": {
                    "display_name": "Language Partner",
                    "language": "Any",
                    "flag_emoji": "🌍",
                    "short_description": "Practice any language",
                    "level": "All levels",
                    "accent_color": "#4ECDC4",
                },
            }

    def _render_tutor_card(self, profile: dict[str, Any]) -> str:
        """Generate HTML for a tutor card.

        Args:
            profile: Dictionary with tutor metadata (display_name, language, etc.)

        Returns:
            HTML string for the tutor card.

        """
        return f"""
        <div class="tutor-card" style="border-left: 4px solid {profile['accent_color']};">
            <div class="tutor-header">
                <span class="tutor-flag">{profile['flag_emoji']}</span>
                <h3 class="tutor-name">{profile['display_name']}</h3>
            </div>
            <p class="tutor-language">{profile['language']}</p>
            <p class="tutor-description">{profile['short_description']}</p>
            <span class="tutor-level">{profile['level']}</span>
        </div>
        """

    def create_components(self) -> None:
        """Instantiate Gradio components for the tutor selector UI."""
        # Tutor selection cards
        self.tutor_cards = gr.Dataset(
            components=[gr.HTML()],
            samples=[[self._render_tutor_card(profile)] for profile in self.tutor_profiles],
            label="Choose Your Language Partner",
            samples_per_page=3,
            type="index",
        )

        # API key configuration
        # Note: Accordion needs to be created within Blocks context, so we'll add it in wire_events
        self.api_key_textbox = gr.Textbox(
            label="OpenAI API Key (Advanced Settings)",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            placeholder="sk-...",
            info="Required for conversation. Your key is stored securely.",
        )

        # Status messages
        self.status_md = gr.Markdown(visible=True)

    def additional_inputs_ordered(self) -> list[Any]:
        """Return the additional inputs in the expected order for Stream.

        Returns:
            List of Gradio components to pass as additional_inputs to Stream.

        """
        return [
            self.api_key_textbox,
            self.tutor_cards,
            self.status_md,
        ]

    def wire_events(
        self,
        handler: Any,
        blocks: gr.Blocks,
    ) -> None:
        """Wire up event handlers for tutor selection.

        Args:
            handler: OpenaiRealtimeHandler instance.
            blocks: Gradio Blocks context (stream.ui).

        """
        # Tutor card selection handler
        async def _on_tutor_selected(evt: gr.SelectData) -> str:
            """Handle tutor card selection and apply personality.

            Args:
                evt: SelectData containing the selected card index.

            Returns:
                Status message string.

            """
            try:
                selected_index = evt.index
                selected_profile = self.tutor_profiles[selected_index]
                profile_id = selected_profile["id"]

                # Convert profile ID to handler format (None for default)
                profile_name = None if profile_id == "default" else profile_id

                # Apply personality
                status_msg = await handler.apply_personality(profile_name)

                return f"✅ {status_msg}"
            except Exception as e:
                logger.error(f"Error applying tutor profile: {e}", exc_info=True)
                return f"❌ Error switching tutor: {e}"

        # Wire the selection event within the Blocks context
        with blocks:
            self.tutor_cards.select(
                fn=_on_tutor_selected,
                inputs=[],
                outputs=[self.status_md],
            )
