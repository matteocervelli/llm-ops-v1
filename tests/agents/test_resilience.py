"""Tests for retry/backoff, circuit breaker, and context trimmer."""

import asyncio

import pytest

from llm_ops_v1.agents.resilience import (
    CircuitBreaker,
    CircuitOpen,
    RetryConfig,
    with_retry,
)

# --- retry ---


@pytest.mark.asyncio
async def test_retry_succeeds_on_first_try() -> None:
    calls = []

    async def fn() -> str:
        calls.append(1)
        return "ok"

    result = await with_retry(fn, RetryConfig(max_attempts=3, base_delay=0.0))
    assert result == "ok"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_retry_recovers_after_transient_failure() -> None:
    calls = []

    async def fn() -> str:
        calls.append(1)
        if len(calls) < 3:
            raise OSError("transient")
        return "ok"

    result = await with_retry(fn, RetryConfig(max_attempts=3, base_delay=0.0))
    assert result == "ok"
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_retry_raises_after_max_attempts() -> None:
    async def fn() -> str:
        raise OSError("always fails")

    with pytest.raises(OSError):
        await with_retry(fn, RetryConfig(max_attempts=2, base_delay=0.0))


# --- circuit breaker ---


@pytest.mark.asyncio
async def test_breaker_opens_after_threshold() -> None:
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60.0)

    async def failing() -> str:
        raise OSError("boom")

    for _ in range(2):
        with pytest.raises(OSError):
            await breaker.call(failing)

    with pytest.raises(CircuitOpen):
        await breaker.call(failing)


@pytest.mark.asyncio
async def test_breaker_closed_on_success() -> None:
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)

    async def ok() -> str:
        return "fine"

    result = await breaker.call(ok)
    assert result == "fine"
    assert breaker.failure_count == 0


@pytest.mark.asyncio
async def test_breaker_half_open_after_timeout() -> None:
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)

    async def fail() -> str:
        raise OSError("x")

    with pytest.raises(OSError):
        await breaker.call(fail)

    await asyncio.sleep(0.02)

    async def ok() -> str:
        return "recovered"

    result = await breaker.call(ok)
    assert result == "recovered"
