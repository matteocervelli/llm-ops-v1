import os
import uuid
from collections.abc import Generator
from typing import Any

import pytest

from llm_ops_v1.memory.episodic import EpisodicMemory


@pytest.fixture
def redis_episodic_backend() -> Generator[tuple[Any, str, str], None, None]:
    redis = pytest.importorskip("redis")
    redis_url = os.getenv("LLM_OPS_TEST_REDIS_URL", "redis://localhost:6379/0")
    client = redis.Redis.from_url(redis_url, decode_responses=True)
    try:
        client.ping()
    except redis.RedisError:
        pytest.skip("Redis unavailable for episodic integration tests")

    key_prefix = f"llm_ops_v1:test:episodic:{uuid.uuid4().hex}"
    try:
        yield client, redis_url, key_prefix
    finally:
        keys = list(client.scan_iter(f"{key_prefix}:*"))
        if keys:
            client.delete(*keys)
        client.close()


def test_redis_episodic_memory_persists_across_instances(
    redis_episodic_backend: tuple[Any, str, str],
) -> None:
    _, redis_url, key_prefix = redis_episodic_backend
    first_memory = EpisodicMemory(redis_url, ttl_seconds=60, key_prefix=key_prefix)

    first = first_memory.record("customer-123", "opened_ticket", "Package missing.")
    second = first_memory.record("customer-123", "opened_ticket", "Package still missing.")
    first_memory.record("customer-999", "opened_ticket", "Billing question.")

    restarted_memory = EpisodicMemory(redis_url, ttl_seconds=60, key_prefix=key_prefix)

    assert restarted_memory.latest_for_actor("customer-123", limit=3) == [first, second]
    assert len(restarted_memory.latest(limit=3)) == 3


def test_redis_episodic_memory_returns_global_latest_in_order(
    redis_episodic_backend: tuple[Any, str, str],
) -> None:
    _, redis_url, key_prefix = redis_episodic_backend
    memory = EpisodicMemory(redis_url, ttl_seconds=60, key_prefix=key_prefix)

    first = memory.record("customer-123", "opened_ticket", "Package missing.")
    second = memory.record("customer-999", "opened_ticket", "Billing question.")
    third = memory.record("customer-123", "opened_ticket", "Package still missing.")

    assert memory.latest(limit=2) == [second, third]
    assert memory.latest_for_actor("customer-123", limit=1) == [third]
    assert memory.latest(limit=0) == []
    assert memory.latest_for_actor("customer-123", limit=0) == []
    assert first.happened_at <= second.happened_at <= third.happened_at


def test_redis_episodic_memory_sets_ttl_and_hashes_actor_keys(
    redis_episodic_backend: tuple[Any, str, str],
) -> None:
    client, redis_url, key_prefix = redis_episodic_backend
    memory = EpisodicMemory(redis_url, ttl_seconds=60, key_prefix=key_prefix)

    memory.record("customer-123", "opened_ticket", "Package missing.")

    keys = sorted(str(key) for key in client.scan_iter(f"{key_prefix}:*"))

    assert f"{key_prefix}:global" in keys
    assert all("customer-123" not in key for key in keys)
    assert all(client.ttl(key) > 0 for key in keys)
