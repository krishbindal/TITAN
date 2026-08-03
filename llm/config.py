import os

from dotenv import load_dotenv

load_dotenv()

# DashScope is OpenAI-compatible, so we reuse the `openai` client.
# Docs: https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope
QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

# Valid DashScope model ids include e.g. "qwen-max", "qwen-plus", "qwen-turbo",
# "qwen3-max", "qwen3-235b-a22b".
QWEN_MODEL = "qwen3-max"

QWEN_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# Groq config (https://console.groq.com)
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Ollama is a local server, no API key required.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

SUPPORTED_PROVIDERS = ("qwen", "groq", "ollama")
