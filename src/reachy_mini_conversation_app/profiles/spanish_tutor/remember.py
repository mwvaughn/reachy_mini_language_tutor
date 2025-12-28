"""Remember tool for storing learner facts in persistent memory."""

from __future__ import annotations
from typing import Any

from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class RememberTool(Tool):
    """Store important facts about the learner for future sessions."""

    name = "remember"
    description = (
        "Store an important fact about this learner for future sessions. "
        "Use this to record progress, struggles, preferences, or successes "
        "so you can provide personalized tutoring next time."
    )
    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "fact": {
                "type": "string",
                "description": (
                    "The fact to remember, e.g., 'Learner struggles with subjunctive', "
                    "'Prefers topics about Mexican culture', 'Successfully used preterite vs imperfect today'"
                ),
            },
            "category": {
                "type": "string",
                "enum": ["progress", "preference", "struggle", "success"],
                "description": (
                    "Category of the memory: progress (general notes), preference (what they like), "
                    "struggle (what's difficult), success (what they mastered)"
                ),
            },
        },
        "required": ["fact", "category"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> dict[str, Any]:
        """Store a fact in memory.

        Args:
            deps: Tool dependencies including memory_manager.
            **kwargs: Tool arguments including 'fact' and 'category'.

        Returns:
            Dictionary with confirmation or error.

        """
        if not deps.memory_manager:
            return {"error": "Memory not available", "stored": False}

        fact = kwargs.get("fact", "")
        category = kwargs.get("category", "progress")

        if not fact:
            return {"error": "No fact provided", "stored": False}

        await deps.memory_manager.store(fact, category)
        return {"stored": True, "fact": fact, "category": category}
