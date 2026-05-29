import pytest

from llm_ops_v1.caching import (
    CacheDelta,
    PromptPrefixCacheEstimate,
    cache_key,
    estimate_cache_savings,
    estimate_support_triage_cache_demo,
)
from llm_ops_v1.economics.commercial_models import get_pricing
from llm_ops_v1.economics.cost_calculator import estimate_token_cost


def test_cache_key_is_stable_for_normalized_whitespace() -> None:
    first = cache_key(
        "You are a support triage agent.",
        ["Standard SLA: respond within 4 hours.", "  Refunds require approval.  "],
    )
    second = cache_key(
        "You are   a support\ntriage agent.",
        ["Standard SLA:  respond within 4 hours.", "\nRefunds require approval."],
    )

    assert first == second
    assert len(first) == 64


def test_cache_key_preserves_policy_order() -> None:
    first = cache_key("system", ["SLA", "Refund policy"])
    second = cache_key("system", ["Refund policy", "SLA"])

    assert first != second


def test_support_triage_cache_key_ignores_ticket_text() -> None:
    first = estimate_support_triage_cache_demo(
        ticket_prompt="A package is delayed.",
        output="Decision: reply. Provide tracking details.",
        policy_snippets=["Standard SLA: respond within 4 hours."],
    )
    second = estimate_support_triage_cache_demo(
        ticket_prompt="A customer reports a billing issue.",
        output="Decision: escalate. Send to billing.",
        policy_snippets=["Standard SLA: respond within 4 hours."],
    )

    assert first.cache_key == second.cache_key


def test_estimate_cache_savings_accepts_float_totals() -> None:
    delta = estimate_cache_savings(uncached_cost=0.0100, cached_cost=0.0040)

    assert isinstance(delta, CacheDelta)
    assert delta.uncached_cost_usd == 0.0100
    assert delta.cached_cost_usd == 0.0040
    assert delta.savings_usd == 0.0060
    assert delta.savings_pct == 60.0


def test_estimate_cache_savings_accepts_cost_breakdowns() -> None:
    pricing = get_pricing("openai:gpt-5.5")
    uncached = estimate_token_cost(pricing, input_tokens=1_000, output_tokens=100)
    cached = estimate_token_cost(
        pricing,
        input_tokens=1_000,
        output_tokens=100,
        cached_input_tokens=800,
    )

    delta = estimate_cache_savings(uncached, cached)

    assert delta.uncached_cost_usd == uncached.total_cost_usd
    assert delta.cached_cost_usd == cached.total_cost_usd
    assert delta.savings_usd > 0.0


@pytest.mark.parametrize(
    ("uncached_cost", "cached_cost"),
    [(-0.1, 0.0), (0.1, -0.1)],
)
def test_estimate_cache_savings_rejects_negative_costs(
    uncached_cost: float,
    cached_cost: float,
) -> None:
    with pytest.raises(ValueError, match="Costs cannot be negative"):
        estimate_cache_savings(uncached_cost, cached_cost)


def test_support_triage_cache_demo_computes_lower_cached_cost() -> None:
    estimate = estimate_support_triage_cache_demo(
        ticket_prompt=(
            "A shipment is delayed. Draft the support reply, mention the tracking update, "
            "and decide whether to escalate."
        ),
        output=(
            "Category: shipping_delay. Reply draft: We are checking the tracking update. "
            "Decision: reply. Estimated cost: low."
        ),
        policy_snippets=[
            "Standard SLA: respond within 4 hours for priority tickets.",
            "Escalate only when the customer reports legal, safety, or repeated billing risk.",
        ],
    )

    assert isinstance(estimate, PromptPrefixCacheEstimate)
    assert estimate.prefix_tokens > 0
    assert estimate.input_tokens >= estimate.prefix_tokens
    assert estimate.output_tokens > 0
    assert estimate.cached_cost.cached_input_tokens == estimate.prefix_tokens
    assert estimate.delta.savings_usd > 0.0
    assert estimate.cached_cost.total_cost_usd < estimate.uncached_cost.total_cost_usd
