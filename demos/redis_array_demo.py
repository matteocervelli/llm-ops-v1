#!/usr/bin/env python3
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from redis import Redis
from redis.exceptions import RedisError

from llm_ops_v1.memory.redis_array import RedisArray

DEFAULT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_NAMESPACE = "module5:shared-research"
DEMO_KEY_PREFIX = "llm_ops_v1:demo:array"


@dataclass(frozen=True)
class ResearchFinding:
    agent: str
    finding: str


def research_findings() -> tuple[ResearchFinding, ...]:
    return (
        ResearchFinding(
            "research-agent-a",
            "Redis Array supports sparse indexed knowledge with ARSET and ARGREP.",
        ),
        ResearchFinding(
            "research-agent-b",
            "Shared memory lets agents publish findings into one Redis namespace.",
        ),
        ResearchFinding(
            "research-agent-c",
            "ARGREP can synthesize Redis and agent findings with server-side regex.",
        ),
    )


def write_research_finding(array: RedisArray, namespace: str, finding: ResearchFinding) -> int:
    return array.arinsert(namespace, f"{finding.agent}: {finding.finding}")


def reset_demo_namespace(redis_url: str, namespace: str) -> None:
    client = Redis.from_url(redis_url, decode_responses=True)
    try:
        client.delete(
            f"{DEMO_KEY_PREFIX}:{namespace}:idx",
            f"{DEMO_KEY_PREFIX}:{namespace}:values",
            f"{DEMO_KEY_PREFIX}:{namespace}:meta",
        )
    finally:
        client.close()


def run_shared_memory_demo(
    redis_url: str = DEFAULT_REDIS_URL,
    namespace: str = DEFAULT_NAMESPACE,
) -> list[tuple[int, str]]:
    array = RedisArray(redis_url, ttl_seconds=300, key_prefix=DEMO_KEY_PREFIX)
    array.ping()
    reset_demo_namespace(redis_url, namespace)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(write_research_finding, array, namespace, finding)
            for finding in research_findings()
        ]
        for future in futures:
            future.result()
    result = array.argrep(namespace, "-", "+", "RE", "Redis|ARGREP|agent", "WITHVALUES")
    return list(result)


def main() -> int:
    redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
    try:
        matches = run_shared_memory_demo(redis_url=redis_url)
    except RedisError as exc:
        print(f"Redis Array demo unavailable: {exc.__class__.__name__}")
        return 1

    print("Synthesis agent findings:")
    for index, value in matches:
        print(f"{index}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
