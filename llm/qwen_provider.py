from openai import OpenAI

from llm.base import LLMProvider, SYSTEM_PROMPT
from llm.config import (
    QWEN_API_KEY,
    QWEN_BASE_URL,
    QWEN_MODEL,
)


class QwenProvider(LLMProvider):

    def __init__(self, api_key: str | None = None, model: str = QWEN_MODEL):
        self.api_key = api_key or QWEN_API_KEY
        self.model = model
        # Avoid leaking the key in the repr.
        self._client = None

    @property
    def client(self):
        # Created lazily so importing this module never makes network calls
        # or instantiates an OpenAI client when no key is present.
        if self._client is None:
            if not self.api_key:
                raise RuntimeError(
                    "DASHSCOPE_API_KEY is not set. "
                    "Add it to your .env file or environment variables."
                )
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=QWEN_BASE_URL,
            )
        return self._client

    def chat(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
