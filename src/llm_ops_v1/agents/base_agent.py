import os
from dataclasses import dataclass, field

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel

from llm_ops_v1.economics.commercial_models import get_pricing
from llm_ops_v1.economics.cost_calculator import estimate_token_cost
from llm_ops_v1.observability.langfuse_setup import observe, push_usage


def wrap_external(content: str) -> str:
    """Tag external content as untrusted so the model treats it adversarially."""
    return f"<UNTRUSTED_EXTERNAL_CONTEXT>\n{content}\n</UNTRUSTED_EXTERNAL_CONTEXT>"


# ---------------------------------------------------------------------------
# Generic production agent (kept for existing tests)
# ---------------------------------------------------------------------------


@dataclass
class AgentDependencies:
    request_id: str = "dev-request"
    user_tier: str = "demo"


production_agent = Agent(
    "openai:gpt-5.5",
    deps_type=AgentDependencies,
    defer_model_check=True,
    instructions=(
        "You are a support triage assistant. Be concise, explicit about tradeoffs, "
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

SUPPORT_TRIAGE_SYSTEM_PROMPT = (
    "You are a support triage agent. Given a customer ticket, you must:\n"
    "1. Categorize the ticket (billing_issue, shipping_delay, technical_problem, other)\n"
    "2. Draft a concise, empathetic reply\n"
    "3. Decide: reply | ask_clarification | escalate\n"
    "4. Estimate the cost impact\n"
    "Always include: Category, Reply draft, Decision, Estimated cost."
)
DEFAULT_SUPPORT_POLICY_SNIPPETS = ["Standard SLA: respond within 4 hours for priority tickets."]

_ZERO_KEY_OUTPUT = (
    "Category: other. "
    "Reply draft: Abbiamo ricevuto la richiesta, ma ci servono alcuni dettagli in piu' "
    "per classificarla correttamente e indicarti il prossimo passo. "
    "Decision: ask_clarification. "
    "Estimated cost: $0.0003."
)


def _zero_key_output_for_prompt(prompt: str, deps: "SupportTriageDependencies") -> str:
    prompt_lower = _normalize_prompt_for_intent(prompt)
    if _is_order_change_or_payment_request(prompt_lower):
        return (
            "Category: billing_issue. "
            "Reply draft: Possiamo verificare la modifica dell'ordine e ricalcolare il totale. "
            "Per procedere ci servono conferma del codice ordine, articolo da aggiungere, "
            "articolo da rimuovere e accettazione del nuovo totale prima della conferma. "
            "Decision: ask_clarification. "
            "Estimated cost: $0.0007."
        )
    if any(term in prompt_lower for term in ["fattura", "fatturazione", "billing", "addebito"]):
        return (
            "Category: billing_issue. "
            "Reply draft: Abbiamo ricevuto la segnalazione sull'addebito e la stiamo "
            "passando al team billing per una verifica puntuale. Ti aggiorneremo appena "
            "confermata la correzione. "
            "Decision: escalate. "
            "Estimated cost: $0.0008."
        )
    if any(term in prompt_lower for term in ["login", "errore", "app", "down", "bloccata"]):
        return (
            "Category: technical_problem. "
            "Reply draft: Ci dispiace per il problema tecnico. Abbiamo aperto una verifica "
            "con il team tecnico e ti chiediamo di inviarci screenshot ed eventuale codice "
            "errore per accelerare la diagnosi. "
            "Decision: escalate. "
            "Estimated cost: $0.0012."
        )
    if any(term in prompt_lower for term in ["reso", "restituire", "rimborso"]):
        return (
            "Category: other. "
            "Reply draft: Possiamo aiutarti con la richiesta di reso, ma ci serve sapere "
            "quale prodotto vuoi restituire e il motivo della richiesta. "
            "Decision: ask_clarification. "
            "Estimated cost: $0.0005."
        )
    if deps.ticket_priority in {"urgent", "high"} and deps.customer_tier == "enterprise":
        return (
            "Category: shipping_delay. "
            "Reply draft: Ci dispiace per il ritardo della spedizione. Per il tuo account "
            "enterprise stiamo verificando subito il tracking con priorita' alta e ti "
            "aggiorneremo entro 1 ora. "
            "Decision: escalate. "
            "Estimated cost: $0.0010."
        )
    return _ZERO_KEY_OUTPUT


def _normalize_prompt_for_intent(prompt: str) -> str:
    lowered = prompt.lower()
    replacements = {
        "'": " ",
        "’": " ",
        ".": " ",
        ",": " ",
        ";": " ",
        ":": " ",
        "-": " ",
        "_": " ",
    }
    for old, new in replacements.items():
        lowered = lowered.replace(old, new)
    return " ".join(lowered.split())


def _is_order_change_or_payment_request(prompt_lower: str) -> bool:
    order_terms = ["ordine", "articolo", "totale", "carrello"]
    change_terms = [
        "modifica",
        "modificare",
        "cambiare",
        "aggiungere",
        "aggiungendo",
        "togliere",
        "togliendone",
        "rimuovere",
        "ricalcolare",
        "ricalcolato",
    ]
    payment_terms = ["pagare", "pagamento", "rate", "dilazione", "piu tempo", "piu' tempo"]
    return (
        any(term in prompt_lower for term in order_terms)
        and any(term in prompt_lower for term in change_terms)
    ) or any(term in prompt_lower for term in payment_terms)


@dataclass
class SupportTriageDependencies:
    ticket_id: str = "ticket-demo-001"
    customer_tier: str = "standard"
    ticket_priority: str = "normal"
    policy_snippets: list[str] = field(default_factory=list)


support_triage_agent = Agent(
    "openai:gpt-5.5",
    deps_type=SupportTriageDependencies,
    defer_model_check=True,
    instructions=SUPPORT_TRIAGE_SYSTEM_PROMPT,
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
    return ctx.deps.policy_snippets or DEFAULT_SUPPORT_POLICY_SNIPPETS


def _has_provider_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))


@dataclass(frozen=True)
class TriageRunResult:
    output: str
    input_tokens: int
    output_tokens: int
    estimated: bool  # True when pydantic-ai ran offline (TestModel)


async def run_support_triage_agent(
    prompt: str,
    deps: SupportTriageDependencies | None = None,
) -> str:
    """Backward-compatible: returns the output string only."""
    return (await run_triage_with_usage(prompt, deps)).output


@observe(name="triage")
async def run_triage_with_usage(
    prompt: str,
    deps: SupportTriageDependencies | None = None,
) -> TriageRunResult:
    """Run triage and return output + real token usage when a provider key is set."""
    effective_deps = deps or SupportTriageDependencies()
    safe_prompt = wrap_external(prompt)
    if not _has_provider_key():
        zero_key_output = _zero_key_output_for_prompt(prompt, effective_deps)
        with support_triage_agent.override(model=TestModel(custom_output_text=zero_key_output)):
            result = await support_triage_agent.run(safe_prompt, deps=effective_deps)
        return TriageRunResult(
            output=result.output,
            input_tokens=0,
            output_tokens=0,
            estimated=True,
        )
    result = await support_triage_agent.run(safe_prompt, deps=effective_deps)
    usage = result.usage
    input_tokens = getattr(usage, "input_tokens", 0) or 0
    output_tokens = getattr(usage, "response_tokens", 0) or getattr(usage, "output_tokens", 0) or 0
    push_usage("anthropic:claude-sonnet-4-6", input_tokens, output_tokens)
    return TriageRunResult(
        output=result.output,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated=False,
    )
