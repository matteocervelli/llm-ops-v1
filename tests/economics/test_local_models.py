import pytest

from llm_ops_v1.economics.local_models import LOCAL_MODELS, estimate_local_infra_cost

EXPECTED_KEYS = {
    "ollama:qwen3.6:27b",
    "ollama:qwen3.6:35b-a3b",
    "mlx:qwen3.6-27b-4bit",
    "mlx:qwen3.6-35b-a3b-4bit",
}


def test_all_expected_models_present():
    assert EXPECTED_KEYS == set(LOCAL_MODELS)


def test_all_models_have_valid_fields():
    for key, profile in LOCAL_MODELS.items():
        assert profile.model, f"{key}: model name is empty"
        assert profile.runtime in {"ollama", "mlx"}, f"{key}: unknown runtime"
        assert profile.context_window > 0, f"{key}: context_window must be positive"
        assert profile.estimated_hourly_infra_usd > 0, f"{key}: infra cost must be positive"


def test_moe_model_cheaper_than_dense():
    dense = LOCAL_MODELS["ollama:qwen3.6:27b"]
    moe = LOCAL_MODELS["ollama:qwen3.6:35b-a3b"]
    assert moe.estimated_hourly_infra_usd < dense.estimated_hourly_infra_usd


def test_estimate_local_infra_cost():
    cost = estimate_local_infra_cost("ollama:qwen3.6:27b", latency_seconds=3600)
    assert cost == pytest.approx(0.40, rel=1e-3)


def test_estimate_zero_latency():
    assert estimate_local_infra_cost("ollama:qwen3.6:35b-a3b", latency_seconds=0) == 0.0


def test_estimate_35b_moe():
    cost = estimate_local_infra_cost("ollama:qwen3.6:35b-a3b", latency_seconds=3600)
    assert cost == pytest.approx(0.20, rel=1e-3)


def test_estimate_unknown_model_raises():
    with pytest.raises(KeyError):
        estimate_local_infra_cost("ollama:nonexistent", latency_seconds=1)
