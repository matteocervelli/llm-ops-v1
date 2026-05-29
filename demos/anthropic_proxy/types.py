"""Anthropic Messages API to OpenAI-compatible proxy demo."""

import json
import os
import re
import uuid
from dataclasses import dataclass, field
from hashlib import sha256
from ipaddress import ip_address
from typing import Any

from fastapi import Request

BACKEND = os.getenv("PROXY_BACKEND", "http://localhost:11434").rstrip("/")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")
DEFAULT_DEDUPE_WINDOW_MS = 30_000
HARMONY_MESSAGE_RE = re.compile(
    r"<\|channel\|>(?P<channel>[^<]+)<\|message\|>(?P<message>.*?)(?=<\|end\|>|$)",
    re.DOTALL,
)
HARMONY_TAG_RE = re.compile(r"<\|[^|]+\|>")

JsonDict = dict[str, Any]

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


def _is_loopback_host(host: str) -> bool:
    if host in {"localhost", "testclient"}:
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def _request_token(authorization: str | None, api_key: str | None) -> str:
    if api_key:
        return api_key
    if not authorization:
        return ""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return ""
    return token.strip()


def _proxy_auth_error(
    client_host: str, authorization: str | None, api_key: str | None
) -> str | None:
    if _env_bool("PROXY_ALLOW_UNAUTHENTICATED", False):
        return None

    expected = os.getenv("PROXY_AUTH_TOKEN", "")
    if not expected:
        return "Set PROXY_AUTH_TOKEN or PROXY_ALLOW_UNAUTHENTICATED=true for local demos."

    supplied = _request_token(authorization, api_key)
    if supplied == expected:
        return None
    return "Missing or invalid proxy auth token."


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
    mode = os.getenv("PROXY_TOOL_MODE", "none").lower()
    allowlist = set(_csv_env("PROXY_TOOL_ALLOWLIST"))
    defaults = {
        "none": set(),
        "read-only": {"Read", "Glob", "Grep", "LS"},
        "minimal": {"Read", "Glob", "Grep", "LS", "TodoWrite"},
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
        if os.getenv("PROXY_TOOL_REPAIR", "off") == "off":
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
