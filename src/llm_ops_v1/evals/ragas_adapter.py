"""RAGAS adapter for pydantic-ai triage traces.

Converts a triage execution trace into RAGAS MultiTurnSample format so that
agentic metrics (Agent Goal Accuracy, Tool Call Accuracy/F1) can be computed
offline in CI or in batch sampling runs.

IMPORTANT: RAGAS is an OFFLINE eval tool, not a production monitoring tool.
Run this on a sampled batch of traces (1-5%), not inline per request.
See docs/03-evals-llm-as-a-judge.md for the full architecture rationale.

Usage (requires ragas extra):
    pip install llm-ops-v1[evals]   # adds ragas dependency

    from llm_ops_v1.evals.ragas_adapter import trace_to_sample, evaluate_traces
    sample = trace_to_sample(trace, expected_action="escalate")
    results = await evaluate_traces([sample])
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TriageTrace:
    """Captured triage execution — collect this at runtime via the Langfuse callback."""

    prompt: str
    output: str
    tool_calls: list[dict[str, Any]]  # [{"name": str, "args": dict, "result": Any}]
    expected_action: str  # reply | ask_clarification | escalate
    expected_tool_calls: list[str]  # ordered list of expected tool names


def trace_to_sample(trace: TriageTrace) -> dict[str, Any]:
    """Convert a TriageTrace to a RAGAS MultiTurnSample dict.

    RAGAS does not ship a pydantic-ai integration (only LangGraph, LlamaIndex,
    Bedrock, OpenAI Swarm). This converter is written by hand.

    The MultiTurnSample schema:
        user_input: list of {"role": "human"|"ai"|"tool", "content": str}
        reference: str  (the expected final output / goal)
        reference_tool_calls: list of {"name": str, "args": dict}
    """
    messages: list[dict[str, str]] = [
        {"role": "human", "content": trace.prompt},
    ]
    for tc in trace.tool_calls:
        messages.append(
            {
                "role": "ai",
                "content": f"[tool_call] {tc['name']}({tc.get('args', {})})",
            }
        )
        messages.append(
            {
                "role": "tool",
                "content": str(tc.get("result", "")),
            }
        )
    messages.append({"role": "ai", "content": trace.output})

    return {
        "user_input": messages,
        "reference": trace.expected_action,
        "reference_tool_calls": [{"name": n, "args": {}} for n in trace.expected_tool_calls],
    }


async def evaluate_traces(
    traces: list[TriageTrace],
    llm_model: str = "claude-sonnet-4-6",
) -> list[dict[str, Any]]:
    """Run RAGAS agentic metrics on a list of traces.

    Requires ragas>=0.2 and ANTHROPIC_API_KEY (or OPENAI_API_KEY).
    Metrics: AgentGoalAccuracy (WithReference), ToolCallAccuracy.

    Raises ImportError with instructions if ragas is not installed.
    """
    try:
        from ragas import evaluate as ragas_evaluate  # type: ignore[import-not-found]
        from ragas.dataset_schema import MultiTurnSample  # type: ignore[import-not-found]
        from ragas.metrics import (  # type: ignore[import-not-found]
            AgentGoalAccuracyWithReference,
            ToolCallAccuracy,
        )
    except ImportError as exc:
        raise ImportError(
            "ragas is not installed. Install with: pip install 'llm-ops-v1[evals]'\n"
            "Note: ragas is intentionally an optional offline dependency — "
            "do NOT add it to the runtime dependencies."
        ) from exc

    samples = [MultiTurnSample(**trace_to_sample(t)) for t in traces]
    metrics = [AgentGoalAccuracyWithReference(), ToolCallAccuracy()]
    result = await ragas_evaluate(samples, metrics=metrics, llm=llm_model)
    return result.to_pandas().to_dict(orient="records")  # type: ignore[no-any-return]
