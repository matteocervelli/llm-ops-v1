"""Golden dataset loader for eval regression suites."""

import json
from dataclasses import dataclass
from pathlib import Path

_GOLDEN_PATH = Path(__file__).parent / "datasets" / "golden.jsonl"


@dataclass(frozen=True)
class GoldenExample:
    id: str
    prompt: str
    expected_action: str  # reply | ask_clarification | escalate
    expected_category: str
    policy: str
    notes: str


def load_golden(path: Path = _GOLDEN_PATH) -> list[GoldenExample]:
    examples = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        examples.append(
            GoldenExample(
                id=d["id"],
                prompt=d["prompt"],
                expected_action=d["expected_action"],
                expected_category=d["expected_category"],
                policy=d.get("policy", ""),
                notes=d.get("notes", ""),
            )
        )
    return examples
