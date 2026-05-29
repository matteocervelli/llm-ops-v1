"""Async triage worker — consumes jobs from the queue and runs backends concurrently.

Run alongside the webhook server:
    uv run uvicorn llm_ops_v1.agents.webhook_handler:app --port 8080
    uv run python -m llm_ops_v1.agents.worker
"""

import asyncio
import logging
import os
import signal

from llm_ops_v1.agents.base_agent import SupportTriageDependencies
from llm_ops_v1.agents.queue import InMemoryQueue, JobQueue, RedisStreamsQueue
from llm_ops_v1.agents.triage_contracts import (
    TicketWebhookRequest,
    build_ticket_prompt,
    enabled_backends,
)
from llm_ops_v1.agents.webhook_handler import _run_backend

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 0.5  # seconds between consume attempts when queue is empty


def _make_queue() -> JobQueue:
    from dotenv import load_dotenv

    load_dotenv()  # pick up REDIS_URL from .env if not already in env
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        return JobQueue(RedisStreamsQueue(url=redis_url))
    except Exception:
        logger.warning("Redis unavailable — worker using in-memory queue.")
        return JobQueue(InMemoryQueue())


async def _process(job: dict, queue: JobQueue) -> None:  # type: ignore[type-arg]
    job_id = job["id"]
    try:
        payload = job["payload"]
        req = TicketWebhookRequest.model_validate(payload)
        prompt = build_ticket_prompt(req)
        deps = SupportTriageDependencies(
            ticket_id=req.ticket_id,
            customer_tier=req.customer_tier,
            ticket_priority=req.ticket_priority,
            policy_snippets=[],
        )
        # Run enabled backends concurrently (previously serial in the sync path).
        results = await asyncio.gather(
            *[
                _run_backend(b, prompt, deps, deps.policy_snippets)
                for b in enabled_backends(req.backend)
            ],
            return_exceptions=False,
        )
        await queue.set_result(job_id, {"results": [r.model_dump() for r in results]})
    except Exception:
        logger.exception("job %s failed", job_id)
        await queue.set_result(job_id, {"error": "Job processing failed."})
    finally:
        await queue.ack(str(job.get("_stream_id", job_id)))


async def run_worker(queue: JobQueue | None = None) -> None:
    q = queue or _make_queue()
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def _handle_sig(*_: object) -> None:
        stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_sig)

    logger.info("Worker started.")
    while not stop.is_set():
        try:
            job = await q.consume()
        except Exception as exc:
            # Redis auth failure or connection drop: avoid logging exception text,
            # because connection errors can include credentials from the URL.
            exc_name = exc.__class__.__name__.lower()
            if "auth" in exc_name or "noauth" in exc_name:
                logger.warning("Redis auth failed; switching to in-memory queue.")
                q = JobQueue(InMemoryQueue())
                continue
            logger.warning("Queue consume error; retrying.")
            await asyncio.sleep(_POLL_INTERVAL)
            continue
        if job is None:
            await asyncio.sleep(_POLL_INTERVAL)
            continue
        asyncio.create_task(_process(job, q))
    logger.info("Worker stopped.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())
