"""Tests for budget-aware context trimming."""

from llm_ops_v1.agents.context import context_budget, trim_snippets


def test_trim_keeps_all_when_under_budget() -> None:
    snippets = ["short", "also short"]
    result = trim_snippets(snippets, max_tokens=1000)
    assert result == snippets


def test_trim_drops_overflow() -> None:
    long = " ".join(["word"] * 100)  # ~130 tokens — does not fit
    result = trim_snippets([long], max_tokens=5)
    assert result == []


def test_trim_partial_keeps_fitting_prefix() -> None:
    snippets = ["aaa bbb ccc", " ".join(["x"] * 200)]
    result = trim_snippets(snippets, max_tokens=10)
    assert result == ["aaa bbb ccc"]


def test_trim_calls_summarize_on_overflow() -> None:
    snippets = ["keep this", " ".join(["overflow"] * 50)]
    summary_called_with: list[list[str]] = []

    def summarizer(items: list[str]) -> str:
        summary_called_with.append(items)
        return "summary"

    result = trim_snippets(snippets, max_tokens=20, summarize=summarizer)
    assert "summary" in result
    assert len(summary_called_with) == 1


def test_context_budget_known_model() -> None:
    budget = context_budget("ollama:qwen3.6:27b")
    assert budget == 128_000 - 512


def test_context_budget_unknown_model_returns_default() -> None:
    assert context_budget("unknown:model") == 4096
