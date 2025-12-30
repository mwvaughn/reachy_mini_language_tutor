"""Gradio tutor selector UI for language learning focus.

This module provides a simplified, language-learning-focused UI with visual
tutor cards instead of the developer-oriented personality management interface.
"""

from __future__ import annotations
import os
import json
import logging
from typing import Any
from pathlib import Path

import gradio as gr


logger = logging.getLogger(__name__)


class TutorSelectorUI:
    """Container for language tutor selection UI components."""

    def __init__(self) -> None:
        """Initialize the TutorSelectorUI instance."""
        # Paths
        self._metadata_path = Path(__file__).parent / "profile_metadata.json"

        # Components (initialized in create_components)
        self.title_display: gr.HTML
        self.tutor_cards: gr.Dataset
        self.api_key_textbox: gr.Textbox
        self.status_md: gr.Markdown

        # Tutor metadata
        self.tutor_metadata = self._load_metadata()
        self.tutor_profiles = [
            {**data, "id": profile_id}
            for profile_id, data in self.tutor_metadata.items()
        ]

        # Track current selection (find default profile index)
        self.selected_index = next(
            (i for i, p in enumerate(self.tutor_profiles) if p["id"] == "default"),
            0
        )

    def _load_metadata(self) -> dict[str, Any]:
        """Load tutor metadata from JSON file.

        Returns:
            Dictionary of tutor profiles with display metadata.
            Falls back to empty dict if file not found.

        """
        try:
            with open(self._metadata_path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
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

    def _render_tutor_card(self, profile: dict[str, Any], is_selected: bool = False) -> str:
        """Generate HTML for a tutor card.

        Args:
            profile: Dictionary with tutor metadata (display_name, language, etc.)
            is_selected: Whether this card is currently selected.

        Returns:
            HTML string for the tutor card.

        """
        selected_styles = ""
        checkmark = ""
        if is_selected:
            selected_styles = f"""
                background: linear-gradient(135deg, {profile['accent_color']}10 0%, {profile['accent_color']}20 100%);
                border-left: 6px solid {profile['accent_color']};
                box-shadow: 0 4px 16px {profile['accent_color']}40;
                transform: scale(1.02);
            """
            checkmark = f"""
                <div style="
                    position: absolute;
                    top: 12px;
                    right: 12px;
                    background: {profile['accent_color']};
                    color: white;
                    width: 28px;
                    height: 28px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1rem;
                    font-weight: bold;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                ">✓</div>
            """
        else:
            selected_styles = f"border-left: 4px solid {profile['accent_color']};"

        return f"""
        <div class="tutor-card" style="{selected_styles} position: relative;">
            {checkmark}
            <div class="tutor-header">
                <span class="tutor-flag">{profile['flag_emoji']}</span>
                <h3 class="tutor-name">{profile['display_name']}</h3>
            </div>
            <p class="tutor-language">{profile['language']}</p>
            <p class="tutor-description">{profile['short_description']}</p>
            <span class="tutor-level">{profile['level']}</span>
        </div>
        """

    def _render_title(self, profile: dict[str, Any]) -> str:
        """Generate HTML for the dynamic title showing current tutor.

        Args:
            profile: Dictionary with current tutor metadata.

        Returns:
            HTML string for the title.

        """
        return f"""
        <h1 style="
            font-family: 'Outfit', system-ui, sans-serif;
            font-size: clamp(2rem, 5vw, 3rem);
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, {profile['accent_color']} 0%, {profile['accent_color']}99 50%, {profile['accent_color']}66 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            padding: 16px 0;
            text-align: center;
        ">
            {profile['flag_emoji']} {profile['display_name']}
        </h1>
        """

    def _render_all_cards(self) -> list[list[str]]:
        """Render all tutor cards with current selection state.

        Returns:
            List of card HTML samples for gr.Dataset.

        """
        return [
            [self._render_tutor_card(profile, is_selected=(i == self.selected_index))]
            for i, profile in enumerate(self.tutor_profiles)
        ]

    def create_components(self) -> None:
        """Instantiate Gradio components for the tutor selector UI."""
        # Get current profile
        current_profile = self.tutor_profiles[self.selected_index]

        # Dynamic title showing current tutor
        self.title_display = gr.HTML(
            value=self._render_title(current_profile),
            label="",
        )

        # Tutor selection cards with selection highlighting
        self.tutor_cards = gr.Dataset(
            components=[gr.HTML()],
            samples=self._render_all_cards(),
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
            self.title_display,
            self.tutor_cards,
            self.api_key_textbox,
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
        async def _on_tutor_selected(evt: gr.SelectData) -> tuple[str, gr.Dataset, str]:
            """Handle tutor card selection and apply personality.

            Args:
                evt: SelectData containing the selected card index.

            Returns:
                Tuple of (title_html, updated_cards, status_message).

            """
            try:
                # Update selected index
                self.selected_index = evt.index
                selected_profile = self.tutor_profiles[self.selected_index]
                profile_id = selected_profile["id"]

                # Convert profile ID to handler format (None for default)
                profile_name = None if profile_id == "default" else profile_id

                # Apply personality
                status_msg = await handler.apply_personality(profile_name)

                # Re-render title and cards with new selection
                new_title = self._render_title(selected_profile)
                updated_cards = gr.Dataset(samples=self._render_all_cards())

                return new_title, updated_cards, f"✅ {status_msg}"
            except Exception as e:
                logger.error(f"Error applying tutor profile: {e}", exc_info=True)
                # Keep current state on error
                current_profile = self.tutor_profiles[self.selected_index]
                return self._render_title(current_profile), gr.Dataset(samples=self._render_all_cards()), f"❌ Error switching tutor: {e}"

        # Wire the selection event within the Blocks context
        with blocks:
            self.tutor_cards.select(
                fn=_on_tutor_selected,
                inputs=[],
                outputs=[self.title_display, self.tutor_cards, self.status_md],
            )
