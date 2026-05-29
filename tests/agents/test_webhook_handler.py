from fastapi.testclient import TestClient

from llm_ops_v1.agents import webhook_handler
from llm_ops_v1.agents.base_agent import SupportTriageDependencies
from llm_ops_v1.agents.triage_contracts import TriageBackendStatus


def test_webhook_ticket_uses_pydantic_ai_by_default(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_OPS_WEBHOOK_TOKEN", raising=False)
    monkeypatch.setenv("LLM_OPS_ALLOW_UNAUTHENTICATED_LOCAL", "true")

    async def fake_run_support_triage_agent(prompt, deps) -> str:
        assert prompt == "Shipment late"
        assert deps.ticket_id == "ticket-webhook-001"
        return "Category: shipping_delay. Reply draft: Checking tracking. Decision: reply."

    monkeypatch.setattr(
        webhook_handler,
        "run_support_triage_agent",
        fake_run_support_triage_agent,
    )

    response = TestClient(webhook_handler.app).post(
        "/webhook/ticket",
        json={"subject": "Shipment late"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["subject"] == "Shipment late"
    assert payload["results"][0]["source"] == "pydantic_ai"
    assert payload["results"][0]["classification"] == "shipping_delay"
    assert payload["results"][0]["mode"] == "fallback"


def test_webhook_ticket_can_run_all_backends_with_partial_unavailable(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_OPS_CODEX_APP_SERVER_ENABLED", raising=False)
    monkeypatch.delenv("LLM_OPS_WEBHOOK_TOKEN", raising=False)
    monkeypatch.setenv("LLM_OPS_ALLOW_UNAUTHENTICATED_LOCAL", "true")

    async def fake_run_support_triage_agent(prompt, deps) -> str:
        return "Category: other. Reply draft: We are checking it. Decision: ask_clarification."

    monkeypatch.setattr(
        webhook_handler,
        "run_support_triage_agent",
        fake_run_support_triage_agent,
    )

    response = TestClient(webhook_handler.app).post(
        "/webhook/ticket",
        json={"subject": "Need help", "backend": "all"},
    )

    results = response.json()["results"]
    assert response.status_code == 200
    assert [result["source"] for result in results] == [
        "pydantic_ai",
        "claude_agent_sdk",
        "codex_app_server",
        "langgraph",
    ]
    assert results[0]["status"] == TriageBackendStatus.OK
    assert results[1]["status"] == TriageBackendStatus.UNAVAILABLE
    assert results[2]["status"] == TriageBackendStatus.UNAVAILABLE
    assert results[3]["status"] == TriageBackendStatus.OK


def test_webhook_ticket_requires_configured_token(monkeypatch) -> None:
    monkeypatch.setenv("LLM_OPS_WEBHOOK_TOKEN", "example-webhook-token")

    response = TestClient(webhook_handler.app).post(
        "/webhook/ticket",
        json={"subject": "Shipment late"},
    )

    assert response.status_code == 401


def test_webhook_ticket_requires_auth_by_default(monkeypatch) -> None:
    monkeypatch.delenv("LLM_OPS_WEBHOOK_TOKEN", raising=False)
    monkeypatch.delenv("LLM_OPS_ALLOW_UNAUTHENTICATED_LOCAL", raising=False)

    response = TestClient(webhook_handler.app).post(
        "/webhook/ticket",
        json={"subject": "Shipment late"},
    )

    assert response.status_code == 401


def test_webhook_ticket_accepts_configured_token(monkeypatch) -> None:
    monkeypatch.setenv("LLM_OPS_WEBHOOK_TOKEN", "example-webhook-token")

    async def fake_run_support_triage_agent(prompt, deps) -> str:
        return "Category: other. Reply draft: Done. Decision: reply."

    monkeypatch.setattr(
        webhook_handler,
        "run_support_triage_agent",
        fake_run_support_triage_agent,
    )

    response = TestClient(webhook_handler.app).post(
        "/webhook/ticket",
        headers={"Authorization": "Bearer example-webhook-token"},
        json={"subject": "Shipment late"},
    )

    assert response.status_code == 200


def test_async_result_requires_auth_by_default(monkeypatch) -> None:
    monkeypatch.delenv("LLM_OPS_WEBHOOK_TOKEN", raising=False)
    monkeypatch.delenv("LLM_OPS_ALLOW_UNAUTHENTICATED_LOCAL", raising=False)

    response = TestClient(webhook_handler.app).get(
        "/webhook/ticket/0123456789abcdef",
    )

    assert response.status_code == 401


def test_async_result_rejects_invalid_request_id(monkeypatch) -> None:
    monkeypatch.setenv("LLM_OPS_WEBHOOK_TOKEN", "example-webhook-token")

    response = TestClient(webhook_handler.app).get(
        "/webhook/ticket/not-a-hex-id",
        headers={"Authorization": "Bearer example-webhook-token"},
    )

    assert response.status_code == 422


def test_webhook_ticket_returns_400_for_unknown_backend(monkeypatch) -> None:
    monkeypatch.delenv("LLM_OPS_WEBHOOK_TOKEN", raising=False)
    monkeypatch.setenv("LLM_OPS_ALLOW_UNAUTHENTICATED_LOCAL", "true")

    response = TestClient(webhook_handler.app).post(
        "/webhook/ticket",
        json={"subject": "Shipment late", "backend": "missing"},
    )

    assert response.status_code == 400


def test_webhook_ticket_returns_422_for_blank_subject(monkeypatch) -> None:
    monkeypatch.delenv("LLM_OPS_WEBHOOK_TOKEN", raising=False)
    monkeypatch.setenv("LLM_OPS_ALLOW_UNAUTHENTICATED_LOCAL", "true")

    response = TestClient(webhook_handler.app).post(
        "/webhook/ticket",
        json={"subject": "   "},
    )

    assert response.status_code == 422


def test_webhook_ticket_captures_backend_runtime_failure(monkeypatch) -> None:
    monkeypatch.delenv("LLM_OPS_WEBHOOK_TOKEN", raising=False)
    monkeypatch.setenv("LLM_OPS_ALLOW_UNAUTHENTICATED_LOCAL", "true")

    async def broken_backend(prompt, deps, policy_snippets):
        raise RuntimeError("provider down")

    monkeypatch.setattr(webhook_handler, "run_pydantic_ai_backend", broken_backend)

    response = TestClient(webhook_handler.app).post(
        "/webhook/ticket",
        json={"subject": "Shipment late"},
    )

    result = response.json()["results"][0]
    assert response.status_code == 200
    assert result["status"] == "error"
    assert result["error"] == "Backend execution failed."


async def test_codex_backend_is_unavailable_until_explicitly_enabled(monkeypatch) -> None:
    monkeypatch.delenv("LLM_OPS_CODEX_APP_SERVER_ENABLED", raising=False)

    result = await webhook_handler.run_codex_app_server_backend(
        "Help",
        SupportTriageDependencies(),
        [],
    )

    assert result.status == TriageBackendStatus.UNAVAILABLE


async def test_claude_backend_is_unavailable_without_key(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    result = await webhook_handler.run_claude_agent_sdk_backend(
        "Help",
        SupportTriageDependencies(),
        [],
    )

    assert result.status == TriageBackendStatus.UNAVAILABLE
