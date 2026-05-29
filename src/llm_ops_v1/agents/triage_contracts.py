import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from llm_ops_v1.caching import estimate_support_triage_cache_demo


class TriageBackend(StrEnum):
    PYDANTIC_AI = "pydantic_ai"
    CLAUDE_AGENT_SDK = "claude_agent_sdk"
    CODEX_APP_SERVER = "codex_app_server"
    LANGGRAPH = "langgraph"
    ALL = "all"


class TriageBackendStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class TriageMode(StrEnum):
    LIVE = "live"
    FALLBACK = "fallback"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class TriageSummary:
    category: str
    reply_draft: str
    decision: str


class TicketWebhookRequest(BaseModel):
    subject: Annotated[str, Field(min_length=1, max_length=200)]
    body: Annotated[str | None, Field(max_length=4_000)] = None
    backend: TriageBackend = TriageBackend.PYDANTIC_AI
    ticket_id: Annotated[str, Field(max_length=80)] = "ticket-webhook-001"
    customer_tier: Annotated[str, Field(max_length=40)] = "standard"
    ticket_priority: Annotated[str, Field(max_length=40)] = "normal"

    @field_validator("subject")
    @classmethod
    def subject_must_not_be_blank(cls, value: str) -> str:
        subject = value.strip()
        if not subject:
            raise ValueError("subject cannot be blank")
        return subject

    @field_validator("body")
    @classmethod
    def normalize_body(cls, value: str | None) -> str | None:
        if value is None:
            return None
        body = value.strip()
        return body or None


class TriageBackendResult(BaseModel):
    source: TriageBackend
    status: TriageBackendStatus
    classification: str
    draft_reply: str
    decision: str
    cost_usd: float
    mode: TriageMode
    latency_ms: int
    error: str | None = None


class TicketWebhookResponse(BaseModel):
    request_id: str
    subject: str
    results: list[TriageBackendResult]


def enabled_backends(backend: TriageBackend) -> list[TriageBackend]:
    if backend is TriageBackend.ALL:
        return [
            TriageBackend.PYDANTIC_AI,
            TriageBackend.CLAUDE_AGENT_SDK,
            TriageBackend.CODEX_APP_SERVER,
            TriageBackend.LANGGRAPH,
        ]
    return [backend]


def build_ticket_prompt(request: TicketWebhookRequest) -> str:
    if request.body:
        return f"Subject: {request.subject}\n\nBody: {request.body}"
    return request.subject


def parse_triage_output(output: str) -> TriageSummary:
    fields = _extract_labeled_fields(output)
    category = _clean_short_field(fields.get("category", ""))
    decision = _clean_short_field(fields.get("decision", ""))
    reply_draft = fields.get("reply draft", "").strip()

    if not category and not decision and not reply_draft:
        return TriageSummary(category="unknown", reply_draft=output.strip(), decision="unknown")

    return TriageSummary(
        category=category or "unknown",
        reply_draft=reply_draft or output.strip(),
        decision=decision or "unknown",
    )


def estimate_triage_cost(ticket_text: str, output: str, policy_snippets: list[str]) -> float:
    estimate = estimate_support_triage_cache_demo(
        ticket_prompt=ticket_text,
        output=output,
        policy_snippets=policy_snippets,
    )
    return estimate.uncached_cost.total_cost_usd


def _extract_labeled_fields(output: str) -> dict[str, str]:
    labels = "Category|Reply draft|Decision|Estimated cost"
    pattern = rf"({labels})\s*:\s*(.*?)(?=\s*(?:{labels})\s*:|$)"
    matches = re.finditer(pattern, output, flags=re.IGNORECASE | re.DOTALL)
    return {match.group(1).lower(): match.group(2).strip() for match in matches}


def _clean_short_field(value: str) -> str:
    return value.strip().rstrip(".")
