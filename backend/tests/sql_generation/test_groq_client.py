import pytest

from app.sql_generation.groq_client import (
    GroqClientError,
    GroqLLMClient,
)


def test_missing_api_key(monkeypatch):

    monkeypatch.delenv(
        "GROQ_API_KEY",
        raising=False,
    )

    with pytest.raises(
        GroqClientError
    ) as exc_info:

        GroqLLMClient()

    assert (
        "GROQ_API_KEY"
        in str(exc_info.value)
    )


def test_empty_prompt(monkeypatch):

    monkeypatch.setenv(
        "GROQ_API_KEY",
        "test-key",
    )

    client = GroqLLMClient(
        api_key="test-key"
    )

    with pytest.raises(
        GroqClientError
    ) as exc_info:

        client.generate("   ")

    assert (
        "Prompt cannot be empty"
        in str(exc_info.value)
    )


def test_custom_model(monkeypatch):

    monkeypatch.setenv(
        "GROQ_API_KEY",
        "test-key",
    )

    client = GroqLLMClient(
        api_key="test-key",
        model="openai/gpt-oss-20b",
    )

    assert (
        client.model
        == "openai/gpt-oss-20b"
    )