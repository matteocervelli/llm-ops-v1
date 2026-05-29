import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass

from llm_ops_v1.agents._tokens import estimate_tokens
from llm_ops_v1.agents.base_agent import (
    DEFAULT_SUPPORT_POLICY_SNIPPETS,
    SUPPORT_TRIAGE_SYSTEM_PROMPT,
)
from llm_ops_v1.economics.commercial_models import get_pricing
from llm_ops_v1.economics.cost_calculator import CostBreakdown, estimate_token_cost

CostInput = float | CostBreakdown


@dataclass(frozen=True)
class CacheDelta:
    uncached_cost_usd: float
    cached_cost_usd: float
    savings_usd: float
    savings_pct: float


@dataclass(frozen=True)
class PromptPrefixCacheEstimate:
    cache_key: str
    model_id: str
    prefix_tokens: int
    input_tokens: int
    output_tokens: int
    uncached_cost: CostBreakdown
    cached_cost: CostBreakdown
    delta: CacheDelta


def cache_key(system_prompt: str, policy_snippets: Sequence[str]) -> str:
    payload = {
        "system_prompt": _normalize_text(system_prompt),
        "policy_snippets": _normalize_policy_snippets(policy_snippets),
    }
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def estimate_cache_savings(
    uncached_cost: CostInput,
    cached_cost: CostInput,
) -> CacheDelta:
    uncached_total = _total_cost(uncached_cost)
    cached_total = _total_cost(cached_cost)
    if uncached_total < 0 or cached_total < 0:
        raise ValueError("Costs cannot be negative.")

    savings_usd = round(uncached_total - cached_total, 8)
    savings_pct = 0.0
    if uncached_total > 0:
        savings_pct = round((savings_usd / uncached_total) * 100, 2)

    return CacheDelta(
        uncached_cost_usd=uncached_total,
        cached_cost_usd=cached_total,
        savings_usd=savings_usd,
        savings_pct=savings_pct,
    )


def estimate_support_triage_cache_demo(
    ticket_prompt: str,
    output: str,
    policy_snippets: Sequence[str] | None = None,
    model_id: str = "openai:gpt-5.5",
) -> PromptPrefixCacheEstimate:
    effective_policies = list(policy_snippets or DEFAULT_SUPPORT_POLICY_SNIPPETS)
    prefix_text = _prompt_prefix_text(SUPPORT_TRIAGE_SYSTEM_PROMPT, effective_policies)
    prefix_tokens = estimate_tokens(prefix_text)
    ticket_tokens = estimate_tokens(ticket_prompt)
    output_tokens = estimate_tokens(output)
    input_tokens = prefix_tokens + ticket_tokens
    pricing = get_pricing(model_id)
    uncached = estimate_token_cost(pricing, input_tokens, output_tokens)
    cached = estimate_token_cost(
        pricing,
        input_tokens,
        output_tokens,
        cached_input_tokens=prefix_tokens,
    )
    return PromptPrefixCacheEstimate(
        cache_key=cache_key(SUPPORT_TRIAGE_SYSTEM_PROMPT, effective_policies),
        model_id=model_id,
        prefix_tokens=prefix_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        uncached_cost=uncached,
        cached_cost=cached,
        delta=estimate_cache_savings(uncached, cached),
    )


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _normalize_policy_snippets(policy_snippets: Sequence[str]) -> list[str]:
    return [normalized for snippet in policy_snippets if (normalized := _normalize_text(snippet))]


def _prompt_prefix_text(system_prompt: str, policy_snippets: Sequence[str]) -> str:
    normalized_policies = _normalize_policy_snippets(policy_snippets)
    return "\n".join([_normalize_text(system_prompt), *normalized_policies])


def _total_cost(cost: CostInput) -> float:
    if isinstance(cost, CostBreakdown):
        return cost.total_cost_usd
    return float(cost)
