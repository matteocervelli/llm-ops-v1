import os
import re
import uuid
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from typing import Any, cast

import pytest

from llm_ops_v1.memory.redis_array import RedisArray


@pytest.fixture
def redis_array_backend() -> Generator[tuple[Any, str, str], None, None]:
    redis = pytest.importorskip("redis")
    redis_url = os.getenv("LLM_OPS_TEST_REDIS_URL", "redis://localhost:6379/0")
    client = redis.Redis.from_url(redis_url, decode_responses=True)
    try:
        client.ping()
    except redis.RedisError:
        pytest.skip("Redis unavailable for array integration tests")

    key_prefix = f"llm_ops_v1:test:array:{uuid.uuid4().hex}"
    try:
        yield client, redis_url, key_prefix
    finally:
        keys = list(client.scan_iter(f"{key_prefix}:*"))
        if keys:
            client.delete(*keys)
        client.close()


def test_arset_sets_contiguous_values_and_counts_new_slots(
    redis_array_backend: tuple[Any, str, str],
) -> None:
    client, redis_url, key_prefix = redis_array_backend
    array = RedisArray(redis_url, ttl_seconds=60, key_prefix=key_prefix)

    assert array.arset("shared", 0, "alpha", "beta", "gamma") == 3
    assert array.arset("shared", 2, "GAMMA", "delta") == 1

    assert array.argrep("shared", "-", "+", "MATCH", "a", "WITHVALUES") == [
        (0, "alpha"),
        (1, "beta"),
        (3, "delta"),
    ]
    assert client.ttl(f"{key_prefix}:shared:idx") > 0
    assert client.ttl(f"{key_prefix}:shared:values") > 0


def test_arinsert_appends_sequentially_and_is_thread_safe(
    redis_array_backend: tuple[Any, str, str],
) -> None:
    _, redis_url, key_prefix = redis_array_backend
    array = RedisArray(redis_url, ttl_seconds=60, key_prefix=key_prefix)

    assert array.arinsert("shared", "first") == 0
    assert array.arinsert("shared", "second", "third") == 2

    values = [f"agent-{index}" for index in range(20)]
    with ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(lambda value: array.arinsert("parallel", value), values))

    results = cast(
        list[tuple[int, str]],
        array.argrep("parallel", "-", "+", "MATCH", "agent-", "WITHVALUES"),
    )

    assert len(results) == 20
    assert sorted(index for index, _ in results) == list(range(20))
    assert sorted(value for _, value in results) == sorted(values)


def test_argrep_supports_predicates_options_and_reverse_ranges(
    redis_array_backend: tuple[Any, str, str],
) -> None:
    _, redis_url, key_prefix = redis_array_backend
    array = RedisArray(redis_url, ttl_seconds=60, key_prefix=key_prefix)
    array.arset("shared", 0, "RedisArray", "redis-match", "array-only", "plain")

    assert array.argrep("shared", "-", "+", "MATCH", "redis", "NOCASE") == [0, 1]
    assert array.argrep("shared", "-", "+", "EXACT", "plain") == [3]
    assert array.argrep("shared", "-", "+", "GLOB", "*array*", "NOCASE") == [0, 2]
    assert array.argrep("shared", "-", "+", "RE", "^redis", "NOCASE", "WITHVALUES") == [
        (0, "RedisArray"),
        (1, "redis-match"),
    ]
    assert array.argrep(
        "shared",
        "-",
        "+",
        "MATCH",
        "redis",
        "GLOB",
        "*array*",
        "AND",
        "NOCASE",
    ) == [0]
    assert array.argrep("shared", "-", "+", "MATCH", "redis", "LIMIT", 1, "NOCASE") == [0]
    assert array.argrep("shared", "-", "+", "MATCH", "redis", "LIMIT", 0, "NOCASE") == []
    assert array.argrep("shared", 3, 0, "MATCH", "redis", "NOCASE", "WITHVALUES") == [
        (1, "redis-match"),
        (0, "RedisArray"),
    ]
    assert array.argrep("missing", "-", "+", "MATCH", "redis") == []


def test_argrep_dash_bound_uses_logical_zero_for_sparse_arrays(
    redis_array_backend: tuple[Any, str, str],
) -> None:
    _, redis_url, key_prefix = redis_array_backend
    array = RedisArray(redis_url, ttl_seconds=60, key_prefix=key_prefix)
    array.arset("sparse", 100, "far")

    assert array.argrep("sparse", "-", 50, "MATCH", "far") == []
    assert array.argrep("sparse", "+", "-", "MATCH", "far", "WITHVALUES") == [(100, "far")]


def test_argrep_validates_syntax_and_regex_limits(
    redis_array_backend: tuple[Any, str, str],
) -> None:
    _, redis_url, key_prefix = redis_array_backend
    array = RedisArray(redis_url, ttl_seconds=60, key_prefix=key_prefix)
    array.arset("shared", 0, "hello")

    with pytest.raises(ValueError, match="requires at least one predicate"):
        array.argrep("shared", "-", "+")
    with pytest.raises(ValueError, match="LIMIT requires"):
        array.argrep("shared", "-", "+", "MATCH", "hello", "LIMIT")
    with pytest.raises(ValueError, match="invalid regular expression"):
        array.argrep("shared", "-", "+", "RE", "(")
    with pytest.raises(ValueError, match="regular expression is empty"):
        array.argrep("shared", "-", "+", "RE", "")
    with pytest.raises(ValueError, match="maximum is 2048"):
        array.argrep("shared", "-", "+", "RE", "a" * 2049)
    with pytest.raises(ValueError, match="backreferences"):
        array.argrep("shared", "-", "+", "RE", r"(a)\1")
    with pytest.raises(ValueError, match="non-negative"):
        array.arset("shared", -1, "bad")
    with pytest.raises(ValueError, match="at least one value"):
        array.arinsert("shared")
    with pytest.raises(ValueError, match="ttl_seconds"):
        RedisArray(redis_url, ttl_seconds=0, key_prefix=key_prefix)


def test_no_case_rebuilds_regex_predicates_when_option_appears_after_re(
    redis_array_backend: tuple[Any, str, str],
) -> None:
    _, redis_url, key_prefix = redis_array_backend
    array = RedisArray(redis_url, ttl_seconds=60, key_prefix=key_prefix)
    array.arset("shared", 0, "Foo777", "bar")

    assert array.argrep("shared", "-", "+", "RE", r"^foo[0-9]+$", "NOCASE") == [0]
    assert re.search(r"^foo[0-9]+$", "Foo777") is None
