from llm_ops_v1.dashboard.demo_runner import (
    DEMO_SCENARIOS,
    CacheEstimate,
    build_fixture_records,
    build_live_record,
    estimate_demo_metrics,
)
from llm_ops_v1.dashboard.models import DashboardRecord
from llm_ops_v1.evals.deterministic import evaluate as judge_zero_key_output

_VALID_ACTIONS = {"reply", "ask_clarification", "escalate"}

_GOOD_OUTPUT = (
    "Decision: reply. The shipment will arrive by Thursday. "
    "We have confirmed with the warehouse that the delay is resolved."
)
_TODO_OUTPUT = "TODO: figure out what to do here"


def test_estimate_demo_metrics_types() -> None:
    result = estimate_demo_metrics("What is the status?", "The order is on its way.")
    assert isinstance(result, CacheEstimate)
    assert 0.0 <= result.cache_hit_ratio <= 1.0
    assert result.total_cost_usd >= 0.0


def test_judge_zero_key_output_passes_good_output() -> None:
    result = judge_zero_key_output("How do we handle this?", _GOOD_OUTPUT)
    assert result.passed is True
    assert result.score >= 7


def test_judge_zero_key_output_fails_todo_output() -> None:
    result = judge_zero_key_output("How do we handle this?", _TODO_OUTPUT)
    assert result.passed is False
    assert result.score < 7


def test_judge_zero_key_output_fails_irrelevant_answer() -> None:
    result = judge_zero_key_output(
        "Vorrei modificare l'ordine e pagare con piu' tempo.",
        (
            "Category: shipping_delay. Reply draft: Ci dispiace per il ritardo della "
            "spedizione, controlliamo il tracking. Decision: reply."
        ),
    )

    assert result.passed is False
    assert result.score < 7


def test_judge_zero_key_output_accepts_order_change_answer() -> None:
    result = judge_zero_key_output(
        "Vorrei modificare l'ordine SK894435 aggiungendo un articolo e ricalcolando il totale.",
        (
            "Category: billing_issue. Reply draft: Possiamo verificare la modifica "
            "dell'ordine e ricalcolare il totale. Decision: ask_clarification."
        ),
    )

    assert result.passed is True
    assert result.score >= 7


def test_build_fixture_records_returns_empty_seed() -> None:
    assert build_fixture_records() == []


def test_demo_scenarios_cover_expected_operational_shapes() -> None:
    assert len(DEMO_SCENARIOS) == 4
    assert {scenario.deps.ticket_priority for scenario in DEMO_SCENARIOS} >= {
        "low",
        "urgent",
    }


def test_build_live_record_types() -> None:
    record = build_live_record("A package is missing.", _GOOD_OUTPUT, latency_ms=350.0)
    assert isinstance(record, DashboardRecord)
    assert record.action in _VALID_ACTIONS
    assert record.latency_ms == 350.0
    assert record.source == "live"


def test_build_live_record_escalate_parsed() -> None:
    output = "We need to escalate this issue to the supervisor immediately."
    record = build_live_record("Serious complaint received.", output, latency_ms=900.0)
    assert record.action == "escalate"
