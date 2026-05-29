"""Tests for the shared token estimation utility."""

from llm_ops_v1.agents._tokens import estimate_tokens


def test_empty_string_returns_zero() -> None:
    assert estimate_tokens("") == 0


def test_single_word_returns_at_least_one() -> None:
    assert estimate_tokens("hello") >= 1


def test_scales_with_word_count() -> None:
    short = estimate_tokens("one two three")
    long = estimate_tokens("one two three four five six seven eight nine ten")
    assert long > short


def test_extra_whitespace_normalized() -> None:
    assert estimate_tokens("hello world") == estimate_tokens("hello  world")


def test_known_count() -> None:
    # 10 words × 1.3 = 13 tokens (floor)
    assert estimate_tokens("a b c d e f g h i j") == 13
