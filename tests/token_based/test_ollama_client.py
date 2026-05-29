from unittest.mock import AsyncMock, patch

import pytest
from ollama import ChatResponse, Message

from llm_ops_v1.agents.token_based.ollama_client import OllamaChatClient


def _make_response(
    content: str, prompt_tokens: int | None, output_tokens: int | None
) -> ChatResponse:
    return ChatResponse(
        model="qwen3.6:27b",
        message=Message(role="assistant", content=content),
        prompt_eval_count=prompt_tokens,
        eval_count=output_tokens,
        done=True,
    )


@pytest.fixture()
def mock_ollama_chat():
    with patch("llm_ops_v1.agents.token_based.ollama_client.ollama.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.chat = AsyncMock()
        yield instance


async def test_complete_returns_result(mock_ollama_chat):
    mock_ollama_chat.chat.return_value = _make_response("hello", 10, 5)
    client = OllamaChatClient()
    result = await client.complete("say hello")
    assert result.text == "hello"
    assert result.input_tokens == 10
    assert result.output_tokens == 5


async def test_complete_with_system(mock_ollama_chat):
    mock_ollama_chat.chat.return_value = _make_response("ok", 20, 3)
    client = OllamaChatClient()
    await client.complete("hi", system="You are helpful.")
    call_args = mock_ollama_chat.chat.call_args
    messages = call_args.kwargs["messages"]
    assert messages[0] == {"role": "system", "content": "You are helpful."}
    assert messages[1] == {"role": "user", "content": "hi"}


async def test_complete_without_system_sends_only_user(mock_ollama_chat):
    mock_ollama_chat.chat.return_value = _make_response("ok", 5, 2)
    client = OllamaChatClient()
    await client.complete("question")
    messages = mock_ollama_chat.chat.call_args.kwargs["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"


async def test_none_token_counts_become_zero(mock_ollama_chat):
    mock_ollama_chat.chat.return_value = _make_response("text", None, None)
    client = OllamaChatClient()
    result = await client.complete("q")
    assert result.input_tokens == 0
    assert result.output_tokens == 0


async def test_custom_model(mock_ollama_chat):
    mock_ollama_chat.chat.return_value = _make_response("x", 1, 1)
    client = OllamaChatClient(model="qwen3:30b-a3b")
    await client.complete("q")
    assert mock_ollama_chat.chat.call_args.kwargs["model"] == "qwen3:30b-a3b"


async def test_custom_host_passed_to_client():
    with patch("llm_ops_v1.agents.token_based.ollama_client.ollama.AsyncClient") as MockClient:
        MockClient.return_value.chat = AsyncMock(return_value=_make_response("x", 1, 1))
        OllamaChatClient(host="http://ollama.example.test:11434")
        MockClient.assert_called_once_with(host="http://ollama.example.test:11434")
