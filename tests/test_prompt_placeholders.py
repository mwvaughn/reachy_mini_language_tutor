"""Tests for prompt placeholder expansion in language tutor profiles."""

from pathlib import Path

import pytest

from reachy_mini_language_tutor.prompts import (
    PROFILES_DIRECTORY,
    PROMPTS_LIBRARY_DIRECTORY,
    _expand_prompt_includes,
)


class TestPlaceholderExpansion:
    """Test placeholder expansion for shared language tutoring prompts."""

    def test_all_language_tutoring_placeholders_exist(self):
        """Verify all language_tutoring placeholder files exist."""
        expected_placeholders = [
            "language_tutoring/proactive_engagement",
            "language_tutoring/language_behavior",
            "language_tutoring/adaptive_support",
            "language_tutoring/correction_style",
            "language_tutoring/grammar_explanation_structure",
            "language_tutoring/conversation_topics",
            "language_tutoring/robot_expressiveness",
            "language_tutoring/response_guidelines",
            "language_tutoring/vocabulary_teaching",
            "language_tutoring/memory_usage",
            "language_tutoring/error_pattern_tracking",
            "language_tutoring/session_wrap_up",
            "language_tutoring/final_notes",
        ]

        for placeholder in expected_placeholders:
            file_path = PROMPTS_LIBRARY_DIRECTORY / f"{placeholder}.txt"
            assert file_path.exists(), f"Missing shared prompt file: {file_path}"
            assert file_path.stat().st_size > 0, f"Empty shared prompt file: {file_path}"

    def test_placeholder_expansion_works(self):
        """Test that placeholders are expanded correctly."""
        content = "[language_tutoring/proactive_engagement]"
        expanded = _expand_prompt_includes(content)

        assert "[language_tutoring/proactive_engagement]" not in expanded
        assert len(expanded) > len(content)
        assert "## PROACTIVE ENGAGEMENT" in expanded

    def test_multiple_placeholders_expand(self):
        """Test that multiple placeholders on separate lines expand."""
        content = """[language_tutoring/proactive_engagement]

[language_tutoring/language_behavior]"""

        expanded = _expand_prompt_includes(content)

        assert "[language_tutoring/" not in expanded
        assert "## PROACTIVE ENGAGEMENT" in expanded
        assert "## LANGUAGE BEHAVIOR" in expanded

    def test_invalid_placeholder_kept(self):
        """Test that invalid placeholders are kept as-is."""
        content = "[nonexistent_placeholder]"
        expanded = _expand_prompt_includes(content)

        assert "[nonexistent_placeholder]" in expanded

    @pytest.mark.parametrize(
        "tutor",
        [
            "french_tutor",
            "spanish_tutor",
            "german_tutor",
            "italian_tutor",
            "portuguese_tutor",
        ],
    )
    def test_tutor_profile_expands_successfully(self, tutor: str):
        """Test that each tutor profile expands without unexpanded placeholders."""
        instructions_file = PROFILES_DIRECTORY / tutor / "instructions.txt"
        assert instructions_file.exists(), f"Missing instructions file for {tutor}"

        instructions = instructions_file.read_text(encoding="utf-8")
        expanded = _expand_prompt_includes(instructions)

        # Verify no unexpanded language_tutoring placeholders remain
        assert (
            "[language_tutoring/" not in expanded
        ), f"Unexpanded placeholders found in {tutor}"

        # Verify minimum expected length (shared content ~165 lines + unique content)
        assert (
            len(expanded) > 5000
        ), f"Expanded instructions too short for {tutor}: {len(expanded)} chars"

        # Verify key shared sections are present
        assert "## PROACTIVE ENGAGEMENT" in expanded
        assert "## MEMORY USAGE" in expanded
        assert "## SESSION WRAP-UP" in expanded
        assert "## FINAL NOTES" in expanded

    @pytest.mark.parametrize(
        "tutor,expected_identity",
        [
            ("french_tutor", "Delphine"),
            ("spanish_tutor", "Sofia"),
            ("german_tutor", "Lukas"),
            ("italian_tutor", "Chiara"),
            ("portuguese_tutor", "Rafael"),
        ],
    )
    def test_tutor_identity_preserved(self, tutor: str, expected_identity: str):
        """Test that unique tutor identities are preserved after expansion."""
        instructions_file = PROFILES_DIRECTORY / tutor / "instructions.txt"
        instructions = instructions_file.read_text(encoding="utf-8")
        expanded = _expand_prompt_includes(instructions)

        assert expected_identity in expanded, f"Tutor identity '{expected_identity}' missing in {tutor}"

    @pytest.mark.parametrize(
        "tutor,language_specific_section",
        [
            ("spanish_tutor", "MEXICAN SPANISH SPECIFICS"),
            ("german_tutor", "GERMAN-SPECIFIC TEACHING APPROACH"),
            ("italian_tutor", "ITALIAN-SPECIFIC TEACHING APPROACH"),
            ("portuguese_tutor", "BRAZILIAN PORTUGUESE SPECIFICS"),
        ],
    )
    def test_language_specific_sections_preserved(
        self, tutor: str, language_specific_section: str
    ):
        """Test that language-specific teaching sections are preserved."""
        instructions_file = PROFILES_DIRECTORY / tutor / "instructions.txt"
        instructions = instructions_file.read_text(encoding="utf-8")
        expanded = _expand_prompt_includes(instructions)

        assert (
            language_specific_section in expanded
        ), f"Language-specific section '{language_specific_section}' missing in {tutor}"
