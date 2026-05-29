from llm_ops_v1.memory.episodic import EpisodicMemory
from llm_ops_v1.memory.long_term import InMemoryVectorStore, MemoryChunk
from llm_ops_v1.memory.short_term import InMemorySessionState


def test_session_state_is_isolated_by_session() -> None:
    state = InMemorySessionState()

    state.put("session-a", "topic", "routing")
    state.put("session-b", "topic", "memory")

    assert state.get("session-a", "topic") == "routing"
    assert state.get("session-b", "topic") == "memory"
    assert state.get("session-a", "missing", "fallback") == "fallback"


def test_session_snapshot_is_a_copy() -> None:
    state = InMemorySessionState()
    state.put("session-a", "topic", "routing")

    snapshot = state.snapshot("session-a")
    snapshot["topic"] = "changed"

    assert state.get("session-a", "topic") == "routing"


def test_vector_store_returns_most_similar_chunks_first() -> None:
    store = InMemoryVectorStore()
    first = MemoryChunk("first", "close match", [1.0, 0.0], {"kind": "demo"})
    second = MemoryChunk("second", "distant match", [0.0, 1.0], {"kind": "demo"})
    store.add(second)
    store.add(first)

    results = store.search([0.9, 0.1], limit=1)

    assert results == [first]


def test_vector_store_handles_zero_vector_queries() -> None:
    store = InMemoryVectorStore()
    chunk = MemoryChunk("chunk", "content", [1.0, 0.0], {})
    store.add(chunk)

    assert store.search([0.0, 0.0]) == [chunk]


def test_episodic_memory_records_timestamped_events() -> None:
    memory = EpisodicMemory()

    first = memory.record("agent", "searched", "Found provider docs")
    second = memory.record("agent", "summarized", "Wrote comparison")

    assert first.actor == "agent"
    assert first.happened_at.tzinfo is not None
    assert memory.latest(limit=1) == [second]


def test_episodic_memory_filters_latest_events_by_actor() -> None:
    memory = EpisodicMemory()

    first = memory.record("customer-123", "opened_ticket", "Package missing.")
    memory.record("customer-999", "opened_ticket", "Billing question.")
    second = memory.record("customer-123", "opened_ticket", "Package still missing.")

    assert memory.latest_for_actor("customer-123", limit=2) == [first, second]
    assert memory.latest_for_actor("customer-999", limit=0) == []
