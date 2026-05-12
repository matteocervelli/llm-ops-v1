#!/usr/bin/env bash
# Smoke-test all three alternative model backends before the live demo.
# Run from the repo root: bash demos/test-alternative-models.sh
set -euo pipefail

OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
MLX_URL="${MLX_BASE_URL:-http://localhost:8080/v1}"
PASS=0
FAIL=0

ok()   { echo "  [OK]  $*"; ((PASS++)) || true; }
fail() { echo "  [!!]  $*"; ((FAIL++)) || true; }

# ── Ollama ──────────────────────────────────────────────────────────────────
echo ""
echo "=== Ollama ($OLLAMA_URL) ==="

if curl -sf "$OLLAMA_URL/api/tags" -o /tmp/ollama-tags.json; then
    ok "server reachable"
    AVAILABLE=$(python3 -c "import json; d=json.load(open('/tmp/ollama-tags.json')); print(' '.join(m['name'] for m in d['models']))")
    echo "  available: $AVAILABLE"
    for MODEL in "qwen3.6:27b" "qwen3.6:35b-a3b"; do
        if echo "$AVAILABLE" | grep -qi "$MODEL"; then
            ok "model $MODEL"
        else
            fail "model $MODEL missing — run: ollama pull $MODEL"
        fi
    done
else
    fail "server not reachable — run: OLLAMA_HOST=0.0.0.0 ollama serve"
fi

# ── MLX ─────────────────────────────────────────────────────────────────────
echo ""
echo "=== MLX ($MLX_URL) ==="

if curl -sf "$MLX_URL/models" -o /tmp/mlx-models.json; then
    LOADED=$(python3 -c "import json; d=json.load(open('/tmp/mlx-models.json')); print(d['data'][0]['id'] if d['data'] else 'none')" 2>/dev/null || echo "unknown")
    ok "server reachable — model: $LOADED"
else
    fail "server not reachable — start with:"
    echo "         mlx_lm.server --model mlx-community/Qwen3.6-27B-OptiQ-4bit --host 0.0.0.0 --port 8080"
fi

# ── OpenRouter ───────────────────────────────────────────────────────────────
echo ""
echo "=== OpenRouter ==="

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
    fail "OPENROUTER_API_KEY not set"
else
    if curl -sf -H "Authorization: Bearer $OPENROUTER_API_KEY" \
       "https://openrouter.ai/api/v1/models" -o /dev/null; then
        ok "API key valid — model: deepseek/deepseek-v4-flash"
    else
        fail "API key invalid or OpenRouter unreachable"
    fi
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "=== Result: $PASS passed, $FAIL failed ==="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
