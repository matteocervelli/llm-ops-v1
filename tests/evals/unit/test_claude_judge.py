"""Unit tests for ClaudeJudge — AsyncAnthropic mocked, no real API call."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm_ops_v1.evals.llm_judge import ClaudeJudge, JudgeScore


def _mock_response(score: int = 8, passed: bool = True, rationale: str = "good") -> MagicMock:
    payload = json.dumps({"score": score, "passed": passed, "rationale": rationale})
    block = MagicMock()
    block.text = payload
    response = MagicMock()
    response.content = [block]
    return response


@pytest.mark.asyncio
async def test_judge_output_returns_judge_score() -> None:
    mock_create = AsyncMock(return_value=_mock_response(score=9, passed=True, rationale="solid"))

    with patch("llm_ops_v1.evals.llm_judge.AsyncAnthropic") as mock_cls:
        mock_cls.return_value.messages.create = mock_create
        judge = ClaudeJudge()
        result = await judge.judge_output(
            prompt="test prompt",
            output="decision: escalate immediately.",
            rubric="must include an action",
        )

    assert isinstance(result, JudgeScore)
    assert result.score == 9
    assert result.passed is True
    assert result.rationale == "solid"
    mock_create.assert_awaited_once()


@pytest.mark.asyncio
async def test_judge_output_low_score() -> None:
    mock_create = AsyncMock(return_value=_mock_response(score=3, passed=False, rationale="vague"))

    with patch("llm_ops_v1.evals.llm_judge.AsyncAnthropic") as mock_cls:
        mock_cls.return_value.messages.create = mock_create
        judge = ClaudeJudge()
        result = await judge.judge_output("p", "short", "rubric")

    assert result.passed is False
    assert result.score == 3
