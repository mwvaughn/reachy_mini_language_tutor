"""Memory manager for the French tutor using SuperMemory.AI."""

from __future__ import annotations
import logging
from typing import Any

from supermemory import AsyncSupermemory


logger = logging.getLogger(__name__)


class TutorMemory:
    """Manages persistent memory for the French tutor using SuperMemory.AI.

    This class provides methods to store and retrieve memories about the learner,
    enabling personalized tutoring sessions that build on previous interactions.
    """

    # Single user mode - hardcoded user ID
    USER_ID = "french_tutor_learner"

    def __init__(self, api_key: str) -> None:
        """Initialize the memory manager with SuperMemory API key.

        Args:
            api_key: SuperMemory.AI API key.

        """
        self.client = AsyncSupermemory(api_key=api_key)
        logger.info("TutorMemory initialized with SuperMemory.AI")

    async def get_context(self, limit: int = 10) -> str:
        """Retrieve relevant memories to inject as session context.

        Args:
            limit: Maximum number of memories to retrieve.

        Returns:
            Formatted string of relevant memories for the system prompt.

        """
        try:
            response = await self.client.search.execute(
                q="French learning progress, preferences, and recent sessions",
            )
            return self._format_context(response.results[:limit] if response.results else [])
        except Exception as e:
            logger.warning("Failed to retrieve memory context: %s", e)
            return ""

    async def store(self, content: str, category: str = "conversation") -> None:
        """Store a memory.

        Args:
            content: The content to store.
            category: Category of the memory (conversation, progress, preference, struggle, success).

        """
        try:
            # Include metadata in the content for searchability
            formatted_content = f"[{category}] [user:{self.USER_ID}] {content}"
            await self.client.memories.add(content=formatted_content)
            logger.debug("Stored memory: %s", content[:50])
        except Exception as e:
            logger.warning("Failed to store memory: %s", e)

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search memories by query.

        Args:
            query: Search query.
            limit: Maximum number of results.

        Returns:
            List of matching memories.

        """
        try:
            response = await self.client.search.execute(q=query)
            results = response.results[:limit] if response.results else []
            return [{"content": r.content if hasattr(r, "content") else str(r)} for r in results]
        except Exception as e:
            logger.warning("Failed to search memories: %s", e)
            return []

    def _format_context(self, results: list[Any]) -> str:
        """Format search results as context for the system prompt.

        Args:
            results: Search results from SuperMemory.

        Returns:
            Formatted context string.

        """
        if not results:
            return ""

        lines = []
        for r in results:
            content = r.content if hasattr(r, "content") else str(r)
            lines.append(f"- {content}")

        return "\n".join(lines)
