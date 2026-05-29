"""Tests for AlertEngine threshold evaluation."""

from datetime import UTC, datetime

from llm_ops_v1.dashboard.models import DashboardRecord
from llm_ops_v1.monitoring import alerts as alert_module
from llm_ops_v1.monitoring.alerts import AlertEngine, AlertThresholds


def _rec(
    latency_ms: float = 200.0,
    cost_usd: float = 0.001,
    score: float = 8.0,
    action: str = "reply",
) -> DashboardRecord:
    return DashboardRecord(
        run_id="r",
        prompt_preview="ticket",
        output_preview="output",
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        eval_score=score,
        action=action,
        timestamp=datetime.now(UTC),
    )


def test_no_alerts_when_within_thresholds() -> None:
    engine = AlertEngine(AlertThresholds())
    records = [_rec() for _ in range(10)]
    assert engine.evaluate(records) == []


def test_latency_alert_fired() -> None:
    engine = AlertEngine(AlertThresholds(max_p95_latency_ms=100.0))
    records = [_rec(latency_ms=9000.0) for _ in range(10)]
    alerts = engine.evaluate(records)
    metrics = [a.metric for a in alerts]
    assert "p95_latency_ms" in metrics


def test_low_score_alert_fired() -> None:
    engine = AlertEngine(AlertThresholds(min_avg_score=7.0))
    records = [_rec(score=3.0) for _ in range(10)]
    alerts = engine.evaluate(records)
    assert any(a.metric == "avg_score" for a in alerts)


def test_escalation_rate_alert_fired() -> None:
    engine = AlertEngine(AlertThresholds(max_escalation_rate=0.2))
    records = [_rec(action="escalate") for _ in range(10)]
    alerts = engine.evaluate(records)
    assert any(a.metric == "escalation_rate" for a in alerts)


def test_empty_records_no_crash() -> None:
    engine = AlertEngine()
    assert engine.evaluate([]) == []


def test_alert_webhook_allows_https_public_host(monkeypatch) -> None:
    monkeypatch.setattr(
        alert_module.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("8.8.8.8", 443))],
    )

    assert alert_module._is_allowed_webhook_url("https://alerts.example.com/hook")


def test_alert_webhook_blocks_http_and_private_hosts(monkeypatch) -> None:
    monkeypatch.setattr(
        alert_module.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("127.0.0.1", 443))],
    )

    assert not alert_module._is_allowed_webhook_url("http://alerts.example.com/hook")
    assert not alert_module._is_allowed_webhook_url("https://localhost/hook")
