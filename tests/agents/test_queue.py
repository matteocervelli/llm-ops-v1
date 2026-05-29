"""Tests for job queue — InMemory backend only (no Redis required)."""

import pytest

from llm_ops_v1.agents.queue import InMemoryQueue, JobQueue


@pytest.mark.asyncio
async def test_enqueue_and_consume() -> None:
    q = JobQueue(InMemoryQueue())
    job_id = await q.enqueue({"ticket": "test"})
    assert job_id

    item = await q.consume()
    assert item is not None
    assert item["payload"]["ticket"] == "test"


@pytest.mark.asyncio
async def test_consume_empty_returns_none() -> None:
    q = JobQueue(InMemoryQueue())
    assert await q.consume() is None


@pytest.mark.asyncio
async def test_ack_removes_job() -> None:
    q = JobQueue(InMemoryQueue())
    await q.enqueue({"x": 1})
    item = await q.consume()
    assert item is not None
    await q.ack(item["id"])
    # After ack, consuming again should return None
    assert await q.consume() is None


@pytest.mark.asyncio
async def test_set_and_get_result() -> None:
    q = JobQueue(InMemoryQueue())
    job_id = await q.enqueue({})
    await q.set_result(job_id, {"answer": 42})
    result = await q.get_result(job_id)
    assert result == {"answer": 42}


@pytest.mark.asyncio
async def test_get_result_missing_returns_none() -> None:
    q = JobQueue(InMemoryQueue())
    assert await q.get_result("nonexistent") is None
