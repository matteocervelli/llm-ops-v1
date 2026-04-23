from collections import defaultdict
from collections.abc import MutableMapping


class InMemorySessionState:
    def __init__(self) -> None:
        self._sessions: MutableMapping[str, dict[str, str]] = defaultdict(dict)

    def put(self, session_id: str, key: str, value: str) -> None:
        self._sessions[session_id][key] = value

    def get(self, session_id: str, key: str, default: str | None = None) -> str | None:
        return self._sessions[session_id].get(key, default)

    def snapshot(self, session_id: str) -> dict[str, str]:
        return dict(self._sessions[session_id])


class RedisSessionState:
    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url

    def put(self, session_id: str, key: str, value: str) -> None:
        raise NotImplementedError("Add a real Redis adapter when you choose your runtime.")
