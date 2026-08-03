"""Unit tests for the llm package. No network calls are made."""

from unittest.mock import MagicMock, patch

import pytest

from llm.base import LLMProvider
from llm.config import (
    GROQ_BASE_URL,
    GROQ_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    QWEN_BASE_URL,
    QWEN_MODEL,
    SUPPORTED_PROVIDERS,
)
from llm.groq_provider import GroqProvider
from llm.manager import LLMManager, UnsupportedProviderError
from llm.ollama_provider import OllamaProvider
from llm.qwen_provider import QwenProvider


class FakeMessage:
    content = "Hello from the fake LLM."


class FakeChoice:
    message = FakeMessage()


class FakeResponse:
    choices = [FakeChoice()]


def fake_client():
    client = MagicMock()
    client.chat.completions.create.return_value = FakeResponse()
    return client


# --- Config sanity ---------------------------------------------------------

def test_supported_providers_are_expected():
    assert SUPPORTED_PROVIDERS == ("qwen", "groq", "ollama")


def test_qwen_config_defaults():
    assert QWEN_MODEL == "qwen3-max"
    assert QWEN_MODEL != "qwen3.8-max"
    assert "compatible-mode/v1" in QWEN_BASE_URL


def test_groq_config_defaults():
    assert GROQ_MODEL == "llama-3.3-70b-versatile"
    assert "groq.com" in GROQ_BASE_URL


def test_ollama_config_defaults():
    assert "11434" in OLLAMA_BASE_URL
    assert OLLAMA_MODEL == "llama3.2"


# --- QwenProvider ----------------------------------------------------------

@patch("llm.qwen_provider.OpenAI", return_value=fake_client())
def test_qwen_chat_calls_completions(mock_openai):
    provider = QwenProvider(api_key="test-key")
    assert provider.chat("hello") == "Hello from the fake LLM."
    mock_openai.assert_called_once_with(
        api_key="test-key",
        base_url=QWEN_BASE_URL,
    )
    create = mock_openai.return_value.chat.completions.create
    assert create.call_args.kwargs["model"] == "qwen3-max"
    assert create.call_args.kwargs["messages"][0]["role"] == "system"


@patch("llm.qwen_provider.OpenAI")
@patch("llm.qwen_provider.QWEN_API_KEY", None)
def test_qwen_chat_requires_api_key(mock_openai):
    provider = QwenProvider()
    with pytest.raises(RuntimeError, match="DASHSCOPE_API_KEY"):
        provider.chat("hello")
    mock_openai.assert_not_called()


# --- GroqProvider ----------------------------------------------------------

@patch("llm.groq_provider.OpenAI", return_value=fake_client())
def test_groq_chat_uses_groq_endpoint(mock_openai):
    provider = GroqProvider(api_key="test-key")
    assert provider.chat("hi") == "Hello from the fake LLM."
    mock_openai.assert_called_once_with(
        api_key="test-key",
        base_url=GROQ_BASE_URL,
    )


@patch("llm.groq_provider.OpenAI")
def test_groq_chat_requires_api_key(mock_openai):
    provider = GroqProvider(api_key=None)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        provider.chat("hello")
    mock_openai.assert_not_called()


# --- OllamaProvider --------------------------------------------------------

@patch("llm.ollama_provider.OpenAI", return_value=fake_client())
def test_ollama_chat_uses_local_endpoint(mock_openai):
    provider = OllamaProvider()
    assert provider.chat("hi") == "Hello from the fake LLM."
    mock_openai.assert_called_once_with(
        api_key="ollama",
        base_url=OLLAMA_BASE_URL,
    )


@patch("llm.ollama_provider.OpenAI")
def test_ollama_chat_wraps_connection_errors(mock_openai):
    mock_openai.return_value.chat.completions.create.side_effect = ConnectionRefusedError
    provider = OllamaProvider(base_url="http://localhost:1")
    with pytest.raises(ConnectionError, match="ollama serve"):
        provider.chat("hello")


# --- LLMManager ------------------------------------------------------------

def test_manager_defaults_to_qwen():
    manager = LLMManager()
    assert isinstance(manager.provider, QwenProvider)


def test_manager_selects_provider():
    assert isinstance(LLMManager("groq").provider, GroqProvider)
    assert isinstance(LLMManager("ollama").provider, OllamaProvider)


def test_manager_rejects_unknown_provider():
    with pytest.raises(UnsupportedProviderError):
        LLMManager("openai")


@patch.object(QwenProvider, "chat", return_value="mocked")
def test_manager_chat_delegates(mock_chat):
    manager = LLMManager()
    assert manager.chat("hello") == "mocked"
    mock_chat.assert_called_once_with("hello")


# --- Base contract ---------------------------------------------------------

def test_provider_abstract_method_defined():
    assert getattr(LLMProvider, "chat").__isabstractmethod__
