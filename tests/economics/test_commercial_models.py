import pytest

from llm_ops_v1.economics.commercial_models import get_pricing, list_commercial_models


def test_list_commercial_models_returns_sorted_model_ids() -> None:
    models = list_commercial_models()

    assert models == sorted(models)
    assert "anthropic:claude-sonnet-4-5" in models


def test_get_pricing_returns_expected_model() -> None:
    pricing = get_pricing("openai:gpt-5.5")

    assert pricing.provider == "openai"
    assert pricing.model == "gpt-5.5"
    assert pricing.output_per_1m_usd == 30.0


def test_get_pricing_uses_current_gemini_flash_model() -> None:
    pricing = get_pricing("gemini:gemini-3.5-flash")

    assert pricing.provider == "gemini"
    assert pricing.model == "gemini-3.5-flash"
    assert pricing.input_per_1m_usd == 1.5
    assert pricing.cached_input_per_1m_usd == 0.15
    assert pricing.output_per_1m_usd == 9.0
    assert "gemini:gemini-2.5-flash" not in list_commercial_models()


def test_get_pricing_explains_unknown_model() -> None:
    with pytest.raises(KeyError, match="Supported:"):
        get_pricing("missing:model")
