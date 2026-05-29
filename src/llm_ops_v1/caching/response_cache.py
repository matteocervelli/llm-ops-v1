"""Response cache — stores LLM answers keyed on (system+policies+ticket+model).

Two backends: InMemoryCache (tests, no-Redis fallback) and RedisCache (runtime).
Use ResponseCache as the entry point; it wraps either backend.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Protocol

from llm_ops_v1.agents._tokens import _normalize
from llm_ops_v1.caching.prompt_prefix import cache_key


def make_response_key(
    system_prompt: str,
    policy_snippets: list[str],
    ticket_text: str,
    model_id: str,
) -> str:
    """Stable cache key for a specific (prefix, ticket, model) triple."""
    prefix_key = cache_key(system_prompt, policy_snippets)
    ticket_norm = _normalize(ticket_text)
    payload = json.dumps(
        {"prefix": prefix_key, "ticket": ticket_norm, "model": model_id}, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode()).hexdigest()


class CacheBackend(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl_seconds: int) -> None: ...
    async def close(self) -> None: ...


@dataclass
class _Entry:
    value: str
    expires_at: float  # monotonic; 0 = never expires, <0 = already expired


class InMemoryCache:
    """In-process cache — for tests and no-Redis fallback."""

    def __init__(self) -> None:
        self._store: dict[str, _Entry] = {}

    async def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at != 0 and time.monotonic() >= entry.expires_at:
            del self._store[key]
            return None
        return entry.value

    async def set(self, key: str, value: str, ttl_seconds: int = 3600) -> None:
        expires_at = (time.monotonic() + ttl_seconds) if ttl_seconds > 0 else -1.0
        self._store[key] = _Entry(value=value, expires_at=expires_at)

    async def close(self) -> None:
        self._store.clear()


class RedisCache:
    """Redis-backed cache using the existing redis dependency."""

    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        import redis.asyncio as aioredis  # type: ignore[import-untyped]

        self._client = aioredis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self._client.get(f"llmops:rc:{key}")  # type: ignore[no-any-return]

    async def set(self, key: str, value: str, ttl_seconds: int = 3600) -> None:
        await self._client.setex(f"llmops:rc:{key}", ttl_seconds, value)

    async def close(self) -> None:
        await self._client.aclose()


@dataclass
class ResponseCache:
    """Thin wrapper that adds a default TTL and is backend-agnostic."""

    _backend: CacheBackend
    default_ttl: int = field(default=3600)

    async def get(self, key: str) -> str | None:
        return await self._backend.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        await self._backend.set(
            key, value, ttl_seconds if ttl_seconds is not None else self.default_ttl
        )

    async def close(self) -> None:
        await self._backend.close()
