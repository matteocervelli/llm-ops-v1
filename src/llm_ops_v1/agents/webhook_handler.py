import asyncio
import hmac
import json
import os
import shlex
import shutil
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any, NotRequired, TypedDict

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query
from fastapi import Depends, FastAPI, Header, HTTPException, Path, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from langgraph.graph import END, START, StateGraph

from llm_ops_v1.agents.base_agent import (
    SUPPORT_TRIAGE_SYSTEM_PROMPT,
    SupportTriageDependencies,
    run_support_triage_agent,
    wrap_external,
)
from llm_ops_v1.agents.queue import InMemoryQueue, JobQueue
from llm_ops_v1.agents.rate_limit import InMemoryBucket, RateLimiter, RateLimitExceeded
from llm_ops_v1.agents.triage_contracts import (  # noqa: E402
    TicketWebhookRequest,
    TicketWebhookResponse,
    TriageBackend,
    TriageBackendResult,
    TriageBackendStatus,
    TriageMode,
    build_ticket_prompt,
    enabled_backends,
    estimate_triage_cost,
    parse_triage_output,
)

app = FastAPI(title="LLM Ops webhook triage")

# Module-level singletons — replaceable in tests via app.state or direct assignment.
_rate_limiter = RateLimiter(InMemoryBucket(capacity=60.0, refill_rate=1.0))
_job_queue = JobQueue(InMemoryQueue())

Runner = Callable[[str, SupportTriageDependencies, list[str]], Awaitable[TriageBackendResult]]


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: object,
    exc: RequestValidationError,
) -> JSONResponse:
    status_code = 400 if _has_backend_validation_error(exc) else 422
    return JSONResponse(status_code=status_code, content=jsonable_encoder({"detail": exc.errors()}))


class GraphState(TypedDict):
    prompt: str
    deps: SupportTriageDependencies
    policy_snippets: list[str]
    output: NotRequired[str]
    result: NotRequired[TriageBackendResult]


async def require_webhook_auth(
    request: Request,
    authorization: str | None = Header(default=None),
) -> None:
    token = os.getenv("LLM_OPS_WEBHOOK_TOKEN")
    if not token and _allow_unauthenticated_local(request):
        return
    if not token:
        raise HTTPException(status_code=401, detail="Webhook token is not configured.")
    expected = f"Bearer {token}"
    if authorization and hmac.compare_digest(authorization, expected):
        return
    raise HTTPException(status_code=401, detail="Missing or invalid webhook token.")


@app.post("/webhook/ticket", response_model=TicketWebhookResponse)
async def webhook_ticket(
    request: TicketWebhookRequest,
    _authorized: None = Depends(require_webhook_auth),
) -> TicketWebhookResponse:
    prompt = build_ticket_prompt(request)
    deps = SupportTriageDependencies(
        ticket_id=request.ticket_id,
        customer_tier=request.customer_tier,
        ticket_priority=request.ticket_priority,
        policy_snippets=[],
    )
    results = [
        await _run_backend(backend, prompt, deps, deps.policy_snippets)
        for backend in enabled_backends(request.backend)
    ]
    return TicketWebhookResponse(
        request_id=str(uuid.uuid4()),
        subject=request.subject,
        results=results,
    )


async def run_pydantic_ai_backend(
    prompt: str,
    deps: SupportTriageDependencies,
    policy_snippets: list[str],
) -> TriageBackendResult:
    output = await run_support_triage_agent(prompt, deps)
    mode = TriageMode.LIVE if _has_provider_key() else TriageMode.FALLBACK
    return _ok_result(TriageBackend.PYDANTIC_AI, output, prompt, policy_snippets, mode)


async def run_claude_agent_sdk_backend(
    prompt: str,
    _deps: SupportTriageDependencies,
    policy_snippets: list[str],
) -> TriageBackendResult:
    if not os.getenv("ANTHROPIC_API_KEY"):
        return _unavailable_result(TriageBackend.CLAUDE_AGENT_SDK, "ANTHROPIC_API_KEY is not set.")

    options = ClaudeAgentOptions(
        system_prompt=SUPPORT_TRIAGE_SYSTEM_PROMPT,
        max_turns=1,
        tools=[],
        permission_mode="dontAsk",
        max_budget_usd=_env_float("LLM_OPS_CLAUDE_MAX_BUDGET_USD", 0.05),
    )
    output = ""
    cost_usd: float | None = None
    async for message in query(prompt=wrap_external(prompt), options=options):
        if isinstance(message, AssistantMessage):
            output += _assistant_text(message)
        if isinstance(message, ResultMessage):
            cost_usd = message.total_cost_usd
            output = output or (message.result or "")

    result = _ok_result(
        TriageBackend.CLAUDE_AGENT_SDK,
        output,
        prompt,
        policy_snippets,
        TriageMode.LIVE,
    )
    if cost_usd is not None:
        result.cost_usd = cost_usd
    return result


async def run_codex_app_server_backend(
    prompt: str,
    _deps: SupportTriageDependencies,
    policy_snippets: list[str],
) -> TriageBackendResult:
    if os.getenv("LLM_OPS_CODEX_APP_SERVER_ENABLED", "").lower() not in {"1", "true", "yes"}:
        return _unavailable_result(
            TriageBackend.CODEX_APP_SERVER,
            "Set LLM_OPS_CODEX_APP_SERVER_ENABLED=true to use codex app-server.",
        )
    if not os.getenv("LLM_OPS_WEBHOOK_TOKEN"):
        return _unavailable_result(
            TriageBackend.CODEX_APP_SERVER,
            "Codex app-server backend requires webhook authentication.",
        )

    command = shlex.split(
        os.getenv("CODEX_APP_SERVER_COMMAND", "codex app-server --listen stdio://")
    )
    if not command or not shutil.which(command[0]):
        return _unavailable_result(TriageBackend.CODEX_APP_SERVER, "Codex CLI is not available.")

    output = await _run_codex_json_rpc(command, _codex_prompt(prompt))
    return _ok_result(
        TriageBackend.CODEX_APP_SERVER,
        output,
        prompt,
        policy_snippets,
        TriageMode.LIVE,
    )


async def run_langgraph_backend(
    prompt: str,
    deps: SupportTriageDependencies,
    policy_snippets: list[str],
) -> TriageBackendResult:
    graph = _build_langgraph()
    state = await graph.ainvoke(
        {"prompt": prompt, "deps": deps, "policy_snippets": policy_snippets}
    )
    return state["result"]


async def _run_backend(
    backend: TriageBackend,
    prompt: str,
    deps: SupportTriageDependencies,
    policy_snippets: list[str],
) -> TriageBackendResult:
    start = time.perf_counter()
    runner = _backend_runners()[backend]
    try:
        result = await runner(prompt, deps, policy_snippets)
    except Exception:
        result = _error_result(backend, "Backend execution failed.")
    return result.model_copy(update={"latency_ms": _elapsed_ms(start)})


def _backend_runners() -> dict[TriageBackend, Runner]:
    return {
        TriageBackend.PYDANTIC_AI: run_pydantic_ai_backend,
        TriageBackend.CLAUDE_AGENT_SDK: run_claude_agent_sdk_backend,
        TriageBackend.CODEX_APP_SERVER: run_codex_app_server_backend,
        TriageBackend.LANGGRAPH: run_langgraph_backend,
    }


def _has_backend_validation_error(exc: RequestValidationError) -> bool:
    for error in exc.errors():
        if tuple(error.get("loc", ())) == ("body", "backend"):
            return True
    return False


def _ok_result(
    source: TriageBackend,
    output: str,
    prompt: str,
    policy_snippets: list[str],
    mode: TriageMode,
) -> TriageBackendResult:
    summary = parse_triage_output(output)
    return TriageBackendResult(
        source=source,
        status=TriageBackendStatus.OK,
        classification=summary.category,
        draft_reply=summary.reply_draft,
        decision=summary.decision,
        cost_usd=estimate_triage_cost(prompt, output, policy_snippets),
        mode=mode,
        latency_ms=0,
    )


def _unavailable_result(source: TriageBackend, reason: str) -> TriageBackendResult:
    return TriageBackendResult(
        source=source,
        status=TriageBackendStatus.UNAVAILABLE,
        classification="unknown",
        draft_reply="",
        decision="unavailable",
        cost_usd=0.0,
        mode=TriageMode.UNAVAILABLE,
        latency_ms=0,
        error=reason,
    )


def _error_result(source: TriageBackend, reason: str) -> TriageBackendResult:
    return TriageBackendResult(
        source=source,
        status=TriageBackendStatus.ERROR,
        classification="unknown",
        draft_reply="",
        decision="error",
        cost_usd=0.0,
        mode=TriageMode.UNAVAILABLE,
        latency_ms=0,
        error=reason,
    )


def _build_langgraph() -> Any:
    graph = StateGraph(GraphState)
    graph.add_node("triage", _langgraph_triage_node)
    graph.add_node("parse", _langgraph_parse_node)
    graph.add_edge(START, "triage")
    graph.add_edge("triage", "parse")
    graph.add_edge("parse", END)
    return graph.compile()


async def _langgraph_triage_node(state: GraphState) -> dict[str, str]:
    output = await run_support_triage_agent(state["prompt"], state["deps"])
    return {"output": output}


async def _langgraph_parse_node(state: GraphState) -> dict[str, TriageBackendResult]:
    mode = TriageMode.LIVE if _has_provider_key() else TriageMode.FALLBACK
    result = _ok_result(
        TriageBackend.LANGGRAPH,
        state.get("output", ""),
        state["prompt"],
        state["policy_snippets"],
        mode,
    )
    return {"result": result}


async def _run_codex_json_rpc(command: list[str], prompt: str) -> str:
    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    if process.stdin is None or process.stdout is None:
        raise RuntimeError("Codex app-server stdio transport is unavailable.")
    try:
        await _send_rpc(process.stdin, 1, "initialize", _codex_initialize_params())
        await _read_rpc_response(process.stdout, 1)
        await _send_notification(process.stdin, "initialized", {})
        await _send_rpc(process.stdin, 2, "thread/start", {"ephemeral": True, "cwd": os.getcwd()})
        thread_response = await _read_rpc_response(process.stdout, 2)
        thread_id = _thread_id(thread_response)
        await _send_rpc(process.stdin, 3, "turn/start", {"threadId": thread_id, "input": prompt})
        return await _collect_codex_turn(process.stdout)
    finally:
        if process.returncode is None:
            process.terminate()
        await process.wait()


async def _send_rpc(
    writer: asyncio.StreamWriter,
    message_id: int,
    method: str,
    params: dict[str, Any],
) -> None:
    message = {"id": message_id, "method": method, "params": params}
    writer.write(json.dumps(message).encode() + b"\n")
    await writer.drain()


async def _send_notification(
    writer: asyncio.StreamWriter,
    method: str,
    params: dict[str, Any],
) -> None:
    writer.write(json.dumps({"method": method, "params": params}).encode() + b"\n")
    await writer.drain()


async def _read_rpc_response(reader: asyncio.StreamReader, message_id: int) -> dict[str, Any]:
    while line := await reader.readline():
        message = json.loads(line)
        if message.get("id") == message_id:
            if "error" in message:
                raise RuntimeError(str(message["error"]))
            return message
    raise RuntimeError("Codex app-server closed before responding.")


async def _collect_codex_turn(reader: asyncio.StreamReader) -> str:
    chunks: list[str] = []
    while line := await reader.readline():
        message = json.loads(line)
        method = message.get("method")
        params = message.get("params", {})
        if method == "item/agentMessage/delta":
            chunks.append(str(params.get("delta", "")))
        if method == "turn/completed":
            return "".join(chunks) or _codex_completed_text(params)
    raise RuntimeError("Codex app-server closed before turn completed.")


def _thread_id(response: dict[str, Any]) -> str:
    result = response.get("result", {})
    thread = result.get("thread", result)
    thread_id = thread.get("id")
    if not isinstance(thread_id, str):
        raise RuntimeError("Codex app-server did not return a thread id.")
    return thread_id


def _codex_completed_text(params: dict[str, Any]) -> str:
    turn = params.get("turn", {})
    items = turn.get("items", [])
    messages = [item.get("text", "") for item in items if item.get("type") == "agent_message"]
    return "\n".join(message for message in messages if message)


def _codex_initialize_params() -> dict[str, Any]:
    return {
        "clientInfo": {
            "name": "llm_ops_v1",
            "title": "LLM Ops v1 Webhook Demo",
            "version": "0.1.0",
        },
        "capabilities": {"experimentalApi": True},
    }


def _codex_prompt(prompt: str) -> str:
    return "\n\n".join([SUPPORT_TRIAGE_SYSTEM_PROMPT, wrap_external(prompt)])


def _assistant_text(message: AssistantMessage) -> str:
    chunks = [block.text for block in message.content if isinstance(block, TextBlock)]
    return "\n".join(chunks)


def _has_provider_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))


def _allow_unauthenticated_local(request: Request) -> bool:
    if os.getenv("LLM_OPS_ALLOW_UNAUTHENTICATED_LOCAL", "").lower() not in {"1", "true", "yes"}:
        return False
    client = request.client
    return bool(client and client.host in {"127.0.0.1", "::1", "localhost", "testclient"})


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


# ---------------------------------------------------------------------------
# Async (queue-based) endpoints
# ---------------------------------------------------------------------------


async def _rate_limit_dep(authorization: str | None = Header(default=None)) -> None:
    key = authorization or "anonymous"
    try:
        await _rate_limiter.acquire(key)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded.",
            headers={"Retry-After": "1"},
        ) from exc


@app.post("/webhook/ticket/async", status_code=202)
async def webhook_ticket_async(
    request: TicketWebhookRequest,
    _authorized: None = Depends(require_webhook_auth),
    _rate: None = Depends(_rate_limit_dep),
) -> dict[str, str]:
    """Enqueue the ticket and return immediately with request_id.
    Poll GET /webhook/ticket/{request_id} for the result.
    """
    payload = request.model_dump()
    job_id = await _job_queue.enqueue(payload)
    return {"request_id": job_id, "status": "queued"}


@app.get("/webhook/ticket/{request_id}")
async def webhook_ticket_result(
    request_id: str = Path(min_length=1, max_length=64, pattern=r"^[a-f0-9]+$"),
    _authorized: None = Depends(require_webhook_auth),
    _rate: None = Depends(_rate_limit_dep),
) -> dict[str, object]:
    """Return the triage result for a queued job, or 'pending' if not ready."""
    result = await _job_queue.get_result(request_id)
    if result is None:
        return {"request_id": request_id, "status": "pending"}
    return {"request_id": request_id, "status": "complete", "result": result}
