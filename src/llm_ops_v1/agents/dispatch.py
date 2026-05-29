"""Multi-provider dispatch — route a triage prompt to the right client.

Maps commercial model IDs to their SDK clients, calls complete(), and
returns text + real token usage so the dashboard can compute actual cost.

Supported models (from commercial_models.py):
    anthropic:claude-haiku-4-5
    anthropic:claude-sonnet-4-6
    anthropic:claude-sonnet-4-5
    openai:gpt-5.5
    gemini:gemini-3.5-flash
    openrouter:deepseek-v4-flash
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from llm_ops_v1.agents.base_agent import SUPPORT_TRIAGE_SYSTEM_PROMPT
from llm_ops_v1.agents.token_based import CompletionResult
from llm_ops_v1.economics.commercial_models import get_pricing
from llm_ops_v1.economics.cost_calculator import estimate_token_cost


@dataclass(frozen=True)
class DispatchResult:
    text: str
    model_id: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    estimated: bool  # False when real tokens were counted


def available_models() -> list[str]:
    """Return model IDs that have a key configured in the environment."""
    candidates = [
        ("anthropic:claude-haiku-4-5", "ANTHROPIC_API_KEY"),
        ("anthropic:claude-sonnet-4-6", "ANTHROPIC_API_KEY"),
        ("openai:gpt-5.5", "OPENAI_API_KEY"),
        ("gemini:gemini-3.5-flash", "GEMINI_API_KEY"),
        ("openrouter:deepseek-v4-flash", "OPENROUTER_API_KEY"),
    ]
    return [mid for mid, key in candidates if os.getenv(key)]


async def dispatch(
    prompt: str,
    model_id: str,
    system_prompt: str = SUPPORT_TRIAGE_SYSTEM_PROMPT,
) -> DispatchResult:
    """Call the appropriate client for model_id and return a DispatchResult."""
    try:
        result = await _call_client(prompt, model_id, system_prompt)
        cost = _real_cost(model_id, result.input_tokens, result.output_tokens)
        return DispatchResult(
            text=result.text,
            model_id=model_id,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=cost,
            estimated=False,
        )
    except Exception as exc:
        raise RuntimeError(f"dispatch failed for {model_id}") from exc


async def _call_client(prompt: str, model_id: str, system_prompt: str) -> CompletionResult:
    provider, _, model_name = model_id.partition(":")

    if provider == "anthropic":
        from llm_ops_v1.agents.token_based import AnthropicMessagesClient

        client = AnthropicMessagesClient(model=model_name)
        return await client.complete(prompt, system=system_prompt)

    if provider == "openai":
        from llm_ops_v1.agents.token_based import OpenAIChatClient

        client = OpenAIChatClient(model=model_name)
        return await client.complete(prompt, system=system_prompt)

    if provider == "gemini":
        from llm_ops_v1.agents.token_based import GeminiGenerativeLanguageClient

        client = GeminiGenerativeLanguageClient(model=model_name)
        return await client.complete(prompt, system=system_prompt)

    if provider == "openrouter":
        from llm_ops_v1.agents.token_based import DeepSeekOpenRouterClient

        client = DeepSeekOpenRouterClient()
        return await client.complete(prompt, system=system_prompt)

    raise ValueError(f"Unknown provider '{provider}' in model_id '{model_id}'")


def _real_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    try:
        pricing = get_pricing(model_id)
        return estimate_token_cost(pricing, input_tokens, output_tokens).total_cost_usd
    except KeyError:
        return 0.0
