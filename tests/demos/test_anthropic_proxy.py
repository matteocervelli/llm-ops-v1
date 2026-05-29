import json

import demos.anthropic_proxy as proxy


class FakeStreamResponse:
    status_code = 200

    def __init__(self, chunks):
        self._chunks = chunks

    async def aiter_lines(self):
        for chunk in self._chunks:
            yield f"data: {json.dumps(chunk)}"
        yield "data: [DONE]"


def _bash_tool():
    return {
        "name": "Bash",
        "description": "Run a shell command",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    }


async def _collect(async_iterable):
    return [item async for item in async_iterable]


def test_tool_mode_filters_schema(monkeypatch):
    monkeypatch.setenv("PROXY_TOOL_MODE", "read-only")
    tools = [
        _bash_tool(),
        {"name": "Read", "input_schema": {"type": "object"}},
        {"name": "Edit", "input_schema": {"type": "object"}},
    ]

    translated = proxy._translate_tools(tools)

    assert [tool["function"]["name"] for tool in translated] == ["Read"]


def test_oai_body_omits_tools_when_filter_removes_all(monkeypatch):
    monkeypatch.setenv("PROXY_TOOL_MODE", "none")

    oai = proxy._oai_request_body(
        {"model": "m", "tools": [_bash_tool()]},
        [{"role": "user", "content": "hi"}],
        streaming=True,
    )

    assert "tools" not in oai


def test_oai_body_injects_proxy_model_identity():
    oai = proxy._oai_request_body(
        {"model": "mlx-community/Qwen3.6-27B-OptiQ-4bit"},
        [{"role": "user", "content": "Che modello sei?"}],
        streaming=True,
    )

    assert oai["messages"][0]["role"] == "system"
    assert "mlx-community/Qwen3.6-27B-OptiQ-4bit" in oai["messages"][0]["content"]


def test_missing_required_tool_parameter_is_invalid(monkeypatch):
    monkeypatch.setenv("PROXY_TOOL_ALLOWLIST", "Bash")
    schemas = proxy._tool_schemas([_bash_tool()])

    invalid = proxy._validate_tool_input("tool_1", "Bash", "{}", schemas)

    assert invalid is not None
    assert "command" in invalid.message


def test_default_tool_repair_rejects_invalid_json():
    parsed, error = proxy._parse_json_object('Use this: {"command": "ls -la"} trailing')

    assert parsed == {}
    assert error is not None
    assert "invalid JSON" in error


def test_syntax_only_repair_extracts_json_object(monkeypatch):
    monkeypatch.setenv("PROXY_TOOL_REPAIR", "syntax-only")

    parsed, error = proxy._parse_json_object('Use this: {"command": "ls -la"} trailing')

    assert error is None
    assert parsed == {"command": "ls -la"}


def test_proxy_auth_requires_token_without_explicit_dev_mode(monkeypatch):
    monkeypatch.delenv("PROXY_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("PROXY_ALLOW_UNAUTHENTICATED", raising=False)

    assert proxy._proxy_auth_error("127.0.0.1", None, None) is not None
    assert proxy._proxy_auth_error("::1", None, None) is not None


def test_proxy_auth_allows_explicit_dev_mode(monkeypatch):
    monkeypatch.delenv("PROXY_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("PROXY_ALLOW_UNAUTHENTICATED", "true")

    assert proxy._proxy_auth_error("127.0.0.1", None, None) is None


def test_proxy_auth_requires_token_for_non_loopback_without_token(monkeypatch):
    monkeypatch.delenv("PROXY_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("PROXY_ALLOW_UNAUTHENTICATED", raising=False)

    error = proxy._proxy_auth_error("192.0.2.10", None, None)

    assert error is not None
    assert "PROXY_AUTH_TOKEN" in error


def test_proxy_auth_accepts_configured_bearer_token(monkeypatch):
    monkeypatch.setenv("PROXY_AUTH_TOKEN", "example-token")

    assert proxy._proxy_auth_error("192.0.2.10", "Bearer example-token", None) is None


def test_proxy_auth_rejects_invalid_configured_token(monkeypatch):
    monkeypatch.setenv("PROXY_AUTH_TOKEN", "example-token")

    error = proxy._proxy_auth_error("127.0.0.1", "Bearer wrong", None)

    assert error == "Missing or invalid proxy auth token."


def test_harmony_text_is_split_into_reasoning_and_visible_text():
    text = (
        "<|channel|>analysis<|message|>private notes<|end|>"
        "<|start|>assistant<|channel|>final<|message|>visible answer<|end|>"
    )

    reasoning, visible = proxy._split_harmony_text(text)

    assert reasoning == "private notes"
    assert visible == "visible answer"


def test_oai_message_translation_strips_harmony_tags_from_history():
    body = {
        "messages": [
            {
                "role": "assistant",
                "content": (
                    "<|channel|>analysis<|message|>private<|end|>"
                    "<|channel|>final<|message|>public<|end|>"
                ),
            }
        ]
    }

    messages = proxy._to_oai_messages(body)

    assert messages == [{"role": "assistant", "content": "public"}]


def test_nonstreaming_anthropic_response_strips_harmony_tags():
    response = proxy._to_anthropic(
        {
            "choices": [
                {
                    "message": {
                        "content": (
                            "<|channel|>analysis<|message|>private<|end|>"
                            "<|channel|>final<|message|>public<|end|>"
                        )
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {},
        },
        "mlx-community/gpt-oss-20b-MXFP4-Q8",
    )

    assert response["content"][0] == {"type": "thinking", "thinking": "private"}
    assert response["content"][1] == {"type": "text", "text": "public"}


async def test_collect_stream_preserves_tool_argument_chunks():
    chunks = [
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call_1",
                                "function": {"name": "Bash", "arguments": '{"command":'},
                            }
                        ]
                    }
                }
            ]
        },
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [{"index": 0, "function": {"arguments": ' "ls -la"}'}}]
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        },
    ]

    result = await proxy._collect_stream(FakeStreamResponse(chunks))
    events = await _collect(proxy._stream_events(result, "model", "msg_test"))

    assert result.tool_calls[0].arguments == '{"command": "ls -la"}'
    assert any('"type": "input_json_delta"' in event for event in events)
    assert any('"partial_json"' in event and "command" in event for event in events)


async def test_collect_stream_normalizes_harmony_text():
    chunks = [
        {
            "choices": [
                {
                    "delta": {
                        "content": (
                            "<|channel|>analysis<|message|>private<|end|>"
                            "<|channel|>final<|message|>public<|end|>"
                        )
                    },
                    "finish_reason": "stop",
                }
            ]
        },
    ]

    result = await proxy._collect_stream(FakeStreamResponse(chunks))

    assert result.reasoning == "private"
    assert result.text == "public"


async def test_stream_tool_validation_rejects_missing_required_argument(monkeypatch):
    monkeypatch.setenv("PROXY_TOOL_ALLOWLIST", "Bash")
    result = proxy.StreamResult(
        tool_calls={0: proxy.StreamToolCall("call_1", "Bash", ["{}"])},
        finish_reason="tool_calls",
    )
    schemas = proxy._tool_schemas([_bash_tool()])

    invalid = proxy._invalid_stream_tool_call(result, schemas)

    assert invalid is not None
    assert "command" in invalid.message


def test_retry_body_adds_corrective_message():
    oai = {"messages": [{"role": "user", "content": "run ls"}]}
    invalid = proxy.ToolInputError("call_1", "Bash", "required parameter(s) missing: command")

    retry = proxy._retry_body(oai, invalid)

    assert retry["messages"][-1]["role"] == "user"
    assert "Never call a tool with {}" in retry["messages"][-1]["content"]
    assert oai["messages"][-1]["content"] == "run ls"


async def test_duplicate_claim_suppresses_in_flight_request(monkeypatch):
    monkeypatch.setenv("PROXY_DEDUPE", "1")
    proxy._IN_FLIGHT.clear()

    assert await proxy._claim_request("same-fingerprint") is True
    assert await proxy._claim_request("same-fingerprint") is False

    await proxy._release_request("same-fingerprint")
    assert await proxy._claim_request("same-fingerprint") is True
    await proxy._release_request("same-fingerprint")
