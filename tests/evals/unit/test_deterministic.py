"""Tests for DeterministicJudge — zero-dependency eval, CI-safe."""

import pytest

from llm_ops_v1.evals.deterministic import DeterministicJudge


@pytest.mark.asyncio
async def test_passing_output_shipping() -> None:
    judge = DeterministicJudge()
    score = await judge.judge_output(
        prompt="Il mio ordine è in ritardo",
        output="decision: Escalare al team spedizioni per aggiornare il tracking dell'ordine.",
        rubric="",
    )
    assert score.passed is True
    assert score.score == 8


@pytest.mark.asyncio
async def test_failing_output_contains_todo() -> None:
    judge = DeterministicJudge()
    score = await judge.judge_output(
        prompt="Il mio ordine è in ritardo",
        output="TODO: aggiungere logica qui",
        rubric="",
    )
    assert score.passed is False
    assert score.score == 4


@pytest.mark.asyncio
async def test_failing_output_too_short() -> None:
    judge = DeterministicJudge()
    score = await judge.judge_output(
        prompt="billing question",
        output="ok",
        rubric="",
    )
    assert score.passed is False


@pytest.mark.asyncio
async def test_failing_output_no_action_keyword() -> None:
    judge = DeterministicJudge()
    # Long enough, no TODO, but no decision:/reply/escalate/clarif
    output = " ".join(["parola"] * 20)
    score = await judge.judge_output(prompt="shipping", output=output, rubric="")
    assert score.passed is False


@pytest.mark.asyncio
async def test_protocol_method_exists() -> None:
    # Structural conformance: judge_output exists and is async-callable
    judge = DeterministicJudge()
    assert callable(getattr(judge, "judge_output", None))
