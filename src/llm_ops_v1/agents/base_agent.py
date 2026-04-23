from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from llm_ops_v1.economics.commercial_models import get_pricing
from llm_ops_v1.economics.cost_calculator import estimate_token_cost


@dataclass
class AgentDependencies:
    request_id: str = "dev-request"
    user_tier: str = "demo"


production_agent = Agent(
    "openai:gpt-4.1-mini",
    deps_type=AgentDependencies,
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
    pricing = get_pricing(f"{provider}:{model}")
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
