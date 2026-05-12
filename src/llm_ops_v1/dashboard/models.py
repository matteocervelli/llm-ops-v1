from dataclasses import dataclass, field
from datetime import datetime, timezone


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
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def table_row(self) -> dict:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.strftime("%H:%M:%S"),
            "prompt": self.prompt_preview[:60],
            "action": self.action,
            "latency_ms": round(self.latency_ms),
            "cost_usd": f"${self.cost_usd:.4f}",
            "score": self.eval_score,
            "cache_hit": "✓" if self.cache_hit else "–",
        }
