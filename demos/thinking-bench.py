#!/usr/bin/env python3
"""
Thinking budget benchmark — gpt-oss on Ollama+MLX, gemma4 on Ollama only.

Usage:
    uv run python demos/thinking-bench.py
"""

import asyncio
import os
import re
import time

import httpx

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MLX_BASE = os.getenv("MLX_BASE_URL", "http://studio4change.siamese-dominant.ts.net:8080/v1")

SYSTEM = """\
You are a senior Python engineer on a production LLM gateway team.
Stack: Python 3.12+, asyncio. Rules: type hints everywhere, no bare except, \
asyncio.Lock for any shared mutable state, max 130 lines. Return only code.\
"""

# Adaptive retry policy — no standard pattern exists for this specific combination.
# The model must invent formulas and justify them; think budget should matter here.
PROMPT = """\
Our LLM gateway is hitting thundering-herd failures under burst load. Standard
exponential backoff makes it worse because all clients retry in sync.

Implement `SmartRetryPolicy` with a single public method:

    async def next_wait_ms(
        self,
        error_type: str,          # "429" | "502" | "timeout" | other
        attempt: int,             # 0-based, current attempt number
    ) -> float

Rules you must follow:
1. Each error type uses a DIFFERENT base formula — 429 is quota (predictable recovery),
   502 is backend overload (unpredictable), timeout is unknown (could be slow or dead).
   The formulas must reflect these different failure modes.
2. Maintain a rolling 5-minute window of recent (timestamp, error_type, wait_ms, succeeded: bool)
   records. From this window compute a `_congestion_score() -> float` in [0.0, 1.0]:
   0 = no pressure, 1 = saturated. Define your own formula for the score.
3. Add jitter that is PROPORTIONAL to congestion_score: more congestion → wider spread,
   so clients desynchronise faster under load. Low congestion → tight jitter (fast recovery).
4. Record each call result via `record(error_type, wait_ms, succeeded: bool)`.
5. asyncio.Lock around the window.
6. At the top of the file, a 3-line comment block that states:
   - your formula for each error type
   - your congestion_score formula
   - your jitter strategy
   Justify briefly (one clause per line).\
"""

# Each entry: (label, backend, model, think)
# backend: "ollama" -> /api/chat native   "openai" -> /v1/chat/completions
# think: "low"/"medium"/"high"/True/False/None
TESTS = [
    ("ollama gpt-oss low", "ollama", "gpt-oss:20b", "low"),
    ("ollama gpt-oss medium", "ollama", "gpt-oss:20b", "medium"),
    ("ollama gpt-oss high", "ollama", "gpt-oss:20b", "high"),
    ("mlx    gpt-oss", "openai", "mlx-community/gpt-oss-20b-MXFP4-Q8", None),
    ("ollama gemma4", "ollama", "gemma4:31b", None),
]


def _quality(content: str) -> tuple[str, int]:
    # Does it differentiate the three error types with distinct formulas?
    has_error_diff = content.count('"429"') + content.count("'429'") > 0 and (
        content.count('"502"') + content.count("'502'") > 0
    )
    # Does it implement a rolling time window (not just a counter)?
    has_window = "time.time" in content or "monotonic" in content or "deque" in content
    # Does it define a congestion score?
    has_congestion = "congestion" in content.lower()
    # Is jitter explicitly tied to congestion (not just random.uniform fixed range)?
    has_adaptive_jitter = "congestion" in content.lower() and (
        "jitter" in content.lower() or "random" in content.lower()
    )
    # Does it justify choices with comments (formula comment block)?
    has_justification = content.count("#") >= 5
    checks = [has_error_diff, has_window, has_congestion, has_adaptive_jitter, has_justification]
    score = sum(checks)
    labels = ["err_diff", "window", "cong_score", "adapt_jitter", "justified"]
    parts = " ".join(f"{'✓' if ok else '✗'}{lbl}" for ok, lbl in zip(checks, labels, strict=True))
    return f"{score}/5 {parts}", score


def _strip_mlx_thinking(content: str) -> tuple[str, str]:
    """Extract thinking and final answer from MLX gpt-oss channel format."""
    thinking_match = re.search(r"<\|channel\|>analysis<\|message\|>(.*?)<\|end\|>", content, re.S)
    final_match = re.search(r"<\|channel\|>final<\|message\|>(.*?)$", content, re.S)
    thinking = thinking_match.group(1).strip() if thinking_match else ""
    answer = final_match.group(1).strip() if final_match else content.strip()
    return thinking, answer


async def run_ollama(client: httpx.AsyncClient, label: str, model: str, think) -> dict:
    payload: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": PROMPT},
        ],
        "stream": False,
    }
    if think is not None:
        payload["think"] = think

    url = OLLAMA_BASE + "/api/chat"
    t0 = time.monotonic()
    try:
        resp = await client.post(url, json=payload, timeout=300)
        resp.raise_for_status()
        d = resp.json()
    except Exception as exc:
        return _err(label, model, think, exc, t0)

    msg = d.get("message", {})
    thinking = msg.get("thinking") or ""
    content = msg.get("content") or ""
    total_ms = int(d.get("total_duration", (time.monotonic() - t0) * 1e9) // 1_000_000)
    out_tok = d.get("eval_count", 0)

    quality, _ = _quality(content)
    return _result(
        label,
        model,
        think,
        thinking,
        content,
        d.get("prompt_eval_count", 0),
        out_tok,
        total_ms,
        quality,
    )


async def run_openai(client: httpx.AsyncClient, label: str, model: str, think) -> dict:
    url = MLX_BASE + "/chat/completions"
    t0 = time.monotonic()
    try:
        resp = await client.post(
            url,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": PROMPT},
                ],
                "temperature": 0.1,
                "max_tokens": 1200,
            },
            timeout=300,
        )
        resp.raise_for_status()
        d = resp.json()
    except Exception as exc:
        return _err(label, model, think, exc, t0)

    if "error" in d:
        return _err(label, model, think, Exception(d["error"]), t0)

    raw = d["choices"][0]["message"]["content"]
    thinking, content = _strip_mlx_thinking(raw)
    u = d.get("usage", {})
    total_ms = int((time.monotonic() - t0) * 1000)

    quality, _ = _quality(content or raw)
    return _result(
        label,
        model,
        think,
        thinking,
        content or raw,
        u.get("prompt_tokens", 0),
        u.get("completion_tokens", 0),
        total_ms,
        quality,
    )


def _err(label, model, think, exc, t0) -> dict:
    return {
        "label": label,
        "model": model,
        "think": str(think),
        "error": str(exc)[:80],
        "thinking_words": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_ms": int((time.monotonic() - t0) * 1000),
        "quality": "—",
        "answer": "",
    }


def _result(label, model, think, thinking, content, in_tok, out_tok, total_ms, quality) -> dict:
    return {
        "label": label,
        "model": model,
        "think": str(think),
        "error": None,
        "thinking_words": len(thinking.split()) if thinking else 0,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "total_ms": total_ms,
        "toks": round(out_tok / (total_ms / 1000), 1) if total_ms > 0 else 0,
        "quality": quality,
        "answer": content,
    }


async def main() -> None:
    print(f"\nOllama: {OLLAMA_BASE}   MLX: {MLX_BASE}")
    print(f"Prompt: {PROMPT.splitlines()[0]}…\n")

    async with httpx.AsyncClient() as client:
        tasks = []
        for label, backend, model, think in TESTS:
            if backend == "ollama":
                tasks.append(run_ollama(client, label, model, think))
            else:
                tasks.append(run_openai(client, label, model, think))
        results = await asyncio.gather(*tasks)

    sep = "─" * 100
    print(sep)
    print(f"{'':25} {'think_wds':>10} {'in':>6} {'out':>6} {'ms':>8} {'tok/s':>6}  quality")
    print(sep)

    for r in results:
        print()
        if r["error"]:
            print(f"  {r['label']:<23}  ERROR: {r['error']}")
            continue
        print(
            f"  {r['label']:<23}  "
            f"{r['thinking_words']:>10} {r['input_tokens']:>6} {r['output_tokens']:>6} "
            f"{r['total_ms']:>8} {r['toks']:>6}  {r['quality']}"
        )
        lines = [ln for ln in r["answer"].splitlines() if ln.strip()][:25]
        print("\n".join(f"    {ln}" for ln in lines))

    print(f"\n{sep}")


if __name__ == "__main__":
    asyncio.run(main())
