"""Recall tool for searching learner memories."""

from __future__ import annotations
from typing import Any

from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class RecallTool(Tool):
    """Search persistent memory for information about the learner."""

    name = "recall"
    description = (
        "Search your memory for information about this learner from previous sessions. "
        "Use this to check their progress, preferences, or past struggles before giving advice."
    )
    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "What to search for, e.g., 'vocabulary struggles', 'preferred topics', "
                    "'last session progress', 'grammar they find difficult'"
                ),
            },
        },
        "required": ["query"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> dict[str, Any]:
        """Search memories for the given query.

        Args:
            deps: Tool dependencies including memory_manager.
            **kwargs: Tool arguments including 'query'.

        Returns:
            Dictionary with search results or error.

        """
        if not deps.memory_manager:
            return {"error": "Memory not available", "memories": []}

        query = kwargs.get("query", "")
        if not query:
            return {"error": "No query provided", "memories": []}

        results = await deps.memory_manager.search(query)
        return {"memories": results, "count": len(results)}
