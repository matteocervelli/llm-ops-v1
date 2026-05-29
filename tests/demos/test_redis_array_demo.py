import importlib.util
import os
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from redis.exceptions import ConnectionError

DEMO_PATH = Path(__file__).resolve().parents[2] / "demos" / "redis_array_demo.py"


def _load_demo() -> Any:
    spec = importlib.util.spec_from_file_location("redis_array_demo", DEMO_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load Redis Array demo")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def redis_demo_backend() -> tuple[Any, str, str]:
    redis = pytest.importorskip("redis")
    redis_url = os.getenv("LLM_OPS_TEST_REDIS_URL", "redis://localhost:6379/0")
    client = redis.Redis.from_url(redis_url, decode_responses=True)
    try:
        client.ping()
    except redis.RedisError:
        pytest.skip("Redis unavailable for array demo tests")

    namespace = f"module5:test:{uuid.uuid4().hex}"
    return client, redis_url, namespace


def test_redis_array_demo_writes_and_synthesizes_shared_findings(
    redis_demo_backend: tuple[Any, str, str],
) -> None:
    client, redis_url, namespace = redis_demo_backend
    demo = _load_demo()
    try:
        matches = demo.run_shared_memory_demo(redis_url=redis_url, namespace=namespace)
    finally:
        keys = list(client.scan_iter(f"llm_ops_v1:demo:array:{namespace}:*"))
        if keys:
            client.delete(*keys)
        client.close()

    assert len(matches) == 3
    assert [index for index, _ in matches] == [0, 1, 2]
    assert all("research-agent-" in value for _, value in matches)


def test_redis_array_demo_reports_unavailable_redis_without_url_leak(capsys: Any) -> None:
    demo = _load_demo()
    secret_url = "redis://:example-password@localhost:1/0"

    with patch.object(demo, "run_shared_memory_demo", side_effect=ConnectionError("boom")):
        exit_code = demo.main()

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Redis Array demo unavailable: ConnectionError" in output
    assert secret_url not in output
