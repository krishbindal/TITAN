from abc import ABC, abstractmethod

# Shared system prompt used by every provider so assistant identity stays
# consistent regardless of the backend.
SYSTEM_PROMPT = (
    "You are TITAN, an intelligent desktop AI assistant. "
    "Be accurate, concise and helpful."
)


class LLMProvider(ABC):

    @abstractmethod
    def chat(self, prompt: str) -> str:
        """Send a prompt to the LLM and return the response."""
