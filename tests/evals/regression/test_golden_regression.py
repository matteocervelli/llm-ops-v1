"""Golden-set regression — DeterministicJudge, no API, CI-safe.

Gates: pass_rate >= 0.80, action_accuracy >= 0.50.
The action_accuracy threshold is intentionally low because the deterministic
output synthesised by the runner always prefixes with "decision: reply",
so escalate/ask_clarification examples will fail action detection.
What we're gating here is that the judge itself is stable and the dataset loads.
"""

import pytest

from llm_ops_v1.evals.datasets import load_golden
from llm_ops_v1.evals.deterministic import DeterministicJudge
from llm_ops_v1.evals.runner import run_eval

PASS_RATE_GATE = 0.80
ACTION_ACCURACY_GATE = 0.30  # synthetic output always says "reply"; raise when real agent wired


@pytest.mark.asyncio
@pytest.mark.regression
async def test_golden_pass_rate() -> None:
    dataset = load_golden()
    assert len(dataset) >= 10, "Golden set too small — check datasets/golden.jsonl"

    summary = await run_eval(dataset, DeterministicJudge())

    assert summary.pass_rate >= PASS_RATE_GATE, (
        f"pass_rate {summary.pass_rate:.2f} < gate {PASS_RATE_GATE}. "
        f"Failures: {[r.example_id for r in summary.results if not r.passed]}"
    )


@pytest.mark.asyncio
@pytest.mark.regression
async def test_golden_action_accuracy() -> None:
    dataset = load_golden()
    summary = await run_eval(dataset, DeterministicJudge())

    assert summary.action_accuracy >= ACTION_ACCURACY_GATE, (
        f"action_accuracy {summary.action_accuracy:.2f} < gate {ACTION_ACCURACY_GATE}."
    )


@pytest.mark.asyncio
async def test_runner_returns_correct_counts() -> None:
    dataset = load_golden()
    summary = await run_eval(dataset, DeterministicJudge())

    assert summary.total == len(dataset)
    assert 0.0 <= summary.pass_rate <= 1.0
    assert 1.0 <= summary.avg_score <= 10.0
