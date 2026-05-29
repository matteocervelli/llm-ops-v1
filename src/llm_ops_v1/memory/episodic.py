import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from redis import Redis


@dataclass(frozen=True)
class Episode:
    actor: str
    action: str
    summary: str
    happened_at: datetime


class EpisodicMemory:
    def __init__(
        self,
        redis_url: str | None = None,
        ttl_seconds: int = 604_800,
        key_prefix: str = "llm_ops_v1:episodic",
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero")
        self._episodes: list[Episode] = []
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self._client: Redis | None = None
        if redis_url is not None:
            self._client = Redis.from_url(redis_url, decode_responses=True)

    def record(self, actor: str, action: str, summary: str) -> Episode:
        episode = Episode(
            actor=actor,
            action=action,
            summary=summary,
            happened_at=datetime.now(UTC),
        )
        if self._client is None:
            self._episodes.append(episode)
        else:
            self._record_redis(episode)
        return episode

    def latest(self, limit: int = 10) -> list[Episode]:
        if limit <= 0:
            return []
        if self._client is not None:
            return self._latest_redis(self._global_key(), limit)
        return self._episodes[-limit:]

    def latest_for_actor(self, actor: str, limit: int = 10) -> list[Episode]:
        if limit <= 0:
            return []
        if self._client is not None:
            return self._latest_redis(self._actor_key(actor), limit)
        return [episode for episode in self._episodes if episode.actor == actor][-limit:]

    def _record_redis(self, episode: Episode) -> None:
        if self._client is None:
            raise RuntimeError("Redis client is not configured")

        global_key = self._global_key()
        actor_key = self._actor_key(episode.actor)
        payload = _episode_to_json(episode)
        pipeline = self._client.pipeline(transaction=True)
        pipeline.rpush(global_key, payload)
        pipeline.rpush(actor_key, payload)
        pipeline.expire(global_key, self.ttl_seconds)
        pipeline.expire(actor_key, self.ttl_seconds)
        pipeline.execute()

    def _latest_redis(self, key: str, limit: int) -> list[Episode]:
        if self._client is None:
            raise RuntimeError("Redis client is not configured")

        entries = cast(list[Any], self._client.lrange(key, -limit, -1))
        return [_episode_from_json(str(entry)) for entry in entries]

    def _global_key(self) -> str:
        return f"{self.key_prefix}:global"

    def _actor_key(self, actor: str) -> str:
        actor_hash = hashlib.sha256(actor.encode("utf-8")).hexdigest()
        return f"{self.key_prefix}:actor:{actor_hash}"


def _episode_to_json(episode: Episode) -> str:
    return json.dumps(
        {
            "actor": episode.actor,
            "action": episode.action,
            "summary": episode.summary,
            "happened_at": episode.happened_at.isoformat(),
        },
        separators=(",", ":"),
    )


def _episode_from_json(payload: str) -> Episode:
    try:
        data = cast(Mapping[str, Any], json.loads(payload))
        happened_at = datetime.fromisoformat(str(data["happened_at"]))
        if happened_at.tzinfo is None:
            happened_at = happened_at.replace(tzinfo=UTC)
        return Episode(
            actor=str(data["actor"]),
            action=str(data["action"]),
            summary=str(data["summary"]),
            happened_at=happened_at.astimezone(UTC),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Malformed episodic memory entry") from exc
