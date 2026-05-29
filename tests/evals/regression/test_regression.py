import pytest
from pydantic_ai.models.test import TestModel

from llm_ops_v1.agents.base_agent import AgentDependencies, production_agent


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("Estimate the cost of 1k input and 500 output tokens.", "regression-a"),
        ("Report the current request context.", "regression-b"),
    ],
)
async def test_regression_suite(prompt: str, expected: str) -> None:
    test_model = TestModel(custom_output_text=expected)
    with production_agent.override(model=test_model):
        result = await production_agent.run(prompt, deps=AgentDependencies())
    assert result.output == expected
