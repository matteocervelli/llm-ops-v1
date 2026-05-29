#!/usr/bin/env bash
set -euo pipefail

WEBHOOK_URL="${WEBHOOK_URL:-http://127.0.0.1:8000/webhook/ticket}"
BACKEND="${BACKEND:-${LLM_OPS_WEBHOOK_DEFAULT_BACKEND:-pydantic_ai}}"
SUBJECT="${SUBJECT:-Il mio ordine e in ritardo}"
BODY="${BODY:-La pagina tracking non si aggiorna da due giorni.}"
export BACKEND BODY SUBJECT

payload=$(
  uv run python - <<'PY'
import json
import os

print(
    json.dumps(
        {
            "subject": os.environ["SUBJECT"],
            "body": os.environ["BODY"],
            "backend": os.environ["BACKEND"],
        }
    )
)
PY
)

headers=(-H "Content-Type: application/json")
if [[ -n "${LLM_OPS_WEBHOOK_TOKEN:-}" ]]; then
  headers+=(-H "Authorization: Bearer ${LLM_OPS_WEBHOOK_TOKEN}")
fi

curl -sS -X POST "${WEBHOOK_URL}" "${headers[@]}" -d "${payload}"
