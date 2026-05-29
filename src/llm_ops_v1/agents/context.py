"""Budget-aware context trimming.

Trims policy snippets and message history to fit within a model's context
window. Uses the 1.3× word-count heuristic from _tokens.py.

Production systems would use a real tokenizer; this is deliberately simple.
"""

from collections.abc import Callable

from llm_ops_v1.agents._tokens import estimate_tokens
from llm_ops_v1.economics.local_models import LOCAL_MODELS


def trim_snippets(
    snippets: list[str],
    max_tokens: int,
    summarize: Callable[[list[str]], str] | None = None,
) -> list[str]:
    """Return the longest prefix of snippets that fits within max_tokens.

    If a summarize callback is provided and the full list exceeds the budget,
    the callback is called with the overflow and its result is appended.
    """
    kept: list[str] = []
    used = 0
    overflow: list[str] = []
    for snippet in snippets:
        cost = estimate_tokens(snippet)
        if used + cost <= max_tokens:
            kept.append(snippet)
            used += cost
        else:
            overflow.append(snippet)

    if overflow and summarize is not None:
        summary = summarize(overflow)
        if estimate_tokens(summary) + used <= max_tokens:
            kept.append(summary)

    return kept


def context_budget(model_id: str, reserved_output_tokens: int = 512) -> int:
    """Return the available input token budget for a local model."""
    profile = LOCAL_MODELS.get(model_id)
    if profile is None:
        return 4096
    return max(0, profile.context_window - reserved_output_tokens)
