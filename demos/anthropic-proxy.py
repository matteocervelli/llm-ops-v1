#!/usr/bin/env python3
"""
Minimal Anthropic Messages API -> OpenAI-compat proxy.
No LiteLLM. Translates /v1/messages -> /v1/chat/completions (Ollama, MLX, OpenRouter).
Handles tools, tool_use, tool_result, streaming tool_calls.

Usage:
    PROXY_BACKEND=http://localhost:11434 uv run uvicorn demos.anthropic-proxy:app --port 4000
    PROXY_BACKEND=https://openrouter.ai/api \
        PROXY_API_KEY=$OPENROUTER_API_KEY \
        uv run uvicorn demos.anthropic-proxy:app --port 4002

Claude Code:
    ANTHROPIC_BASE_URL=http://localhost:4000 ANTHROPIC_AUTH_TOKEN=proxy claude --model gpt-oss:20b
"""

import json
import os
import re
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

BACKEND = os.getenv("PROXY_BACKEND", "http://localhost:11434").rstrip("/")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")
DEFAULT_DEDUPE_WINDOW_MS = 30_000
HARMONY_MESSAGE_RE = re.compile(
    r"<\|channel\|>(?P<channel>[^<]+)<\|message\|>(?P<message>.*?)(?=<\|end\|>|$)",
    re.DOTALL,
)
HARMONY_TAG_RE = re.compile(r"<\|[^|]+\|>")

JsonDict = dict[str, Any]

app = FastAPI()

_IN_FLIGHT: dict[str, float] = {}


@dataclass
class RequestContext:
    request_id: str
    model: str
    streaming: bool
    fingerprint: str
    client: str
    messages: int
    tools: int


@dataclass
class ToolInputError:
    tool_id: str
    tool_name: str
    message: str


@dataclass
class StreamToolCall:
    tool_id: str = ""
    name: str = ""
    argument_chunks: list[str] = field(default_factory=list)

    @property
    def arguments(self) -> str:
        return "".join(self.argument_chunks)


@dataclass
class StreamResult:
    reasoning: str = ""
    text: str = ""
    tool_calls: dict[int, StreamToolCall] = field(default_factory=dict)
    finish_reason: str = "stop"
    output_tokens: int = 0


# ── Format translation helpers ────────────────────────────────────────────────


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if b.get("type") == "text")
    return ""


def _split_harmony_text(text: str) -> tuple[str, str]:
    if "<|channel|>" not in text:
        return "", text

    reasoning_parts: list[str] = []
    visible_parts: list[str] = []
    for match in HARMONY_MESSAGE_RE.finditer(text):
        channel = match.group("channel").strip()
        message = HARMONY_TAG_RE.sub("", match.group("message")).strip()
        if not message:
            continue
        if channel == "analysis":
            reasoning_parts.append(message)
        elif channel in {"commentary", "final"}:
            visible_parts.append(message)

    if visible_parts:
        return "\n\n".join(reasoning_parts), "\n\n".join(visible_parts)
    return "\n\n".join(reasoning_parts), HARMONY_TAG_RE.sub("", text).strip()


def _sanitize_content_text(text: str) -> str:
    _, visible = _split_harmony_text(text)
    return visible


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _csv_env(name: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


def _request_fingerprint(body: JsonDict) -> str:
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(encoded.encode()).hexdigest()[:16]


def _request_context(
    request: Request, body: JsonDict, oai_messages: list[JsonDict]
) -> RequestContext:
    client = request.client
    client_addr = f"{client.host}:{client.port}" if client else "unknown"
    return RequestContext(
        request_id=f"req_{uuid.uuid4().hex[:10]}",
        model=body.get("model", "gpt-oss:20b"),
        streaming=bool(body.get("stream", False)),
        fingerprint=_request_fingerprint(body),
        client=client_addr,
        messages=len(oai_messages),
        tools=len(body.get("tools") or []),
    )


def _is_suppressed_model(model: str) -> bool:
    return any(model.startswith(prefix) for prefix in _csv_env("SUPPRESS_MODELS"))


def _filter_tools(tools: list[JsonDict]) -> list[JsonDict]:
    mode = os.getenv("PROXY_TOOL_MODE", "full").lower()
    allowlist = set(_csv_env("PROXY_TOOL_ALLOWLIST"))
    defaults = {
        "none": set(),
        "read-only": {"Read", "Glob", "Grep", "LS", "Bash"},
        "minimal": {"Read", "Glob", "Grep", "LS", "Bash", "Edit", "Write", "TodoWrite"},
    }
    allowed = allowlist or defaults.get(mode)
    if allowed is None:
        return tools
    return [tool for tool in tools if tool.get("name") in allowed]


def _translate_tools(tools: list) -> list:
    """Anthropic tool defs -> OpenAI function defs."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
            },
        }
        for t in _filter_tools(tools)
    ]


def _tool_schemas(tools: list[JsonDict]) -> dict[str, JsonDict]:
    return {
        tool["name"]: tool.get("input_schema", {"type": "object", "properties": {}})
        for tool in _filter_tools(tools)
        if tool.get("name")
    }


def _required_fields(schema: JsonDict | None) -> list[str]:
    if not schema:
        return []
    required = schema.get("required") or []
    return [field for field in required if isinstance(field, str)]


def _parse_json_object(raw: Any) -> tuple[JsonDict, str | None]:
    if isinstance(raw, dict):
        return raw, None
    if raw in (None, ""):
        return {}, None
    if not isinstance(raw, str):
        return {}, "tool arguments are not a JSON object"

    candidate = raw.strip()
    if candidate.startswith("```"):
        lines = [line for line in candidate.splitlines() if not line.strip().startswith("```")]
        candidate = "\n".join(lines).strip()

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        if os.getenv("PROXY_TOOL_REPAIR", "syntax-only") == "off":
            return {}, f"tool arguments are invalid JSON: {exc.msg}"
        start = candidate.find("{")
        if start == -1:
            return {}, f"tool arguments are invalid JSON: {exc.msg}"
        try:
            parsed, _ = json.JSONDecoder().raw_decode(candidate[start:])
        except json.JSONDecodeError as repair_exc:
            return {}, f"tool arguments are invalid JSON: {repair_exc.msg}"

    if not isinstance(parsed, dict):
        return {}, "tool arguments must decode to a JSON object"
    return parsed, None


def _validate_tool_input(
    tool_id: str, tool_name: str, raw_arguments: Any, schemas: dict[str, JsonDict]
) -> ToolInputError | None:
    if schemas and tool_name not in schemas:
        return ToolInputError(tool_id, tool_name, "tool was not offered by the proxy")

    parsed, parse_error = _parse_json_object(raw_arguments)
    if parse_error:
        return ToolInputError(tool_id, tool_name, parse_error)

    missing = [field for field in _required_fields(schemas.get(tool_name)) if field not in parsed]
    if missing:
        fields = ", ".join(missing)
        return ToolInputError(tool_id, tool_name, f"required parameter(s) missing: {fields}")
    return None


def _invalid_tool_call(oai: JsonDict, schemas: dict[str, JsonDict]) -> ToolInputError | None:
    for choice in oai.get("choices", []):
        msg = choice.get("message") or {}
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function") or {}
            invalid = _validate_tool_input(
                tc.get("id", ""),
                fn.get("name", ""),
                fn.get("arguments", ""),
                schemas,
            )
            if invalid:
                return invalid
    return None


def _invalid_stream_tool_call(
    result: StreamResult, schemas: dict[str, JsonDict]
) -> ToolInputError | None:
    for tc in result.tool_calls.values():
        invalid = _validate_tool_input(tc.tool_id, tc.name, tc.arguments, schemas)
        if invalid:
            return invalid
    return None


def _retry_body(oai: JsonDict, invalid: ToolInputError) -> JsonDict:
    corrective = (
        "The previous tool call was invalid: "
        f"{invalid.tool_name} {invalid.message}. Retry once. "
        "If you call a tool, provide a complete JSON object matching its schema. "
        "Never call a tool with {} when required parameters exist."
    )
    return {**oai, "messages": [*oai["messages"], {"role": "user", "content": corrective}]}


def _with_proxy_identity(messages: list[JsonDict], model: str) -> list[JsonDict]:
    if not _env_bool("PROXY_INJECT_MODEL_ID", True):
        return messages

    identity = (
        "Proxy metadata: this Claude Code compatibility session is backed by the "
        f"upstream model `{model}`. If the user asks which model you are, answer "
        "with this upstream model id. Do not claim to be Claude or Anthropic unless "
        "the upstream model id itself is a Claude model."
    )
    return [{"role": "system", "content": identity}, *messages]


def _diagnostic_text(invalid: ToolInputError) -> str:
    return (
        "[proxy] Blocked malformed tool call from upstream model: "
        f"{invalid.tool_name} ({invalid.message}). "
        "Retry with a stronger tool-calling model, fewer Claude Code tools, or text-only mode."
    )


def _to_oai_messages(body: dict) -> list[dict]:
    msgs: list[dict] = []
    system = body.get("system")
    if system:
        msgs.append(
            {
                "role": "system",
                "content": _sanitize_content_text(
                    _text(system) if isinstance(system, list) else system
                ),
            }
        )

    for m in body.get("messages", []):
        role, content = m["role"], m["content"]
        if isinstance(content, str):
            msgs.append({"role": role, "content": _sanitize_content_text(content)})
            continue

        tool_results = [b for b in content if b.get("type") == "tool_result"]
        tool_uses = [b for b in content if b.get("type") == "tool_use"]

        if tool_results:
            # user message containing tool results → one "tool" message per result
            for tr in tool_results:
                rc = tr.get("content", "")
                msgs.append(
                    {
                        "role": "tool",
                        "tool_call_id": tr["tool_use_id"],
                        "content": _sanitize_content_text(
                            _text(rc) if isinstance(rc, list) else rc
                        ),
                    }
                )
        elif tool_uses:
            # assistant message with tool calls
            tc_list = [
                {
                    "id": tu["id"],
                    "type": "function",
                    "function": {"name": tu["name"], "arguments": json.dumps(tu.get("input", {}))},
                }
                for tu in tool_uses
            ]
            text_parts = [b.get("text", "") for b in content if b.get("type") == "text"]
            msgs.append(
                {
                    "role": "assistant",
                    "content": _sanitize_content_text(" ".join(text_parts)) or None,
                    "tool_calls": tc_list,
                }
            )
        else:
            msgs.append({"role": role, "content": _sanitize_content_text(_text(content))})
    return msgs


def _stop_reason(finish: str) -> str:
    return {"tool_calls": "tool_use", "length": "max_tokens"}.get(finish, "end_turn")


def _to_anthropic(oai: dict, model: str) -> dict:
    choice = oai["choices"][0]
    msg = choice["message"]
    finish = choice.get("finish_reason", "stop")
    usage = oai.get("usage", {})

    content = []
    content_reasoning, visible_text = _split_harmony_text(msg.get("content") or "")
    reasoning = "\n\n".join(
        part for part in [msg.get("reasoning") or "", content_reasoning] if part
    )
    if reasoning:
        content.append({"type": "thinking", "thinking": reasoning})
    if visible_text:
        content.append({"type": "text", "text": visible_text})
    for tc in msg.get("tool_calls") or []:
        fn = tc["function"]
        inp, _ = _parse_json_object(fn.get("arguments", ""))
        content.append({"type": "tool_use", "id": tc["id"], "name": fn["name"], "input": inp})
    if not content:
        content = [{"type": "text", "text": ""}]

    return {
        "id": f"msg_{uuid.uuid4().hex[:24]}",
        "type": "message",
        "role": "assistant",
        "content": content,
        "model": model,
        "stop_reason": _stop_reason(finish),
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }


def _diagnostic_response(model: str, invalid: ToolInputError) -> JsonDict:
    return {
        "id": f"msg_{uuid.uuid4().hex[:24]}",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": _diagnostic_text(invalid)}],
        "model": model,
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 0, "output_tokens": 0},
    }


def _empty_message(model: str) -> JsonDict:
    return {
        "id": f"msg_{uuid.uuid4().hex[:24]}",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": ""}],
        "model": model,
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 0, "output_tokens": 0},
    }


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


async def _collect_stream(resp: httpx.Response) -> StreamResult:
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


def _oai_request_body(body: JsonDict, messages: list[JsonDict], streaming: bool) -> JsonDict:
    tools = body.get("tools") or []
    translated_tools = _translate_tools(tools)
    model = body.get("model", "gpt-oss:20b")
    return {
        "model": model,
        "messages": _with_proxy_identity(messages, model),
        "max_tokens": body.get("max_tokens", 4096),
        "temperature": body.get("temperature", 0.0),
        "stream": streaming,
        **({"stop": body["stop_sequences"]} if body.get("stop_sequences") else {}),
        **({"tools": translated_tools} if translated_tools else {}),
    }


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
                            "message": f"Backend {r.status_code}: {raw[:200]}",
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


# -- Endpoints -----------------------------------------------------------------


@app.post("/v1/messages")
async def messages(request: Request):
    body = await request.json()
    streaming = bool(body.get("stream", False))
    oai_messages = _to_oai_messages(body)
    ctx = _request_context(request, body, oai_messages)
    schemas = _tool_schemas(body.get("tools") or [])
    oai = _oai_request_body(body, oai_messages, streaming)
    headers = {"Authorization": f"Bearer {PROXY_API_KEY}"} if PROXY_API_KEY else {}
    t0 = time.monotonic()

    if _is_suppressed_model(ctx.model):
        _log_start(ctx, "suppressed")
        if streaming:
            return StreamingResponse(
                _empty_stream(ctx.model, f"msg_{uuid.uuid4().hex[:24]}"),
                media_type="text/event-stream",
            )
        return JSONResponse(_empty_message(ctx.model))

    if not await _claim_request(ctx.fingerprint):
        _log_start(ctx, "duplicate-suppressed")
        if streaming:
            return StreamingResponse(
                _empty_stream(ctx.model, f"msg_{uuid.uuid4().hex[:24]}"),
                media_type="text/event-stream",
            )
        return JSONResponse(_empty_message(ctx.model))

    if streaming:
        _log_start(ctx, "stream")

        async def generate() -> AsyncIterator[str]:
            try:
                async for chunk in _stream_response(oai, headers, schemas, ctx):
                    yield chunk
            finally:
                await _release_request(ctx.fingerprint)
                _log_done(ctx, "stream", t0)

        return StreamingResponse(generate(), media_type="text/event-stream")

    _log_start(ctx, "no-stream")
    try:
        response = await _post_nonstreaming(oai, headers, schemas, ctx.model)
    finally:
        await _release_request(ctx.fingerprint)
        _log_done(ctx, "no-stream", t0)
    return response


@app.post("/v1/messages/count_tokens")
async def count_tokens(request: Request):
    body = await request.json()
    total = sum(len(_text(m.get("content", ""))) for m in body.get("messages", []))
    return JSONResponse({"input_tokens": max(1, total // 4)})


@app.get("/v1/models")
async def list_models():
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{BACKEND}/v1/models")
            return JSONResponse(r.json())
        except Exception:
            return JSONResponse({"object": "list", "data": []})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PROXY_PORT", "4000")))
