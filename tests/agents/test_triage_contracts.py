import pytest
from pydantic import ValidationError

from llm_ops_v1.agents.triage_contracts import (
    TicketWebhookRequest,
    TriageBackend,
    build_ticket_prompt,
    enabled_backends,
    parse_triage_output,
)


def test_parse_triage_output_extracts_required_fields() -> None:
    output = (
        "Category: shipping_delay. "
        "Reply draft: We are checking the tracking page. "
        "Decision: reply. "
        "Estimated cost: $0.0001."
    )

    summary = parse_triage_output(output)

    assert summary.category == "shipping_delay"
    assert summary.reply_draft == "We are checking the tracking page."
    assert summary.decision == "reply"


def test_parse_triage_output_falls_back_to_raw_text() -> None:
    summary = parse_triage_output("The customer needs help.")

    assert summary.category == "unknown"
    assert summary.reply_draft == "The customer needs help."
    assert summary.decision == "unknown"


def test_ticket_request_rejects_blank_subject() -> None:
    with pytest.raises(ValidationError):
        TicketWebhookRequest(subject="   ")


def test_build_ticket_prompt_includes_optional_body() -> None:
    request = TicketWebhookRequest(subject="Shipment late", body="Tracking is stuck.")

    assert build_ticket_prompt(request) == "Subject: Shipment late\n\nBody: Tracking is stuck."


def test_enabled_backends_expands_all_in_stable_order() -> None:
    assert enabled_backends(TriageBackend.ALL) == [
        TriageBackend.PYDANTIC_AI,
        TriageBackend.CLAUDE_AGENT_SDK,
        TriageBackend.CODEX_APP_SERVER,
        TriageBackend.LANGGRAPH,
    ]
