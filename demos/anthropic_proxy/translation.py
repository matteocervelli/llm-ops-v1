"""Anthropic Messages API to OpenAI-compatible proxy demo."""

import json
import uuid

from .types import (
    JsonDict,
    ToolInputError,
    _diagnostic_text,
    _parse_json_object,
    _sanitize_content_text,
    _split_harmony_text,
    _text,
    _translate_tools,
    _with_proxy_identity,
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
