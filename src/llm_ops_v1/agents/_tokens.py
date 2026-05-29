# Shared token estimation utility.
# Used by caching, economics, and eval modules to avoid duplicating the
# word-count × 1.3 heuristic. This is a didactic approximation; real systems
# use a tokenizer (tiktoken, SentencePiece) matched to the specific model.


def estimate_tokens(text: str) -> int:
    """Estimate token count for `text` using the 1.3× word-count heuristic.

    Returns 0 for empty input; minimum 1 for any non-empty input.
    """
    words = _normalize(text).split()
    if not words:
        return 0
    return int(max(1, len(words) * 1.3))


def _normalize(text: str) -> str:
    return " ".join(text.split())
