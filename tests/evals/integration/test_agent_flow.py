import pytest
from pydantic_ai.models.test import TestModel

from llm_ops_v1.agents.base_agent import AgentDependencies, production_agent


@pytest.mark.asyncio
@pytest.mark.integration
async def test_agent_flow_exposes_tools() -> None:
    test_model = TestModel(custom_output_text="integration-ok")

    with production_agent.override(model=test_model):
        result = await production_agent.run(
            "Summarize the request context and estimate cost for a short reply.",
            deps=AgentDependencies(request_id="req-123", user_tier="beam-me-up"),
        )

    assert result.output == "integration-ok"
    assert test_model.last_model_request_parameters is not None
    assert test_model.last_model_request_parameters.function_tools
