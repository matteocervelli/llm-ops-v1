import pytest

from llm_ops_v1 import cli
from llm_ops_v1.agents.base_agent import SupportTriageDependencies


def test_triage_command_zero_key_outputs_required_labels(capsys, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    exit_code = cli.main(["triage", "Il mio ordine è in ritardo"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Category:" in captured.out
    assert "Reply draft:" in captured.out
    assert "Decision:" in captured.out
    assert "Estimated cost:" in captured.out


def test_parse_triage_output_extracts_zero_key_fields() -> None:
    output = (
        "Category: shipping_delay. "
        "Reply draft: Ci dispiace per il ritardo della spedizione. Abbiamo ricevuto "
        "la richiesta e stiamo verificando l'aggiornamento di tracking; invieremo "
        "un nuovo stato entro 2 ore. "
        "Decision: reply. "
        "Estimated cost: $0.0003."
    )

    summary = cli.parse_triage_output(output)

    assert summary.category == "shipping_delay"
    assert summary.reply_draft.startswith("Ci dispiace per il ritardo")
    assert summary.decision == "reply"


def test_zero_key_order_change_request_is_not_shipping(capsys, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    exit_code = cli.main(
        [
            "triage",
            (
                "Vorrei modificare l'ordine SK894435 aggiungendo un articolo, "
                "togliendone un altro e ricalcolando il totale."
            ),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "tracking" not in captured.out.lower()
    assert "shipping_delay" not in captured.out
    assert "ricalcolare" in captured.out.lower() or "ricalcol" in captured.out.lower()
    assert "Decision: ask_clarification" in captured.out


def test_parse_triage_output_falls_back_to_raw_reply() -> None:
    output = "The customer needs help, but no labels were returned."

    summary = cli.parse_triage_output(output)

    assert summary.category == "unknown"
    assert summary.reply_draft == output
    assert summary.decision == "unknown"


def test_estimated_cost_is_independent_from_model_text() -> None:
    model_output = (
        "Category: other. "
        "Reply draft: We are checking the request. "
        "Decision: reply. "
        "Estimated cost: $9999.0000."
    )

    cost = cli.estimate_triage_cost("Please check my order.", model_output, [])
    formatted = cli.format_triage_summary(cli.parse_triage_output(model_output), cost)

    assert "Estimated cost: $9999.0000" not in formatted
    assert formatted.splitlines()[-1] == f"Estimated cost: ${cost:.4f}"


def test_triage_command_passes_dependency_flags(capsys, monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_run_support_triage_agent(
        prompt: str,
        deps: SupportTriageDependencies | None = None,
    ) -> str:
        captured["prompt"] = prompt
        captured["deps"] = deps
        return "Category: technical_problem. Reply draft: Checking now. Decision: escalate."

    monkeypatch.setattr(cli, "run_support_triage_agent", fake_run_support_triage_agent)

    exit_code = cli.main(
        [
            "triage",
            "App is broken",
            "--ticket-id",
            "ticket-42",
            "--customer-tier",
            "enterprise",
            "--ticket-priority",
            "urgent",
            "--policy",
            "Escalate enterprise outages.",
            "--policy",
            "Reply within 1 hour.",
        ]
    )

    deps = captured["deps"]
    assert exit_code == 0
    assert captured["prompt"] == "App is broken"
    assert isinstance(deps, SupportTriageDependencies)
    assert deps.ticket_id == "ticket-42"
    assert deps.customer_tier == "enterprise"
    assert deps.ticket_priority == "urgent"
    assert deps.policy_snippets == ["Escalate enterprise outages.", "Reply within 1 hour."]
    assert "Decision: escalate" in capsys.readouterr().out


def test_triage_command_handles_runtime_failure(capsys, monkeypatch) -> None:
    async def fake_run_support_triage_agent(
        prompt: str,
        deps: SupportTriageDependencies | None = None,
    ) -> str:
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(cli, "run_support_triage_agent", fake_run_support_triage_agent)

    exit_code = cli.main(["triage", "Help"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Error: provider unavailable" in captured.err


def test_triage_requires_ticket_text() -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["triage"])

    assert exc_info.value.code == 2
