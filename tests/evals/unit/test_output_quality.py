import pytest


@pytest.mark.asyncio
async def test_output_quality(fake_judge) -> None:
    result = await fake_judge.judge_output(
        prompt="Explain why evals matter in production.",
        output=(
            "Evals create a repeatable quality gate and make regressions visible "
            "before release."
        ),
        rubric="The answer must be specific, concise, and operationally useful.",
    )

    assert result.passed is True
    assert result.score >= 7
