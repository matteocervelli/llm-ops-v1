"""Anthropic Messages API to OpenAI-compatible proxy demo."""

import os
import time
import uuid
from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .streaming import (
    _claim_request,
    _empty_stream,
    _log_done,
    _log_start,
    _post_nonstreaming,
    _release_request,
    _stream_response,
)
from .translation import _empty_message, _oai_request_body, _to_oai_messages
from .types import (
    BACKEND,
    PROXY_API_KEY,
    _is_suppressed_model,
    _proxy_auth_error,
    _request_context,
    _text,
    _tool_schemas,
)

app = FastAPI()


@app.middleware("http")
async def require_proxy_auth(request: Request, call_next):
    client_host = request.client.host if request.client else ""
    error = _proxy_auth_error(
        client_host,
        request.headers.get("authorization"),
        request.headers.get("x-api-key"),
    )
    if error:
        return JSONResponse(
            {
                "type": "error",
                "error": {"type": "authentication_error", "message": error},
            },
            status_code=401,
        )
    return await call_next(request)


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

    uvicorn.run(
        app,
        host=os.getenv("PROXY_HOST", "127.0.0.1"),
        port=int(os.getenv("PROXY_PORT", "4000")),
    )
