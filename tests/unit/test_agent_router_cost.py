"""Tests for cost-aware routing additions."""

from llm_ops_v1.agents.router import HAIKU_MODEL, SONNET_MODEL, decide_form


def test_simple_ticket_routes_haiku() -> None:
    form = decide_form("Where is my package?")
    assert form.model == HAIKU_MODEL


def test_complex_ticket_routes_sonnet() -> None:
    form = decide_form("Enterprise customer: billing refund and app outage both urgent.")
    assert form.model == SONNET_MODEL


def test_ambiguous_routes_escalate() -> None:
    form = decide_form("Help.")
    assert form.model == "escalate"


def test_cost_estimate_attached() -> None:
    form = decide_form("Where is my package?")
    assert form.estimated_cost_usd > 0.0


def test_budget_exceeded_downgrades_to_haiku(monkeypatch: object) -> None:
    import os

    # Set a tiny cap (0.000001 USD) so any Sonnet call exceeds it.
    monkeypatch.setenv("DAILY_SPEND_CAP_USD", "0.000001")  # type: ignore[attr-defined]
    form = decide_form(
        "Enterprise billing outage urgent multiple issues",
        session_total_usd=0.0,
    )
    # Sonnet cost > cap → falls back to Haiku.
    assert form.model == HAIKU_MODEL
    os.environ.pop("DAILY_SPEND_CAP_USD", None)
