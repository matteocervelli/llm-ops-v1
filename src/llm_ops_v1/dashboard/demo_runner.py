import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from llm_ops_v1.agents._tokens import estimate_tokens
from llm_ops_v1.agents.base_agent import SupportTriageDependencies
from llm_ops_v1.dashboard.models import DashboardRecord
from llm_ops_v1.economics.commercial_models import get_pricing
from llm_ops_v1.economics.cost_calculator import estimate_token_cost
from llm_ops_v1.evals.deterministic import evaluate as _det_evaluate


@dataclass(frozen=True)
class CacheEstimate:
    cache_hit_ratio: float
    total_cost_usd: float
    cached_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class DemoScenario:
    ticket_id: str
    title: str
    ticket_text: str
    deps: SupportTriageDependencies


DEMO_SCENARIOS: tuple[DemoScenario, ...] = (
    DemoScenario(
        ticket_id="scenario-shipping-001",
        title="Spedizione priority in ritardo",
        ticket_text="Il mio ordine e' in ritardo e mi serve un aggiornamento oggi.",
        deps=SupportTriageDependencies(
            ticket_id="scenario-shipping-001",
            customer_tier="priority",
            ticket_priority="high",
            policy_snippets=["SLA priority: inviare un aggiornamento entro 4 ore."],
        ),
    ),
    DemoScenario(
        ticket_id="scenario-billing-001",
        title="Errore di fatturazione",
        ticket_text="Ho ricevuto un doppio addebito in fattura e voglio il rimborso.",
        deps=SupportTriageDependencies(
            ticket_id="scenario-billing-001",
            customer_tier="standard",
            ticket_priority="normal",
            policy_snippets=["Billing disputes: escalare al team billing."],
        ),
    ),
    DemoScenario(
        ticket_id="scenario-return-001",
        title="Richiesta di reso incompleta",
        ticket_text="Vorrei fare un reso ma non so quale procedura seguire.",
        deps=SupportTriageDependencies(
            ticket_id="scenario-return-001",
            customer_tier="standard",
            ticket_priority="low",
            policy_snippets=["Return requests: chiedere prodotto e motivo del reso."],
        ),
    ),
    DemoScenario(
        ticket_id="scenario-outage-001",
        title="Problema tecnico enterprise",
        ticket_text="La nostra app e' bloccata sul login e il team non riesce a lavorare.",
        deps=SupportTriageDependencies(
            ticket_id="scenario-outage-001",
            customer_tier="enterprise",
            ticket_priority="urgent",
            policy_snippets=["Enterprise outages: escalare immediatamente al team tecnico."],
        ),
    ),
)


def estimate_demo_metrics(prompt: str, output: str) -> CacheEstimate:
    total_tokens = max(1, estimate_tokens(prompt) + estimate_tokens(output))
    cached_tokens = int(total_tokens * 0.67)
    pricing = get_pricing("anthropic:claude-sonnet-4-5")
    cost = estimate_token_cost(
        pricing,
        input_tokens=total_tokens,
        output_tokens=int(total_tokens * 0.15),
        cached_input_tokens=cached_tokens,
    )
    return CacheEstimate(
        cache_hit_ratio=round(cached_tokens / total_tokens, 2),
        total_cost_usd=cost.total_cost_usd,
        cached_tokens=cached_tokens,
        total_tokens=total_tokens,
    )


def build_fixture_records() -> list[DashboardRecord]:
    return []


def build_live_record(
    prompt: str,
    output: str,
    latency_ms: float,
    cache_hit: bool = False,
    cost_usd: float | None = None,
    is_estimated: bool = True,
) -> DashboardRecord:
    metrics = estimate_demo_metrics(prompt, output)
    judge = _det_evaluate(prompt, output)
    output_lower = output.lower()
    if "escalate" in output_lower:
        action = "escalate"
    elif "clarif" in output_lower:
        action = "ask_clarification"
    else:
        action = "reply"
    return DashboardRecord(
        run_id=f"live-{uuid.uuid4().hex[:8]}",
        prompt_preview=prompt,
        output_preview=output,
        latency_ms=latency_ms,
        cost_usd=cost_usd if cost_usd is not None else metrics.total_cost_usd,
        eval_score=float(judge.score),
        action=action,
        cache_hit=cache_hit,
        source="live",
        estimated=is_estimated,
        timestamp=datetime.now(UTC),
    )
