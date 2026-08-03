from llm.base import LLMProvider, SYSTEM_PROMPT
from llm.config import (
    QWEN_API_KEY,
    QWEN_BASE_URL,
    QWEN_MODEL,
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from llm.manager import LLMManager, UnsupportedProviderError

__all__ = [
    "LLMProvider",
    "LLMManager",
    "UnsupportedProviderError",
    "SYSTEM_PROMPT",
    "QWEN_API_KEY",
    "QWEN_BASE_URL",
    "QWEN_MODEL",
    "GROQ_API_KEY",
    "GROQ_BASE_URL",
    "GROQ_MODEL",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
]

# Intentionally NO module-level LLMManager instance or chat() call here.
# Instantiating providers / making API calls is the caller's responsibility
# so that `import llm` never blocks on the network or requires a key.
