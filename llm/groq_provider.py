from openai import OpenAI

from llm.base import LLMProvider, SYSTEM_PROMPT
from llm.config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL,
)


class GroqProvider(LLMProvider):

    def __init__(self, api_key: str | None = None, model: str = GROQ_MODEL):
        self.api_key = api_key or GROQ_API_KEY
        self.model = model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError(
                    "GROQ_API_KEY is not set. "
                    "Add it to your .env file or environment variables."
                )
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=GROQ_BASE_URL,
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
