from datetime import UTC, datetime

from llm_ops_v1.dashboard.models import DashboardRecord
from llm_ops_v1.dashboard.store import DashboardStore


def _make_record(run_id: str) -> DashboardRecord:
    return DashboardRecord(
        run_id=run_id,
        prompt_preview="test prompt",
        output_preview="test output",
        latency_ms=100.0,
        cost_usd=0.001,
        eval_score=7.0,
        action="reply",
        cache_hit=False,
        timestamp=datetime(2026, 5, 22, 9, 0, 0, tzinfo=UTC),
    )


def test_store_initialised_with_fixtures() -> None:
    records = [_make_record("r-001"), _make_record("r-002")]
    store = DashboardStore(records)
    snapshot = store.snapshot()
    assert len(snapshot) == 2
    assert {r.run_id for r in snapshot} == {"r-001", "r-002"}


def test_store_append_adds_record() -> None:
    store = DashboardStore([_make_record("r-001")])
    store.append(_make_record("r-002"))
    assert len(store.snapshot()) == 2


def test_snapshot_returns_copy() -> None:
    store = DashboardStore([_make_record("r-001")])
    snapshot = store.snapshot()
    snapshot.clear()
    assert len(store.snapshot()) == 1


def test_store_persists_records_to_json(tmp_path) -> None:
    storage_path = tmp_path / "records.json"
    store = DashboardStore.from_file(storage_path, [_make_record("fixture-001")])

    store.append(_make_record("live-001"))
    reloaded = DashboardStore.from_file(storage_path, [])

    assert [record.run_id for record in reloaded.snapshot()] == ["live-001", "fixture-001"]


def test_store_replace_persists_new_records(tmp_path) -> None:
    storage_path = tmp_path / "records.json"
    store = DashboardStore.from_file(storage_path, [_make_record("fixture-001")])

    store.replace([_make_record("fixture-reset")])
    reloaded = DashboardStore.from_file(storage_path, [])

    assert [record.run_id for record in reloaded.snapshot()] == ["fixture-reset"]
