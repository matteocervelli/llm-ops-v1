"""Job queue — InMemory and Redis Streams backends.

Provides at-least-once delivery: jobs must be acked after processing.
The InMemory backend is used in tests; RedisStreamsQueue in production.

Anatomy of a job entry: {"id": str, "payload": dict[str, Any]}
"""

import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Protocol


class QueueBackend(Protocol):
    async def enqueue(self, payload: dict[str, Any]) -> str: ...
    async def consume(self) -> dict[str, Any] | None: ...
    async def ack(self, job_id: str) -> None: ...
    async def set_result(self, job_id: str, result: dict[str, Any]) -> None: ...
    async def get_result(self, job_id: str) -> dict[str, Any] | None: ...


@dataclass
class InMemoryQueue:
    """Single-process queue for tests and offline demo."""

    _pending: deque[dict[str, Any]] = field(default_factory=deque)
    _in_flight: dict[str, dict[str, Any]] = field(default_factory=dict)
    _results: dict[str, dict[str, Any]] = field(default_factory=dict)

    async def enqueue(self, payload: dict[str, Any]) -> str:
        job_id = uuid.uuid4().hex
        self._pending.append({"id": job_id, "payload": payload})
        return job_id

    async def consume(self) -> dict[str, Any] | None:
        if not self._pending:
            return None
        item = self._pending.popleft()
        self._in_flight[item["id"]] = item
        return item

    async def ack(self, job_id: str) -> None:
        self._in_flight.pop(job_id, None)

    async def set_result(self, job_id: str, result: dict[str, Any]) -> None:
        self._results[job_id] = result

    async def get_result(self, job_id: str) -> dict[str, Any] | None:
        return self._results.get(job_id)

    def depth(self) -> dict[str, int]:
        return {
            "pending": len(self._pending),
            "in_flight": len(self._in_flight),
            "complete": len(self._results),
        }


class RedisStreamsQueue:
    """Redis Streams backed queue with consumer group for at-least-once delivery."""

    _STREAM = "llmops:jobs"
    _GROUP = "triage-workers"
    _CONSUMER = "worker-1"
    _RESULT_TTL = 3600  # seconds

    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        import redis.asyncio as aioredis  # type: ignore[import-untyped]

        self._r = aioredis.from_url(url, decode_responses=True)
        self._group_created = False

    async def _ensure_group(self) -> None:
        if self._group_created:
            return
        try:
            await self._r.xgroup_create(self._STREAM, self._GROUP, id="0", mkstream=True)
        except Exception as exc:
            message = exc.args[0] if exc.args and isinstance(exc.args[0], str) else ""
            if "BUSYGROUP" not in message:
                raise
        self._group_created = True

    async def enqueue(self, payload: dict[str, Any]) -> str:
        import json

        await self._ensure_group()
        job_id = uuid.uuid4().hex
        await self._r.xadd(self._STREAM, {"id": job_id, "payload": json.dumps(payload)})
        return job_id

    async def consume(self) -> dict[str, Any] | None:
        import json

        await self._ensure_group()
        results = await self._r.xreadgroup(
            self._GROUP, self._CONSUMER, {self._STREAM: ">"}, count=1, block=0
        )
        if not results:
            return None
        _stream, messages = results[0]
        msg_id, data = messages[0]
        return {"id": data["id"], "_stream_id": msg_id, "payload": json.loads(data["payload"])}

    async def ack(self, job_id: str) -> None:
        # job_id here is the stream message id stored as _stream_id
        await self._r.xack(self._STREAM, self._GROUP, job_id)

    async def set_result(self, job_id: str, result: dict[str, Any]) -> None:
        import json

        await self._r.setex(f"llmops:result:{job_id}", self._RESULT_TTL, json.dumps(result))

    async def get_result(self, job_id: str) -> dict[str, Any] | None:
        import json

        raw = await self._r.get(f"llmops:result:{job_id}")
        return json.loads(raw) if raw else None


@dataclass
class JobQueue:
    """Thin wrapper — backend-agnostic entry point."""

    _backend: QueueBackend

    async def enqueue(self, payload: dict[str, Any]) -> str:
        return await self._backend.enqueue(payload)

    async def consume(self) -> dict[str, Any] | None:
        return await self._backend.consume()

    async def ack(self, job_id: str) -> None:
        await self._backend.ack(job_id)

    async def set_result(self, job_id: str, result: dict[str, Any]) -> None:
        await self._backend.set_result(job_id, result)

    async def get_result(self, job_id: str) -> dict[str, Any] | None:
        return await self._backend.get_result(job_id)

    def depth(self) -> dict[str, int]:
        """Return pending/in_flight/complete counts. InMemoryQueue only."""
        if hasattr(self._backend, "depth"):
            return self._backend.depth()  # type: ignore[attr-defined]
        return {"pending": -1, "in_flight": -1, "complete": -1}
