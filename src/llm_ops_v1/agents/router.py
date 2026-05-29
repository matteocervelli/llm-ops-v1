"""Agent routing — keyword complexity + cost-aware model selection.

decide_form() chooses the cheapest model that meets the complexity requirement.
It estimates the cost for the candidate models and respects the per-request
budget cap (DAILY_SPEND_CAP_USD env var via check_budget).
"""

import argparse
from dataclasses import dataclass

from llm_ops_v1.agents._tokens import estimate_tokens
from llm_ops_v1.economics.commercial_models import get_pricing
from llm_ops_v1.economics.cost_calculator import BudgetExceeded, check_budget, estimate_token_cost
from llm_ops_v1.observability.structured_logging import get_logger

_log = get_logger("llm_ops_v1.router")

HAIKU_MODEL = "anthropic:claude-haiku-4-5"
SONNET_MODEL = "anthropic:claude-sonnet-4-6"
ESCALATION_MODEL = "escalate"

# Rough output multiplier used for cost estimation before the call.
_OUTPUT_RATIO = 0.4

_TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "billing": ("bill", "billing", "charge", "charged", "invoice", "refund", "payment"),
    "shipping": ("delivery", "delivered", "package", "shipping", "shipment", "tracking"),
    "technical": ("app", "bug", "crash", "error", "login", "password", "site", "website"),
    "account": ("account", "access", "locked", "plan", "subscription", "upgrade"),
}
_COMPLEXITY_KEYWORDS = ("also", "enterprise", "escalate", "multiple", "outage", "urgent")
_AMBIGUOUS_KEYWORDS = ("help", "issue", "problem", "question")
_DEMO_TICKETS = [
    "Where is my package? The tracking page has not updated.",
    "Enterprise customer: billing refund and app outage are both blocking launch.",
    "Help.",
]


@dataclass(frozen=True)
class AgentForm:
    model: str
    path: str
    guardrail: str
    confidence: float
    reason: str
    uses_tools: bool
    estimated_cost_usd: float = 0.0


ESCALATION_FORM = AgentForm(ESCALATION_MODEL, "escalate", "human_review", 0.5, "ambiguous", False)


def decide_form(ticket: str, session_total_usd: float = 0.0) -> AgentForm:
    text = ticket.lower().strip()
    topics = _matched_topics(text)
    complex_ticket = len(topics) > 1 or any(kw in text for kw in _COMPLEXITY_KEYWORDS)
    ambiguous = not text or (not topics and _is_ambiguous(text))

    if ambiguous:
        _log.info('{"route":"escalate","reason":"ambiguous"}')
        return ESCALATION_FORM

    input_tokens = estimate_tokens(ticket)
    output_tokens = max(1, int(input_tokens * _OUTPUT_RATIO))

    if complex_ticket:
        cost = _estimate_cost(SONNET_MODEL, input_tokens, output_tokens)
        try:
            check_budget(cost, session_total_usd)
            return AgentForm(
                SONNET_MODEL, "sonnet_with_tools", "tool_use_required", 0.85, "complex", True, cost
            )
        except BudgetExceeded:
            # Budget exceeded for Sonnet — fall back to Haiku.
            cost = _estimate_cost(HAIKU_MODEL, input_tokens, output_tokens)

    cost = _estimate_cost(HAIKU_MODEL, input_tokens, output_tokens)
    return AgentForm(
        HAIKU_MODEL, "haiku_direct", "standard_support_policy", 0.9, "simple", False, cost
    )


def route_trace(form: AgentForm) -> str:
    cost_str = f" est=${form.estimated_cost_usd:.6f}" if form.estimated_cost_usd else ""
    return f"PATH: INPUT -> {form.model} -> OUTPUT -> {form.guardrail}{cost_str}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m llm_ops_v1.agents.router")
    parser.add_argument("--demo", action="store_true", help="Run three support triage examples.")
    args = parser.parse_args(argv)
    if args.demo:
        for ticket in _DEMO_TICKETS:
            print(route_trace(decide_form(ticket)))
    return 0


def _estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    try:
        pricing = get_pricing(model_id)
    except KeyError:
        return 0.0
    return estimate_token_cost(pricing, input_tokens, output_tokens).total_cost_usd


def _matched_topics(text: str) -> set[str]:
    return {topic for topic, kws in _TOPIC_KEYWORDS.items() if any(kw in text for kw in kws)}


def _is_ambiguous(text: str) -> bool:
    words = text.split()
    return len(words) <= 3 or any(kw == text for kw in _AMBIGUOUS_KEYWORDS)


if __name__ == "__main__":
    raise SystemExit(main())
