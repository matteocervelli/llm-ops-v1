"""Retry, circuit breaker, and provider fallback — in-house, no framework.

Kept intentionally small: this is a teaching repo. Production systems would
add hedging, bulkhead isolation, and dead-letter queues (see docs/05).
"""

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum, auto


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 0.5  # seconds; doubled each attempt
    max_delay: float = 10.0
    jitter: float = 0.1  # fraction of delay added randomly


_DEFAULT_RETRY = RetryConfig()


async def with_retry[T](
    fn: Callable[[], Awaitable[T]],
    config: RetryConfig | None = None,
) -> T:
    """Call fn up to config.max_attempts times with exponential backoff + jitter."""
    cfg = config if config is not None else _DEFAULT_RETRY
    last_exc: BaseException = RuntimeError("no attempts made")
    for attempt in range(cfg.max_attempts):
        try:
            return await fn()
        except Exception as exc:
            last_exc = exc
            if attempt < cfg.max_attempts - 1:
                delay = min(cfg.base_delay * (2**attempt), cfg.max_delay)
                delay += random.uniform(0, cfg.jitter * delay)
                if delay > 0:
                    await asyncio.sleep(delay)
    raise last_exc


class _State(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


class CircuitOpen(Exception):
    """Raised when a call is attempted while the breaker is open."""


@dataclass
class CircuitBreaker:
    """Simple closed/open/half-open breaker keyed per instance (one per provider)."""

    failure_threshold: int = 5
    recovery_timeout: float = 30.0  # seconds until half-open probe

    failure_count: int = field(default=0, init=False)
    _state: _State = field(default=_State.CLOSED, init=False)
    _opened_at: float = field(default=0.0, init=False)

    async def call[T](self, fn: Callable[[], Awaitable[T]]) -> T:
        if self._state == _State.OPEN:
            if time.monotonic() - self._opened_at >= self.recovery_timeout:
                self._state = _State.HALF_OPEN
            else:
                raise CircuitOpen("Circuit is open; call blocked.")
        try:
            result = await fn()
            self._on_success()
            return result
        except CircuitOpen:
            raise
        except Exception:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        self.failure_count = 0
        self._state = _State.CLOSED

    def _on_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold or self._state == _State.HALF_OPEN:
            self._state = _State.OPEN
            self._opened_at = time.monotonic()
