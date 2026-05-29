"""Drift detection — Population Stability Index (PSI) and score/action drift.

PSI measures how much an input distribution has shifted relative to a baseline.
Rule of thumb: PSI < 0.1 = stable, 0.1-0.2 = monitor, > 0.2 = significant drift.

No scipy/numpy — PSI is simple enough to compute in-house (~20 lines).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from llm_ops_v1.dashboard.models import DashboardRecord


@dataclass(frozen=True)
class PSIResult:
    feature: str
    psi: float
    stable: bool  # psi < 0.1
    warn: bool  # 0.1 <= psi < 0.2
    drift: bool  # psi >= 0.2


@dataclass(frozen=True)
class ScoreDriftResult:
    baseline_avg: float
    current_avg: float
    delta: float
    drift: bool  # abs delta > threshold


@dataclass(frozen=True)
class DriftReport:
    psi_prompt_length: PSIResult
    psi_action: PSIResult
    score_drift: ScoreDriftResult
    any_drift: bool


def _psi(baseline: list[float], current: list[float], bins: int = 10) -> float:
    """Compute PSI between two numeric distributions."""
    if not baseline or not current:
        return 0.0
    lo = min(min(baseline), min(current))
    hi = max(max(baseline), max(current))
    if lo == hi:
        return 0.0
    width = (hi - lo) / bins

    def bucket(vals: list[float]) -> list[float]:
        counts = [0] * bins
        for v in vals:
            idx = min(int((v - lo) / width), bins - 1)
            counts[idx] += 1
        total = len(vals)
        return [max(c / total, 1e-6) for c in counts]

    b = bucket(baseline)
    c = bucket(current)
    return sum((c[i] - b[i]) * math.log(c[i] / b[i]) for i in range(bins))


def _categorical_psi(baseline: list[str], current: list[str]) -> float:
    """PSI over a categorical distribution (action labels)."""
    cats = set(baseline) | set(current)
    n_b, n_c = len(baseline), len(current)
    if n_b == 0 or n_c == 0:
        return 0.0
    total = 0.0
    for cat in cats:
        p_b = max(baseline.count(cat) / n_b, 1e-6)
        p_c = max(current.count(cat) / n_c, 1e-6)
        total += (p_c - p_b) * math.log(p_c / p_b)
    return total


def _psi_result(feature: str, psi: float) -> PSIResult:
    return PSIResult(
        feature=feature,
        psi=round(psi, 4),
        stable=psi < 0.1,
        warn=0.1 <= psi < 0.2,
        drift=psi >= 0.2,
    )


def compute_drift(
    baseline: list[DashboardRecord],
    current: list[DashboardRecord],
    score_delta_threshold: float = 1.0,
) -> DriftReport:
    """Compare two windows of DashboardRecord and return a DriftReport."""
    b_lengths = [float(len(r.prompt_preview.split())) for r in baseline]
    c_lengths = [float(len(r.prompt_preview.split())) for r in current]
    psi_len = _psi_result("prompt_length", _psi(b_lengths, c_lengths))

    b_actions = [r.action for r in baseline]
    c_actions = [r.action for r in current]
    psi_act = _psi_result("action", _categorical_psi(b_actions, c_actions))

    b_avg = sum(r.eval_score for r in baseline) / len(baseline) if baseline else 0.0
    c_avg = sum(r.eval_score for r in current) / len(current) if current else 0.0
    delta = abs(c_avg - b_avg)
    score_drift = ScoreDriftResult(
        baseline_avg=round(b_avg, 3),
        current_avg=round(c_avg, 3),
        delta=round(delta, 3),
        drift=delta > score_delta_threshold,
    )

    any_drift = psi_len.drift or psi_act.drift or score_drift.drift
    return DriftReport(
        psi_prompt_length=psi_len,
        psi_action=psi_act,
        score_drift=score_drift,
        any_drift=any_drift,
    )
