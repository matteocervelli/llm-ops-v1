"""Tests for response_cache — InMemory backend (no Redis required)."""

import asyncio

import pytest

from llm_ops_v1.caching.response_cache import InMemoryCache, ResponseCache, make_response_key


def test_make_response_key_stable() -> None:
    k1 = make_response_key("system", ["p1", "p2"], "ticket text", "haiku")
    k2 = make_response_key("system", ["p1", "p2"], "ticket text", "haiku")
    assert k1 == k2


def test_make_response_key_differs_by_model() -> None:
    k1 = make_response_key("sys", [], "ticket", "haiku")
    k2 = make_response_key("sys", [], "ticket", "sonnet")
    assert k1 != k2


def test_make_response_key_differs_by_ticket() -> None:
    k1 = make_response_key("sys", [], "ticket A", "haiku")
    k2 = make_response_key("sys", [], "ticket B", "haiku")
    assert k1 != k2


def test_make_response_key_normalises_whitespace() -> None:
    k1 = make_response_key("sys", [], "hello  world", "m")
    k2 = make_response_key("sys", [], "hello world", "m")
    assert k1 == k2


@pytest.mark.asyncio
async def test_inmemory_miss_returns_none() -> None:
    cache = ResponseCache(InMemoryCache())
    assert await cache.get("missing-key") is None


@pytest.mark.asyncio
async def test_inmemory_set_and_get() -> None:
    cache = ResponseCache(InMemoryCache())
    await cache.set("k1", "response text")
    assert await cache.get("k1") == "response text"


@pytest.mark.asyncio
async def test_inmemory_ttl_expiry() -> None:
    cache = ResponseCache(InMemoryCache())
    await cache.set("k2", "expires soon", ttl_seconds=0)
    await asyncio.sleep(0.01)
    # TTL=0 means immediate expiry; should be gone
    assert await cache.get("k2") is None


@pytest.mark.asyncio
async def test_inmemory_overwrite() -> None:
    cache = ResponseCache(InMemoryCache())
    await cache.set("k3", "first")
    await cache.set("k3", "second")
    assert await cache.get("k3") == "second"
