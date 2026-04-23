import math
from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryChunk:
    memory_id: str
    content: str
    embedding: list[float]
    metadata: dict[str, str]


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._chunks: list[MemoryChunk] = []

    def add(self, chunk: MemoryChunk) -> None:
        self._chunks.append(chunk)

    def search(self, query_embedding: list[float], limit: int = 5) -> list[MemoryChunk]:
        ranked = sorted(
            self._chunks,
            key=lambda chunk: _cosine_similarity(chunk.embedding, query_embedding),
            reverse=True,
        )
        return ranked[:limit]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    numerator = sum(left * right for left, right in zip(a, b, strict=False))
    left_norm = math.sqrt(sum(value * value for value in a))
    right_norm = math.sqrt(sum(value * value for value in b))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
