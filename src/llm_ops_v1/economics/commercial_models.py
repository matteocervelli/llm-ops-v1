from llm_ops_v1.economics.cost_calculator import PricingModel

# Pricing points intentionally stay explicit because these values change over time.
# Refresh them before a live demo or when preparing teaching material.
COMMERCIAL_MODELS: dict[str, PricingModel] = {
    "anthropic:claude-sonnet-4-5": PricingModel(
        provider="anthropic",
        model="claude-sonnet-4-5",
        input_per_1m_usd=3.0,
        cached_input_per_1m_usd=0.3,
        output_per_1m_usd=15.0,
    ),
    "openai:gpt-4.1-mini": PricingModel(
        provider="openai",
        model="gpt-4.1-mini",
        input_per_1m_usd=0.4,
        cached_input_per_1m_usd=0.1,
        output_per_1m_usd=1.6,
    ),
    "gemini:gemini-2.5-flash": PricingModel(
        provider="gemini",
        model="gemini-2.5-flash",
        input_per_1m_usd=0.3,
        cached_input_per_1m_usd=0.03,
        output_per_1m_usd=2.5,
    ),
    "openrouter:deepseek-v4-flash": PricingModel(
        provider="openrouter",
        model="deepseek/deepseek-v4-flash",
        input_per_1m_usd=0.14,
        cached_input_per_1m_usd=0.014,
        output_per_1m_usd=0.28,
    ),
}


def get_pricing(model_id: str) -> PricingModel:
    try:
        return COMMERCIAL_MODELS[model_id]
    except KeyError as exc:
        supported = ", ".join(sorted(COMMERCIAL_MODELS))
        raise KeyError(f"Unknown model '{model_id}'. Supported: {supported}") from exc


def list_commercial_models() -> list[str]:
    return sorted(COMMERCIAL_MODELS)
