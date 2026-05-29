"""Token-bucket rate limiter — InMemory and Redis backends.

One bucket per API key. Capacity = burst size; refill_rate = tokens/second.
The Redis backend uses a Lua script for atomic check-and-decrement.
"""

import time
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Protocol


class RateLimitExceeded(Exception):
    """Raised when the bucket for a key is empty."""


class BucketBackend(Protocol):
    async def consume(self, key: str, capacity: float, refill_rate: float) -> bool:
        """Return True if a token was consumed, False if the bucket is empty."""
        ...


@dataclass
class _Bucket:
    tokens: float
    last_refill: float = field(default_factory=time.monotonic)


class InMemoryBucket:
    def __init__(self, capacity: float = 60.0, refill_rate: float = 1.0) -> None:
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._buckets: dict[str, _Bucket] = {}

    async def consume(self, key: str, capacity: float, refill_rate: float) -> bool:  # noqa: ARG002
        # Use constructor values so that InMemoryBucket(capacity=N) is self-contained.
        cap = self._capacity
        rate = self._refill_rate
        now = time.monotonic()
        bucket = self._buckets.setdefault(key, _Bucket(tokens=cap))
        elapsed = now - bucket.last_refill
        bucket.tokens = min(cap, bucket.tokens + elapsed * rate)
        bucket.last_refill = now
        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            return True
        return False


class RedisBucket:
    """Redis-backed token bucket using atomic Lua."""

    _LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local entry = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(entry[1]) or capacity
local ts = tonumber(entry[2]) or now
local elapsed = now - ts
tokens = math.min(capacity, tokens + elapsed * refill_rate)
if tokens >= 1 then
  tokens = tokens - 1
  redis.call('HMSET', key, 'tokens', tokens, 'ts', now)
  redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) + 60)
  return 1
end
redis.call('HMSET', key, 'tokens', tokens, 'ts', now)
return 0
"""

    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        import redis.asyncio as aioredis  # type: ignore[import-untyped]

        self._client = aioredis.from_url(url)
        self._script: Any = None

    async def consume(self, key: str, capacity: float, refill_rate: float) -> bool:
        if self._script is None:
            self._script = self._client.register_script(self._LUA)
        now = time.monotonic()
        result = await self._script(keys=[f"llmops:rl:{key}"], args=[capacity, refill_rate, now])
        return bool(result)


@dataclass
class RateLimiter:
    """Entry point: acquire(key) or raise RateLimitExceeded."""

    _backend: BucketBackend
    capacity: float = 60.0
    refill_rate: float = 1.0  # tokens per second

    async def acquire(self, key: str) -> None:
        ok = await self._backend.consume(_bucket_key(key), self.capacity, self.refill_rate)
        if not ok:
            raise RateLimitExceeded("Rate limit exceeded.")


def _bucket_key(key: str) -> str:
    return sha256(key.encode()).hexdigest()
