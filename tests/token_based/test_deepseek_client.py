from unittest.mock import AsyncMock, patch

import pytest

from llm_ops_v1.agents.token_based.deepseek_client import DeepSeekOpenRouterClient


def _make_router_response(content: str, prompt_tokens: int, completion_tokens: int) -> dict:
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


@pytest.fixture()
def mock_router():
    with patch("llm_ops_v1.agents.token_based.deepseek_client.OpenRouterClient") as MockRouter:
        instance = MockRouter.return_value
        instance.chat_completion = AsyncMock()
        yield instance


async def test_complete_returns_result(mock_router):
    mock_router.chat_completion.return_value = _make_router_response("answer", 100, 40)
    client = DeepSeekOpenRouterClient(api_key="test-key")
    result = await client.complete("question")
    assert result.text == "answer"
    assert result.input_tokens == 100
    assert result.output_tokens == 40


async def test_default_model_is_deepseek_v4_flash(mock_router):
    mock_router.chat_completion.return_value = _make_router_response("x", 1, 1)
    client = DeepSeekOpenRouterClient(api_key="test-key")
    await client.complete("q")
    assert mock_router.chat_completion.call_args.kwargs["model"] == "deepseek/deepseek-v4-flash"


async def test_system_message_included(mock_router):
    mock_router.chat_completion.return_value = _make_router_response("x", 1, 1)
    client = DeepSeekOpenRouterClient(api_key="test-key")
    await client.complete("hi", system="Be concise.")
    messages = mock_router.chat_completion.call_args.kwargs["messages"]
    assert messages[0] == {"role": "system", "content": "Be concise."}
    assert messages[1] == {"role": "user", "content": "hi"}


async def test_missing_usage_defaults_to_zero(mock_router):
    mock_router.chat_completion.return_value = {"choices": [{"message": {"content": "text"}}]}
    client = DeepSeekOpenRouterClient(api_key="test-key")
    result = await client.complete("q")
    assert result.input_tokens == 0
    assert result.output_tokens == 0


async def test_custom_model(mock_router):
    mock_router.chat_completion.return_value = _make_router_response("x", 1, 1)
    client = DeepSeekOpenRouterClient(model="deepseek/other-model", api_key="test-key")
    await client.complete("q")
    assert mock_router.chat_completion.call_args.kwargs["model"] == "deepseek/other-model"
