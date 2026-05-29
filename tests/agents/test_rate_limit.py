"""Tests for token-bucket rate limiter — InMemory backend only."""

import pytest

from llm_ops_v1.agents.rate_limit import InMemoryBucket, RateLimiter, RateLimitExceeded


@pytest.mark.asyncio
async def test_allows_calls_within_rate() -> None:
    limiter = RateLimiter(InMemoryBucket(capacity=5, refill_rate=5.0))
    for _ in range(5):
        await limiter.acquire("key1")  # should not raise


@pytest.mark.asyncio
async def test_raises_when_exhausted() -> None:
    limiter = RateLimiter(InMemoryBucket(capacity=2, refill_rate=0.0))
    await limiter.acquire("key2")
    await limiter.acquire("key2")
    with pytest.raises(RateLimitExceeded):
        await limiter.acquire("key2")


@pytest.mark.asyncio
async def test_different_keys_independent() -> None:
    limiter = RateLimiter(InMemoryBucket(capacity=1, refill_rate=0.0))
    await limiter.acquire("a")
    await limiter.acquire("b")  # separate bucket, should not raise
