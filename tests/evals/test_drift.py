"""Tests for PSI drift detection."""

from datetime import UTC, datetime

from llm_ops_v1.dashboard.models import DashboardRecord
from llm_ops_v1.evals.drift import compute_drift


def _rec(prompt: str, action: str = "reply", score: float = 8.0) -> DashboardRecord:
    return DashboardRecord(
        run_id="r",
        prompt_preview=prompt,
        output_preview="output",
        latency_ms=100.0,
        cost_usd=0.001,
        eval_score=score,
        action=action,
        timestamp=datetime.now(UTC),
    )


def test_identical_windows_no_drift() -> None:
    records = [_rec("short prompt") for _ in range(20)]
    report = compute_drift(records, records)
    assert not report.any_drift
    assert report.psi_prompt_length.psi == 0.0


def test_score_drift_detected() -> None:
    baseline = [_rec("prompt", score=8.0) for _ in range(10)]
    current = [_rec("prompt", score=3.0) for _ in range(10)]
    report = compute_drift(baseline, current, score_delta_threshold=1.0)
    assert report.score_drift.drift
    assert report.any_drift


def test_action_distribution_drift() -> None:
    baseline = [_rec("p", action="reply") for _ in range(20)]
    # Sudden surge in escalations — very different distribution
    current = [_rec("p", action="escalate") for _ in range(20)]
    report = compute_drift(baseline, current)
    assert report.psi_action.psi > 0.1


def test_empty_windows_no_crash() -> None:
    report = compute_drift([], [])
    assert not report.any_drift
