import os
from dataclasses import dataclass, field

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel

from llm_ops_v1.economics.commercial_models import get_pricing
from llm_ops_v1.economics.cost_calculator import estimate_token_cost

# ---------------------------------------------------------------------------
# Generic production agent (kept for existing tests)
# ---------------------------------------------------------------------------


@dataclass
class AgentDependencies:
    request_id: str = "dev-request"
    user_tier: str = "demo"


production_agent = Agent(
    "openai:gpt-4.1-mini",
    deps_type=AgentDependencies,
    defer_model_check=True,
    instructions=(
        "You are a production-ready assistant. Be concise, explicit about tradeoffs, "
        "and prefer reliable operational behavior over novelty."
    ),
)


@production_agent.tool
def get_request_context(ctx: RunContext[AgentDependencies]) -> dict[str, str]:
    return {
        "request_id": ctx.deps.request_id,
        "user_tier": ctx.deps.user_tier,
    }


@production_agent.tool
def estimate_llm_cost(
    _ctx: RunContext[AgentDependencies],
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> dict[str, float | int | str]:
    try:
        pricing = get_pricing(f"{provider}:{model}")
    except KeyError:
        return {"error": f"unknown model {provider}:{model}", "total_cost_usd": 0.0}
    breakdown = estimate_token_cost(pricing, input_tokens, output_tokens)
    return {
        "provider": breakdown.provider,
        "model": breakdown.model,
        "input_tokens": breakdown.input_tokens,
        "output_tokens": breakdown.output_tokens,
        "total_cost_usd": breakdown.total_cost_usd,
    }


async def run_agent(prompt: str, deps: AgentDependencies | None = None) -> str:
    result = await production_agent.run(prompt, deps=deps or AgentDependencies())
    return result.output


# ---------------------------------------------------------------------------
# Support triage agent — reference scenario for Module 5
# ---------------------------------------------------------------------------

_ZERO_KEY_OUTPUT = (
    "Category: billing_issue. "
    "Reply draft: Thank you for reaching out. We have received your ticket and are "
    "investigating the shipment delay. A tracking update will follow within 2 hours. "
    "Decision: reply. "
    "Estimated cost: $0.0003."
)


@dataclass
class SupportTriageDependencies:
    ticket_id: str = "ticket-demo-001"
    customer_tier: str = "standard"
    ticket_priority: str = "normal"
    policy_snippets: list[str] = field(default_factory=list)


support_triage_agent = Agent(
    "openai:gpt-4.1-mini",
    deps_type=SupportTriageDependencies,
    defer_model_check=True,
    instructions=(
        "You are a support triage agent. Given a customer ticket, you must:\n"
        "1. Categorize the ticket (billing_issue, shipping_delay, technical_problem, other)\n"
        "2. Draft a concise, empathetic reply\n"
        "3. Decide: reply | ask_clarification | escalate\n"
        "4. Estimate the cost impact\n"
        "Always include: Category, Reply draft, Decision, Estimated cost."
    ),
)


@support_triage_agent.tool
def get_ticket_context(ctx: RunContext[SupportTriageDependencies]) -> dict[str, str]:
    return {
        "ticket_id": ctx.deps.ticket_id,
        "customer_tier": ctx.deps.customer_tier,
        "ticket_priority": ctx.deps.ticket_priority,
    }


@support_triage_agent.tool
def get_policy_snippets(ctx: RunContext[SupportTriageDependencies]) -> list[str]:
    return ctx.deps.policy_snippets or [
        "Standard SLA: respond within 4 hours for priority tickets."
    ]


def _has_provider_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))


async def run_support_triage_agent(
    prompt: str,
    deps: SupportTriageDependencies | None = None,
) -> str:
    effective_deps = deps or SupportTriageDependencies()
    if not _has_provider_key():
        with support_triage_agent.override(model=TestModel(custom_output_text=_ZERO_KEY_OUTPUT)):
            result = await support_triage_agent.run(prompt, deps=effective_deps)
    else:
        result = await support_triage_agent.run(prompt, deps=effective_deps)
    return result.output
