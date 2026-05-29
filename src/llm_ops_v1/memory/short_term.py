from collections import defaultdict
from collections.abc import Mapping, MutableMapping
from typing import Any, Protocol, cast

from redis import Redis
from redis.exceptions import RedisError


class InMemorySessionState:
    def __init__(self) -> None:
        self._sessions: MutableMapping[str, dict[str, str]] = defaultdict(dict)

    def put(self, session_id: str, key: str, value: str) -> None:
        self._sessions[session_id][key] = value

    def get(self, session_id: str, key: str, default: str | None = None) -> str | None:
        return self._sessions[session_id].get(key, default)

    def snapshot(self, session_id: str) -> dict[str, str]:
        return dict(self._sessions[session_id])


class SessionState(Protocol):
    def put(self, session_id: str, key: str, value: str) -> None: ...

    def get(self, session_id: str, key: str, default: str | None = None) -> str | None: ...

    def snapshot(self, session_id: str) -> dict[str, str]: ...


class RedisSessionState:
    def __init__(
        self,
        redis_url: str,
        ttl_seconds: int = 86_400,
        key_prefix: str = "llm_ops_v1:session",
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero")
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self._client = Redis.from_url(redis_url, decode_responses=True)

    def put(self, session_id: str, key: str, value: str) -> None:
        redis_key = self._redis_key(session_id)
        pipeline = self._client.pipeline(transaction=True)
        pipeline.hset(redis_key, key, value)
        pipeline.expire(redis_key, self.ttl_seconds)
        pipeline.execute()

    def get(self, session_id: str, key: str, default: str | None = None) -> str | None:
        value = self._client.hget(self._redis_key(session_id), key)
        if value is None:
            return default
        return str(value)

    def snapshot(self, session_id: str) -> dict[str, str]:
        session_state = cast(
            Mapping[Any, Any],
            self._client.hgetall(self._redis_key(session_id)),
        )
        return {str(key): str(value) for key, value in session_state.items()}

    def ping(self) -> None:
        self._client.ping()

    def _redis_key(self, session_id: str) -> str:
        return f"{self.key_prefix}:{session_id}"


def create_session_state(
    redis_url: str | None = None,
    ttl_seconds: int = 86_400,
    key_prefix: str = "llm_ops_v1:session",
) -> SessionState:
    if redis_url is None:
        return InMemorySessionState()

    try:
        state = RedisSessionState(redis_url, ttl_seconds=ttl_seconds, key_prefix=key_prefix)
        state.ping()
    except RedisError:
        return InMemorySessionState()

    return state
