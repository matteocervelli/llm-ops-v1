from dataclasses import dataclass


@dataclass(frozen=True)
class PricingModel:
    provider: str
    model: str
    input_per_1m_usd: float
    output_per_1m_usd: float
    cached_input_per_1m_usd: float | None = None


@dataclass(frozen=True)
class CostBreakdown:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    input_cost_usd: float
    cached_input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float


def _per_token_cost(price_per_1m_usd: float, tokens: int) -> float:
    return round((price_per_1m_usd / 1_000_000) * tokens, 8)


def estimate_token_cost(
    pricing: PricingModel,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
) -> CostBreakdown:
    if min(input_tokens, output_tokens, cached_input_tokens) < 0:
        raise ValueError("Token counts cannot be negative.")

    billable_input_tokens = max(input_tokens - cached_input_tokens, 0)
    input_cost = _per_token_cost(pricing.input_per_1m_usd, billable_input_tokens)
    cached_rate = pricing.cached_input_per_1m_usd or 0.0
    cached_input_cost = _per_token_cost(cached_rate, cached_input_tokens)
    output_cost = _per_token_cost(pricing.output_per_1m_usd, output_tokens)
    total = round(input_cost + cached_input_cost + output_cost, 8)

    return CostBreakdown(
        provider=pricing.provider,
        model=pricing.model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached_input_tokens,
        input_cost_usd=input_cost,
        cached_input_cost_usd=cached_input_cost,
        output_cost_usd=output_cost,
        total_cost_usd=total,
    )
