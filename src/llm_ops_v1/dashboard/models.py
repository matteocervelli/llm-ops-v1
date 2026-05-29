from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class DashboardRecord:
    run_id: str
    prompt_preview: str
    output_preview: str
    latency_ms: float
    cost_usd: float
    eval_score: float  # 1-10
    action: str  # reply | ask_clarification | escalate
    cache_hit: bool = False
    source: str = "live"  # scenario | live
    estimated: bool = False  # True when cost/cache figures are heuristic, not measured
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def table_row(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "source": self.source,
            "timestamp": self.timestamp.strftime("%H:%M:%S"),
            "prompt": self.prompt_preview[:60],
            "action": self.action,
            "latency_ms": round(self.latency_ms),
            "cost_usd": f"${self.cost_usd:.4f}",
            "score": self.eval_score,
            "cache_hit": "✓" if self.cache_hit else "–",
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "prompt_preview": self.prompt_preview,
            "output_preview": self.output_preview,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "eval_score": self.eval_score,
            "action": self.action,
            "cache_hit": self.cache_hit,
            "source": self.source,
            "estimated": self.estimated,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DashboardRecord":
        timestamp = payload.get("timestamp")
        parsed_timestamp = (
            datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else datetime.now(UTC)
        )
        return cls(
            run_id=str(payload["run_id"]),
            prompt_preview=str(payload["prompt_preview"]),
            output_preview=str(payload["output_preview"]),
            latency_ms=_float_value(payload["latency_ms"]),
            cost_usd=_float_value(payload["cost_usd"]),
            eval_score=_float_value(payload["eval_score"]),
            action=str(payload["action"]),
            cache_hit=bool(payload.get("cache_hit", False)),
            source=str(payload.get("source", "live")),
            estimated=bool(payload.get("estimated", False)),
            timestamp=parsed_timestamp,
        )


def _float_value(value: Any) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Cannot convert {type(value).__name__} to float")
