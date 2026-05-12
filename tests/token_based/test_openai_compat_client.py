from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm_ops_v1.agents.token_based.openai_compat_client import OpenAICompatClient


def _make_openai_response(content: str, prompt_tokens: int, completion_tokens: int):
    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens

    message = MagicMock()
    message.content = content

    choice = MagicMock()
    choice.message = message

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


@pytest.fixture()
def mock_create():
    with patch("llm_ops_v1.agents.token_based.openai_compat_client.AsyncOpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        instance.chat = MagicMock()
        instance.chat.completions = MagicMock()
        instance.chat.completions.create = AsyncMock()
        yield instance.chat.completions.create


async def test_complete_returns_result(mock_create):
    mock_create.return_value = _make_openai_response("response text", 15, 8)
    client = OpenAICompatClient(base_url="http://localhost:8080/v1", model="qwen3.6:27b")
    result = await client.complete("prompt")
    assert result.text == "response text"
    assert result.input_tokens == 15
    assert result.output_tokens == 8


async def test_default_api_key_is_dummy():
    with patch("llm_ops_v1.agents.token_based.openai_compat_client.AsyncOpenAI") as MockOpenAI:
        OpenAICompatClient(base_url="http://localhost:8080/v1", model="test-model")
        _, kwargs = MockOpenAI.call_args
        assert kwargs["api_key"] == "no-key-required"


async def test_custom_api_key():
    with patch("llm_ops_v1.agents.token_based.openai_compat_client.AsyncOpenAI") as MockOpenAI:
        OpenAICompatClient(
            base_url="http://localhost:8080/v1", model="test-model", api_key="my-key"
        )
        _, kwargs = MockOpenAI.call_args
        assert kwargs["api_key"] == "my-key"


async def test_base_url_passed_to_client():
    with patch("llm_ops_v1.agents.token_based.openai_compat_client.AsyncOpenAI") as MockOpenAI:
        OpenAICompatClient(base_url="http://studio:8080/v1", model="test-model")
        _, kwargs = MockOpenAI.call_args
        assert kwargs["base_url"] == "http://studio:8080/v1"


async def test_complete_with_system(mock_create):
    mock_create.return_value = _make_openai_response("ok", 5, 2)
    client = OpenAICompatClient(base_url="http://localhost:8080/v1", model="m")
    await client.complete("hi", system="Be brief.")
    messages = mock_create.call_args.kwargs["messages"]
    assert messages[0] == {"role": "system", "content": "Be brief."}
    assert messages[1] == {"role": "user", "content": "hi"}
