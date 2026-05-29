"""Langfuse observability helpers — Langfuse 3.x API.

Wraps the Langfuse 3.x client for tracing and eval score pushing.
If LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY are not set, all calls
are no-ops so the app works offline without errors.

Langfuse 3.x changes vs 2.x:
- `@observe` is now at `langfuse.observe`, not `langfuse.decorators.observe`
- `langfuse_context` is at `langfuse.langfuse_context`
- `Langfuse().trace()` is removed; use `get_client()` methods
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any


def _langfuse_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


# Module-level reference so tests can monkeypatch langfuse_setup.get_client.
try:
    from langfuse import get_client  # type: ignore[import-untyped]
except ImportError:

    def get_client() -> None:  # type: ignore[misc]
        return None


def get_langfuse_client() -> Any:
    if not _langfuse_enabled():
        return None
    try:
        return get_client()
    except Exception:
        return None


def flush_langfuse() -> None:
    """Flush Langfuse traces (works across v2 and v3).

    v3: @observe uses an OTEL exporter; flush via the decorator singleton.
    Fallback: call get_client().flush() — used by tests and v2 compatibility.
    """
    try:
        from langfuse import observe as _lf_observe  # type: ignore[import-untyped]

        decorator_obj: Any = _lf_observe.__self__  # type: ignore[attr-defined]
        if hasattr(decorator_obj, "flush"):
            decorator_obj.flush()
    except Exception:
        return
    # Fallback path (also used by tests that monkeypatch get_client).
    client = get_langfuse_client()
    if client is not None:
        try:
            client.flush()
        except Exception:
            return


def observe(name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that creates a Langfuse trace span (Langfuse 3.x API).

    Falls back to no-op if Langfuse is not configured or unavailable.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        if not _langfuse_enabled():
            return fn
        try:
            from langfuse import observe as _lf_observe  # type: ignore[import-untyped]

            return _lf_observe(name=name or fn.__name__)(fn)
        except Exception:
            return fn

    return decorator


def push_eval_score(
    trace_id: str,
    name: str,
    score: float,
    comment: str = "",
) -> None:
    """Push an eval score to the current Langfuse trace. No-op if not configured."""
    if not _langfuse_enabled():
        return
    try:
        from langfuse import langfuse_context  # type: ignore[import-untyped]

        langfuse_context.score_current_observation(name=name, value=score, comment=comment)
    except Exception:
        return


def create_trace(name: str, metadata: dict[str, Any] | None = None) -> Any:
    """No-op in Langfuse 3.x — traces are created automatically by @observe."""
    return None
