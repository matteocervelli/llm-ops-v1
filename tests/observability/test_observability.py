import json
import logging

from llm_ops_v1.observability import langfuse_setup
from llm_ops_v1.observability.structured_logging import JsonFormatter, get_logger


class FakeLangfuseClient:
    def __init__(self) -> None:
        self.flushed = False

    def flush(self) -> None:
        self.flushed = True


def test_json_formatter_emits_structured_log_payload() -> None:
    record = logging.LogRecord(
        name="llm_ops_v1.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="demo event",
        args=(),
        exc_info=None,
    )

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "llm_ops_v1.test"
    assert payload["message"] == "demo event"
    assert "timestamp" in payload


def test_get_logger_is_idempotent_for_same_name() -> None:
    logger = get_logger("llm_ops_v1.tests.observability")
    handler_count = len(logger.handlers)

    same_logger = get_logger("llm_ops_v1.tests.observability")

    assert same_logger is logger
    assert len(same_logger.handlers) == handler_count
    assert same_logger.propagate is False


def test_flush_langfuse_uses_configured_client(monkeypatch) -> None:
    fake = FakeLangfuseClient()
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "public-test-key")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "secret-test-key")
    monkeypatch.setattr(langfuse_setup, "get_client", lambda: fake)

    langfuse_setup.flush_langfuse()

    assert fake.flushed is True


def test_flush_langfuse_is_noop_without_keys(monkeypatch) -> None:
    fake = FakeLangfuseClient()
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.setattr(langfuse_setup, "get_client", lambda: fake)

    langfuse_setup.flush_langfuse()

    assert fake.flushed is False
