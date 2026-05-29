from llm_ops_v1.economics.cost_calculator import PricingModel, estimate_token_cost


def test_estimate_token_cost_without_cached_tokens() -> None:
    pricing = PricingModel(
        provider="demo",
        model="demo-model",
        input_per_1m_usd=2.0,
        output_per_1m_usd=6.0,
        cached_input_per_1m_usd=0.5,
    )

    cost = estimate_token_cost(pricing, input_tokens=1_000, output_tokens=500)

    assert cost.provider == "demo"
    assert cost.model == "demo-model"
    assert cost.input_tokens == 1_000
    assert cost.output_tokens == 500
    assert cost.cached_input_tokens == 0
    assert cost.input_cost_usd == 0.002
    assert cost.cached_input_cost_usd == 0.0
    assert cost.output_cost_usd == 0.003
    assert cost.total_cost_usd == 0.005


def test_estimate_token_cost_with_cached_tokens() -> None:
    pricing = PricingModel(
        provider="demo",
        model="demo-model",
        input_per_1m_usd=2.0,
        output_per_1m_usd=6.0,
        cached_input_per_1m_usd=0.5,
    )

    cost = estimate_token_cost(
        pricing,
        input_tokens=1_000,
        cached_input_tokens=400,
        output_tokens=200,
    )

    assert cost.input_tokens == 1_000
    assert cost.cached_input_tokens == 400
    assert cost.output_tokens == 200
    assert cost.input_cost_usd == 0.0012
    assert cost.cached_input_cost_usd == 0.0002
    assert cost.output_cost_usd == 0.0012
    assert cost.total_cost_usd == 0.0026
