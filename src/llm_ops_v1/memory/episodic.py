from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class Episode:
    actor: str
    action: str
    summary: str
    happened_at: datetime


class EpisodicMemory:
    def __init__(self) -> None:
        self._episodes: list[Episode] = []

    def record(self, actor: str, action: str, summary: str) -> Episode:
        episode = Episode(
            actor=actor,
            action=action,
            summary=summary,
            happened_at=datetime.now(UTC),
        )
        self._episodes.append(episode)
        return episode

    def latest(self, limit: int = 10) -> list[Episode]:
        return self._episodes[-limit:]
