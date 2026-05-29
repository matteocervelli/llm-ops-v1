import json
from pathlib import Path

from llm_ops_v1.dashboard.models import DashboardRecord


class DashboardStore:
    def __init__(
        self,
        seed: list[DashboardRecord],
        storage_path: Path | None = None,
    ) -> None:
        self._records: list[DashboardRecord] = list(seed)
        self._storage_path = storage_path

    def append(self, record: DashboardRecord) -> None:
        self._records.append(record)
        self.persist()

    def replace(self, records: list[DashboardRecord]) -> None:
        self._records = list(records)
        self.persist()

    def snapshot(self) -> list[DashboardRecord]:
        return list(reversed(self._records))

    def persist(self) -> None:
        if self._storage_path is None:
            return
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [record.to_dict() for record in self._records]
        self._storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def from_file(
        cls,
        storage_path: Path,
        seed: list[DashboardRecord],
    ) -> "DashboardStore":
        if storage_path.exists():
            try:
                payload = json.loads(storage_path.read_text(encoding="utf-8"))
                records = [DashboardRecord.from_dict(item) for item in payload]
                return cls(records, storage_path=storage_path)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                corrupt_path = storage_path.with_suffix(".corrupt.json")
                storage_path.replace(corrupt_path)

        store = cls(seed, storage_path=storage_path)
        store.persist()
        return store
