from llm.config import SUPPORTED_PROVIDERS
from llm.base import LLMProvider
from llm.qwen_provider import QwenProvider
from llm.groq_provider import GroqProvider
from llm.ollama_provider import OllamaProvider

PROVIDER_CLASSES = {
    "qwen": QwenProvider,
    "groq": GroqProvider,
    "ollama": OllamaProvider,
}


class UnsupportedProviderError(ValueError):
    pass


class LLMManager:

    def __init__(self, provider: str = "qwen", **kwargs):
        if provider not in SUPPORTED_PROVIDERS:
            raise UnsupportedProviderError(
                f"Unknown LLM provider '{provider}'. "
                f"Supported providers: {', '.join(SUPPORTED_PROVIDERS)}"
            )
        provider_class = PROVIDER_CLASSES[provider]
        self.provider: LLMProvider = provider_class(**kwargs)

    def chat(self, prompt: str) -> str:
        return self.provider.chat(prompt)
