from openai import OpenAI

from llm.base import LLMProvider, SYSTEM_PROMPT
from llm.config import OLLAMA_BASE_URL, OLLAMA_MODEL


class OllamaProvider(LLMProvider):

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model
        self._client = None

    @property
    def client(self):
        # Created lazily so this module can be imported without a running
        # local Ollama server.
        if self._client is None:
            self._client = OpenAI(
                api_key="ollama",  # Ollama ignores the key but requires it present
                base_url=self.base_url,
            )
        return self._client

    def chat(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:  # connection refused etc.
            raise ConnectionError(
                f"Could not reach Ollama at {self.base_url}. "
                "Is `ollama serve` running?"
            ) from exc
        return response.choices[0].message.content
