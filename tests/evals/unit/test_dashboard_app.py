from datetime import UTC, datetime

from llm_ops_v1.dashboard.app import (
    build_action_counts,
    build_summary,
    build_table_rows,
    build_trend_rows,
)
from llm_ops_v1.dashboard.models import DashboardRecord


def _make_record(
    run_id: str,
    action: str,
    timestamp: datetime,
    cache_hit: bool = False,
) -> DashboardRecord:
    return DashboardRecord(
        run_id=run_id,
        prompt_preview=f"prompt {run_id}",
        output_preview=f"output {run_id}",
        latency_ms=100.0,
        cost_usd=0.001,
        eval_score=7.0,
        action=action,
        cache_hit=cache_hit,
        timestamp=timestamp,
    )


def test_build_summary_multiple_run_metrics() -> None:
    records = [
        _make_record("r-001", "reply", datetime(2026, 5, 22, 9, 0, tzinfo=UTC), True),
        _make_record("r-002", "escalate", datetime(2026, 5, 22, 9, 1, tzinfo=UTC)),
    ]
    summary = build_summary(records)

    assert summary.run_volume == 2
    assert summary.total_cost_usd == 0.002
    assert summary.avg_cost_usd == 0.001
    assert summary.escalation_rate == 0.5
    assert summary.cache_hit_ratio == 0.5


def test_build_summary_empty_records() -> None:
    summary = build_summary([])

    assert summary.run_volume == 0
    assert summary.avg_latency_ms == 0.0
    assert summary.total_cost_usd == 0.0
    assert summary.avg_cost_usd == 0.0
    assert summary.avg_eval_score == 0.0
    assert summary.escalation_rate == 0.0
    assert summary.cache_hit_ratio == 0.0


def test_build_table_rows_uses_record_table_row() -> None:
    rows = build_table_rows(
        [_make_record("r-001", "reply", datetime(2026, 5, 22, 9, 0, tzinfo=UTC))]
    )

    assert rows[0]["run_id"] == "r-001"
    assert rows[0]["source"] == "live"
    assert "cost_usd" in rows[0]
    assert "cache_hit" in rows[0]


def test_build_action_counts_groups_records() -> None:
    records = [
        _make_record("r-001", "reply", datetime(2026, 5, 22, 9, 0, tzinfo=UTC)),
        _make_record("r-002", "reply", datetime(2026, 5, 22, 9, 1, tzinfo=UTC)),
        _make_record(
            "r-003",
            "ask_clarification",
            datetime(2026, 5, 22, 9, 2, tzinfo=UTC),
        ),
        _make_record("r-004", "escalate", datetime(2026, 5, 22, 9, 3, tzinfo=UTC)),
    ]

    assert build_action_counts(records) == [
        {"action": "reply", "count": 2},
        {"action": "ask_clarification", "count": 1},
        {"action": "escalate", "count": 1},
    ]


def test_build_trend_rows_are_chronological() -> None:
    older = datetime(2026, 5, 22, 8, 59, 0, tzinfo=UTC)
    newer = datetime(2026, 5, 22, 9, 1, 0, tzinfo=UTC)
    records = [
        _make_record("newer", "reply", newer),
        _make_record("older", "escalate", older),
    ]

    rows = build_trend_rows(records)

    assert [row["timestamp"] for row in rows] == ["08:59:00", "09:01:00"]
