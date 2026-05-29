"""Tests for RAGAS adapter — structural only, no ragas import needed."""

from typing import Any

from llm_ops_v1.evals.ragas_adapter import TriageTrace, trace_to_sample


def test_trace_to_sample_no_tool_calls() -> None:
    trace = TriageTrace(
        prompt="Il mio ordine è in ritardo",
        output="decision: escalate",
        tool_calls=[],
        expected_action="escalate",
        expected_tool_calls=[],
    )
    sample = trace_to_sample(trace)
    assert sample["reference"] == "escalate"
    assert sample["reference_tool_calls"] == []
    messages = sample["user_input"]
    assert messages[0] == {"role": "human", "content": trace.prompt}
    assert messages[-1] == {"role": "ai", "content": trace.output}


def test_trace_to_sample_with_tool_calls() -> None:
    trace = TriageTrace(
        prompt="Cerca il numero d'ordine",
        output="reply: trovato",
        tool_calls=[{"name": "lookup_order", "args": {"id": "123"}, "result": "delayed"}],
        expected_action="reply",
        expected_tool_calls=["lookup_order"],
    )
    sample = trace_to_sample(trace)
    messages = sample["user_input"]
    roles = [m["role"] for m in messages]
    assert "tool" in roles
    assert sample["reference_tool_calls"] == [{"name": "lookup_order", "args": {}}]


def test_evaluate_traces_raises_without_ragas(monkeypatch: object) -> None:
    import sys

    # Remove ragas from sys.modules if present to simulate missing install.
    ragas_mods = [k for k in sys.modules if k.startswith("ragas")]
    saved = {k: sys.modules.pop(k) for k in ragas_mods}
    import builtins

    real_import = builtins.__import__

    def block_ragas(name: str, *args: Any, **kwargs: Any) -> object:
        if name.startswith("ragas"):
            raise ImportError("ragas not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", block_ragas)  # type: ignore[attr-defined]
    try:
        import importlib

        import llm_ops_v1.evals.ragas_adapter as mod

        importlib.reload(mod)
        import asyncio

        import pytest

        with pytest.raises(ImportError, match="ragas is not installed"):
            asyncio.run(mod.evaluate_traces([]))
    finally:
        sys.modules.update(saved)
