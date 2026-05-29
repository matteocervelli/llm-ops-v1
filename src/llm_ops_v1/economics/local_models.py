from dataclasses import dataclass


@dataclass(frozen=True)
class LocalModelProfile:
    model: str
    runtime: str
    context_window: int
    estimated_hourly_infra_usd: float


LOCAL_MODELS: dict[str, LocalModelProfile] = {
    # ── Ollama — local workstation ─────────────────────────────────────────────
    "ollama:qwen3.6:27b": LocalModelProfile(
        model="qwen3.6:27b",
        runtime="ollama",
        context_window=128_000,
        estimated_hourly_infra_usd=0.40,
    ),
    # MoE: only 3.5B params active per token — faster than the dense 27B
    "ollama:qwen3.6:35b-a3b": LocalModelProfile(
        model="qwen3.6:35b-a3b",
        runtime="ollama",
        context_window=128_000,
        estimated_hourly_infra_usd=0.20,
    ),
    # Qwen3.6 with thinking budget via SYSTEM prompt (Modelfile-derived)
    "ollama:qwen3.6-27b-budget": LocalModelProfile(
        model="qwen3.6-27b-budget",
        runtime="ollama",
        context_window=128_000,
        estimated_hourly_infra_usd=0.40,
    ),
    "ollama:qwen3.6-35b-budget": LocalModelProfile(
        model="qwen3.6-35b-budget",
        runtime="ollama",
        context_window=128_000,
        estimated_hourly_infra_usd=0.20,
    ),
    # MoE, 3.6B active — supports think: low/medium/high
    "ollama:gpt-oss:20b": LocalModelProfile(
        model="gpt-oss:20b",
        runtime="ollama",
        context_window=128_000,
        estimated_hourly_infra_usd=0.18,
    ),
    # MoE, ~4B active
    "ollama:gemma4:31b": LocalModelProfile(
        model="gemma4:31b",
        runtime="ollama",
        context_window=128_000,
        estimated_hourly_infra_usd=0.22,
    ),
    # ── MLX — Studio (Apple Silicon) ──────────────────────────────────────────
    "mlx:gpt-oss-20b": LocalModelProfile(
        model="mlx-community/gpt-oss-20b-MXFP4-Q8",
        runtime="mlx",
        context_window=128_000,
        estimated_hourly_infra_usd=0.20,
    ),
    "mlx:gemma4-31b-4bit": LocalModelProfile(
        model="mlx-community/gemma-4-27b-it-4bit",
        runtime="mlx",
        context_window=128_000,
        estimated_hourly_infra_usd=0.25,
    ),
    # Qwen3.6 MLX — requires mlx-lm with qwen3_5 arch support (pending)
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
