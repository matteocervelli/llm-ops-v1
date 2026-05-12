from dataclasses import dataclass


@dataclass(frozen=True)
class LocalModelProfile:
    model: str
    runtime: str
    context_window: int
    estimated_hourly_infra_usd: float


LOCAL_MODELS: dict[str, LocalModelProfile] = {
    "ollama:qwen3.6:27b": LocalModelProfile(
        model="qwen3.6:27b",
        runtime="ollama",
        context_window=128_000,
        estimated_hourly_infra_usd=0.40,
    ),
    # MoE: only 3B params active per token — faster and cheaper than the dense 27B
    "ollama:qwen3.6:35b-a3b": LocalModelProfile(
        model="qwen3.6:35b-a3b",
        runtime="ollama",
        context_window=128_000,
        estimated_hourly_infra_usd=0.20,
    ),
    "mlx:qwen3.6-27b-4bit": LocalModelProfile(
        model="mlx-community/Qwen3.6-27B-OptiQ-4bit",
        runtime="mlx",
        context_window=128_000,
        estimated_hourly_infra_usd=0.45,
    ),
    "mlx:qwen3.6-35b-a3b-4bit": LocalModelProfile(
        model="mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit",
        runtime="mlx",
        context_window=128_000,
        estimated_hourly_infra_usd=0.22,
    ),
}


def estimate_local_infra_cost(model_id: str, latency_seconds: float) -> float:
    profile = LOCAL_MODELS[model_id]
    return round((latency_seconds / 3600) * profile.estimated_hourly_infra_usd, 8)
