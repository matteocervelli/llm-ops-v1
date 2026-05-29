"""Anthropic Messages API to OpenAI-compatible proxy demo."""

import json
import time
import uuid
from collections.abc import AsyncIterator
from typing import Protocol

import httpx
from fastapi.responses import JSONResponse

from .translation import _diagnostic_response, _stop_reason, _to_anthropic
from .types import (
    _IN_FLIGHT,
    BACKEND,
    DEFAULT_DEDUPE_WINDOW_MS,
    JsonDict,
    RequestContext,
    StreamResult,
    StreamToolCall,
    ToolInputError,
    _diagnostic_text,
    _env_bool,
    _env_int,
    _invalid_stream_tool_call,
    _invalid_tool_call,
    _retry_body,
    _split_harmony_text,
)


class _LineStream(Protocol):
    def aiter_lines(self) -> AsyncIterator[str]: ...


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _empty_stream(model: str, msg_id: str) -> AsyncIterator[str]:
    yield _sse(
        "message_start",
        {
            "type": "message_start",
            "message": {
                "id": msg_id,
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": model,
                "stop_reason": None,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        },
    )
    yield _sse(
        "message_delta",
        {
            "type": "message_delta",
            "delta": {"stop_reason": "end_turn", "stop_sequence": None},
            "usage": {"output_tokens": 0},
        },
    )
    yield 'event: message_stop\ndata: {"type": "message_stop"}\n\n'


async def _collect_stream(resp: _LineStream) -> StreamResult:
    result = StreamResult()

    async for line in resp.aiter_lines():
        if not line.startswith("data: "):
            continue
        raw = line[6:]
        if raw.strip() == "[DONE]":
            break
        try:
            chunk = json.loads(raw)
        except json.JSONDecodeError:
            continue
        choice = chunk.get("choices", [{}])[0]
        delta = choice.get("delta") or {}
        finish = choice.get("finish_reason")

        reasoning = delta.get("reasoning") or ""
        if reasoning:
            result.reasoning += reasoning

        text = delta.get("content") or ""
        if text:
            result.text += text
            result.output_tokens += 1

        for tc in delta.get("tool_calls") or []:
            i = tc.get("index", 0)
            if i not in result.tool_calls:
                result.tool_calls[i] = StreamToolCall()
            tool_call = result.tool_calls[i]
            if tc.get("id"):
                tool_call.tool_id = tc["id"]
            fn = tc.get("function") or {}
            if fn.get("name"):
                tool_call.name += fn["name"]
            if fn.get("arguments"):
                tool_call.argument_chunks.append(fn["arguments"])

        if finish:
            result.finish_reason = finish
    return _normalize_stream_result(result)


def _normalize_stream_result(result: StreamResult) -> StreamResult:
    content_reasoning, visible_text = _split_harmony_text(result.text)
    if content_reasoning:
        result.reasoning = "\n\n".join(
            part for part in [result.reasoning, content_reasoning] if part
        )
    result.text = visible_text
    return result


async def _stream_events(result: StreamResult, model: str, msg_id: str) -> AsyncIterator[str]:
    yield _sse(
        "message_start",
        {
            "type": "message_start",
            "message": {
                "id": msg_id,
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": model,
                "stop_reason": None,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        },
    )
    yield 'event: ping\ndata: {"type": "ping"}\n\n'

    block_idx = 0
    if result.reasoning:
        yield _sse(
            "content_block_start",
            {
                "type": "content_block_start",
                "index": block_idx,
                "content_block": {"type": "thinking", "thinking": ""},
            },
        )
        yield _sse(
            "content_block_delta",
            {
                "type": "content_block_delta",
                "index": block_idx,
                "delta": {"type": "thinking_delta", "thinking": result.reasoning},
            },
        )
        yield _sse("content_block_stop", {"type": "content_block_stop", "index": block_idx})
        block_idx += 1

    if result.text:
        yield _sse(
            "content_block_start",
            {
                "type": "content_block_start",
                "index": block_idx,
                "content_block": {"type": "text", "text": ""},
            },
        )
        yield _sse(
            "content_block_delta",
            {
                "type": "content_block_delta",
                "index": block_idx,
                "delta": {"type": "text_delta", "text": result.text},
            },
        )
        yield _sse("content_block_stop", {"type": "content_block_stop", "index": block_idx})
        block_idx += 1

    for _, tc in sorted(result.tool_calls.items()):
        yield _sse(
            "content_block_start",
            {
                "type": "content_block_start",
                "index": block_idx,
                "content_block": {
                    "type": "tool_use",
                    "id": tc.tool_id,
                    "name": tc.name,
                    "input": {},
                },
            },
        )
        for partial_json in tc.argument_chunks or [tc.arguments]:
            if partial_json:
                yield _sse(
                    "content_block_delta",
                    {
                        "type": "content_block_delta",
                        "index": block_idx,
                        "delta": {
                            "type": "input_json_delta",
                            "partial_json": partial_json,
                        },
                    },
                )
        yield _sse("content_block_stop", {"type": "content_block_stop", "index": block_idx})
        block_idx += 1

    if block_idx == 0:
        yield _sse(
            "content_block_start",
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            },
        )
        yield _sse("content_block_stop", {"type": "content_block_stop", "index": 0})

    yield _sse(
        "message_delta",
        {
            "type": "message_delta",
            "delta": {"stop_reason": _stop_reason(result.finish_reason), "stop_sequence": None},
            "usage": {"output_tokens": result.output_tokens},
        },
    )
    yield 'event: message_stop\ndata: {"type": "message_stop"}\n\n'


async def _diagnostic_stream(
    model: str, msg_id: str, invalid: ToolInputError
) -> AsyncIterator[str]:
    result = StreamResult(text=_diagnostic_text(invalid), finish_reason="stop", output_tokens=0)
    async for event in _stream_events(result, model, msg_id):
        yield event


async def _claim_request(fingerprint: str) -> bool:
    if not _env_bool("PROXY_DEDUPE", True):
        return True
    now = time.monotonic()
    window = _env_int("PROXY_DEDUPE_WINDOW_MS", DEFAULT_DEDUPE_WINDOW_MS) / 1000
    expired = [key for key, started in _IN_FLIGHT.items() if now - started > window]
    for key in expired:
        _IN_FLIGHT.pop(key, None)
    if fingerprint in _IN_FLIGHT:
        return False
    _IN_FLIGHT[fingerprint] = now
    return True


async def _release_request(fingerprint: str) -> None:
    _IN_FLIGHT.pop(fingerprint, None)


async def _collect_backend_stream(oai: JsonDict, headers: JsonDict) -> StreamResult:
    async with httpx.AsyncClient(timeout=300) as client:
        req = client.build_request(
            "POST", f"{BACKEND}/v1/chat/completions", json=oai, headers=headers
        )
        resp = await client.send(req, stream=True)
        try:
            if resp.status_code != 200:
                text = await resp.aread()
                detail = text.decode(errors="ignore")[:200]
                return StreamResult(
                    text=f"[proxy] Backend {resp.status_code}: {detail}",
                    finish_reason="stop",
                )
            return await _collect_stream(resp)
        finally:
            await resp.aclose()


def _log_start(ctx: RequestContext, action: str) -> None:
    print(
        "[proxy] -> "
        f"{ctx.request_id} {ctx.model} {action} client={ctx.client} "
        f"fp={ctx.fingerprint} msgs={ctx.messages} tools={ctx.tools}"
    )


def _log_done(ctx: RequestContext, action: str, started: float, extra: str = "") -> None:
    elapsed = (time.monotonic() - started) * 1000
    suffix = f" {extra}" if extra else ""
    print(f"[proxy] <- {ctx.request_id} {ctx.model} {action} {elapsed:.0f}ms{suffix}")


async def _stream_response(
    oai: JsonDict, headers: JsonDict, schemas: dict[str, JsonDict], ctx: RequestContext
) -> AsyncIterator[str]:
    msg_id = f"msg_{uuid.uuid4().hex[:24]}"
    attempts = 1 + int(_env_bool("PROXY_TOOL_RETRY_ON_INVALID", True))
    active_oai = oai
    invalid: ToolInputError | None = None

    for attempt in range(attempts):
        result = await _collect_backend_stream(active_oai, headers)
        invalid = _invalid_stream_tool_call(result, schemas)
        if not invalid:
            async for event in _stream_events(result, ctx.model, msg_id):
                yield event
            return
        print(f"[proxy] !! {ctx.request_id} invalid tool attempt={attempt + 1}: {invalid}")
        if attempt + 1 < attempts:
            active_oai = _retry_body(oai, invalid)

    assert invalid is not None
    async for event in _diagnostic_stream(ctx.model, msg_id, invalid):
        yield event


async def _post_nonstreaming(
    oai: JsonDict, headers: JsonDict, schemas: dict[str, JsonDict], model: str
) -> JSONResponse:
    attempts = 1 + int(_env_bool("PROXY_TOOL_RETRY_ON_INVALID", True))
    active_oai = oai
    invalid: ToolInputError | None = None

    async with httpx.AsyncClient(timeout=300) as client:
        for attempt in range(attempts):
            r = await client.post(
                f"{BACKEND}/v1/chat/completions", json=active_oai, headers=headers
            )
            raw = r.text
            if not raw.strip():
                return JSONResponse(
                    {
                        "type": "error",
                        "error": {
                            "type": "api_error",
                            "message": f"Backend empty (HTTP {r.status_code})",
                        },
                    },
                    status_code=502,
                )
            if r.status_code != 200:
                return JSONResponse(
                    {
                        "type": "error",
                        "error": {
                            "type": "api_error",
                            "message": f"Backend request failed with HTTP {r.status_code}.",
                        },
                    },
                    status_code=r.status_code,
                )

            payload = r.json()
            invalid = _invalid_tool_call(payload, schemas)
            if not invalid:
                return JSONResponse(_to_anthropic(payload, model))
            if attempt + 1 < attempts:
                active_oai = _retry_body(oai, invalid)

    assert invalid is not None
    return JSONResponse(_diagnostic_response(model, invalid))
