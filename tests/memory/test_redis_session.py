import os
import uuid
from collections.abc import Generator
from typing import Any

import pytest

from llm_ops_v1.memory.short_term import (
    InMemorySessionState,
    RedisSessionState,
    create_session_state,
)


@pytest.fixture
def redis_session_backend() -> Generator[tuple[Any, str, str], None, None]:
    redis = pytest.importorskip("redis")
    redis_url = os.getenv("LLM_OPS_TEST_REDIS_URL", "redis://localhost:6379/0")
    client = redis.Redis.from_url(redis_url, decode_responses=True)
    try:
        client.ping()
    except redis.RedisError:
        pytest.skip("Redis unavailable for session integration tests")

    key_prefix = f"llm_ops_v1:test:{uuid.uuid4().hex}"
    try:
        yield client, redis_url, key_prefix
    finally:
        keys = list(client.scan_iter(f"{key_prefix}:*"))
        if keys:
            client.delete(*keys)
        client.close()


def test_redis_session_second_ticket_sees_context_from_first(
    redis_session_backend: tuple[Any, str, str],
) -> None:
    _, redis_url, key_prefix = redis_session_backend
    state = RedisSessionState(redis_url, ttl_seconds=60, key_prefix=key_prefix)

    state.put("customer-123", "first_ticket_summary", "Shipment delayed; reply sent.")
    first_ticket_context = state.get("customer-123", "first_ticket_summary")
    state.put("customer-123", "second_ticket_context", first_ticket_context or "")

    assert state.get("customer-123", "second_ticket_context") == "Shipment delayed; reply sent."


def test_redis_session_state_is_isolated_by_session(
    redis_session_backend: tuple[Any, str, str],
) -> None:
    _, redis_url, key_prefix = redis_session_backend
    state = RedisSessionState(redis_url, ttl_seconds=60, key_prefix=key_prefix)

    state.put("session-a", "topic", "routing")
    state.put("session-b", "topic", "memory")

    assert state.get("session-a", "topic") == "routing"
    assert state.get("session-b", "topic") == "memory"
    assert state.get("session-a", "missing", "fallback") == "fallback"


def test_redis_session_snapshot_returns_copy_shaped_dict(
    redis_session_backend: tuple[Any, str, str],
) -> None:
    _, redis_url, key_prefix = redis_session_backend
    state = RedisSessionState(redis_url, ttl_seconds=60, key_prefix=key_prefix)
    state.put("session-a", "topic", "routing")

    snapshot = state.snapshot("session-a")
    snapshot["topic"] = "changed"

    assert snapshot == {"topic": "changed"}
    assert state.get("session-a", "topic") == "routing"
    assert state.snapshot("session-a") == {"topic": "routing"}


def test_redis_session_put_sets_positive_ttl(
    redis_session_backend: tuple[Any, str, str],
) -> None:
    client, redis_url, key_prefix = redis_session_backend
    state = RedisSessionState(redis_url, ttl_seconds=60, key_prefix=key_prefix)

    state.put("session-a", "topic", "routing")

    assert client.ttl(f"{key_prefix}:session-a") > 0


def test_redis_session_factory_falls_back_to_in_memory_when_unavailable() -> None:
    state = create_session_state("redis://localhost:1/0", ttl_seconds=1)

    assert isinstance(state, InMemorySessionState)
    state.put("session-a", "topic", "routing")
    assert state.get("session-a", "topic") == "routing"
