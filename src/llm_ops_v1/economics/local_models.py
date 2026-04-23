from dataclasses import dataclass


@dataclass(frozen=True)
class LocalModelProfile:
    model: str
    runtime: str
    context_window: int
    estimated_hourly_infra_usd: float


LOCAL_MODELS: dict[str, LocalModelProfile] = {
    "ollama:llama3.2": LocalModelProfile(
        model="llama3.2",
        runtime="ollama",
        context_window=128_000,
        estimated_hourly_infra_usd=0.35,
    ),
    "ollama:mistral": LocalModelProfile(
        model="mistral",
        runtime="ollama",
        context_window=32_000,
        estimated_hourly_infra_usd=0.25,
    ),
    "ollama:qwen2.5": LocalModelProfile(
        model="qwen2.5",
        runtime="ollama",
        context_window=128_000,
        estimated_hourly_infra_usd=0.30,
    ),
}


def estimate_local_infra_cost(model_id: str, latency_seconds: float) -> float:
    profile = LOCAL_MODELS[model_id]
    return round((latency_seconds / 3600) * profile.estimated_hourly_infra_usd, 8)
