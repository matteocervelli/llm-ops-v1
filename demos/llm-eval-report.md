# LLM Thinking Budget — Eval Report

**Date**: 2026-05-13 | **Infra**: Ollama homelab (RTX/CPU) + MLX Studio (Apple Silicon M-series)

---

## Setup

| Backend | Model                | Params active | Host           |
| ------- | -------------------- | :-----------: | -------------- |
| Ollama  | gpt-oss:20b          |  3.6B (MoE)   | homelab :11434 |
| Ollama  | gemma4:31b           |   ~4B (MoE)   | homelab :11434 |
| Ollama  | qwen3.6:35b-a3b      |  3.5B (MoE)   | homelab :11434 |
| MLX     | gpt-oss-20b-MXFP4-Q8 |  3.6B (MoE)   | studio :8080   |

Thinking budget tested on gpt-oss native Ollama API (`think: "low"/"medium"/"high"`).
MLX uses OpenAI-compat endpoint — thinking visible as inline `<|channel|>` tokens.

---

## Benchmark 1 — Simple coding (find_duplicates)

**Prompt**: `find_duplicates(directory) -> dict[str, list[str]]` with MD5, PermissionError handling, skip empty files.
**Quality**: 3 binary checks (code block, type hints, error handling).

| Config             | Think wds | Out tok |    ms |   tok/s | Quality       |
| ------------------ | --------: | ------: | ----: | ------: | ------------- |
| gpt-oss **medium** |        62 |    1081 |  9474 | **114** | 3/3           |
| gpt-oss low        |         7 |     588 | 12937 |      45 | 3/3           |
| gpt-oss high       |       230 |    1514 | 21886 |      69 | **2/3 ✗code** |
| mlx gpt-oss        |       241 |     767 | 16379 |      47 | 3/3           |
| gemma4 (Ollama)    |       319 |    1111 | 56276 |      20 | 3/3           |

**Finding**: `think:high` broke formatting — omitted markdown code fences. More thinking
on a trivial problem causes over-elaboration that degrades output structure.
`think:medium` was fastest end-to-end at 114 tok/s despite more output tokens.

---

## Benchmark 2 — Known pattern (CircuitBreaker)

**Prompt**: Full circuit breaker with State enum, asyncio.Lock, HALF_OPEN probe, generics.
**Quality**: 5 binary checks (enum, lock, HALF_OPEN, exception class, TypeVar/Callable).

| Config          | Think wds | Out tok |     ms | tok/s | Quality |
| --------------- | --------: | ------: | -----: | ----: | ------- |
| gpt-oss **low** |         1 |     724 |   7402 |    98 | **5/5** |
| gpt-oss medium  |      1324 |    2825 |  24301 |   116 | 5/5     |
| gpt-oss high    |      4304 |    7969 |  73006 |   109 | 5/5     |
| mlx gpt-oss     |       543 |    1200 |  13926 |    86 | 5/5     |
| gemma4          |       185 |    1296 | 117786 |    11 | 5/5     |

**Finding**: All models know circuit breaker. `think:low` (1 word!) produced a perfect
implementation in 7.4s — the pattern is memorised. `think:high` generated 11× more tokens
than `think:low` with identical quality. Budget overhead: +65s, zero benefit.
MLX thinking process is explicit and readable — pedagogically useful.

---

## Benchmark 3 — Ambiguous problem (SmartRetryPolicy)

**Prompt**: Adaptive retry with different formulas per error type (429/502/timeout),
rolling 5-min congestion score, proportional jitter. Model must **invent** formulas and justify them.
**Quality**: 5 checks (error differentiation, rolling window, congestion score, adaptive jitter, inline justification).

| Config             | Think wds | Out tok |    ms | tok/s | Quality            |
| ------------------ | --------: | ------: | ----: | ----: | ------------------ |
| gpt-oss **low**    |        50 |     699 |  7156 |    98 | **5/5**            |
| gpt-oss **medium** |       290 |    1050 | 13376 |    79 | **5/5**            |
| gpt-oss high       |      3265 |    5983 | 49187 |   122 | **4/5 ✗justified** |
| mlx gpt-oss        |       254 |     986 | 13116 |    75 | 4/5 ✗justified     |
| gemma4             |       360 |    1660 | 98610 |    17 | 4/5 ✗justified     |

**Finding**: The high-thinking model spent 3265 words reasoning the algorithm and produced
only 3 dense justification comments instead of distributing explanations through the code.
Counter-intuitively, `think:low` passed all 5 checks — it "thought out loud" via inline
comments instead of internal reasoning. `think:medium` made the most interesting design choice:
treating timeout as a constant wait (defensible: unknown failure mode → safe default).

---

## Cross-benchmark Summary

| Thinking   | Best for                                       | Risk                                               |
| ---------- | ---------------------------------------------- | -------------------------------------------------- |
| **low**    | Known patterns, latency-sensitive, interactive | May skip formatting                                |
| **medium** | Novel problems, design decisions               | Best overall tradeoff                              |
| **high**   | Genuinely novel algorithms, no time constraint | Over-engineering, verbose, less communicative code |

### Key takeaways

1. **Thinking budget ≠ quality budget.** On known patterns (circuit breaker), low=high quality.
   Budget only matters when the problem has no memorised solution.

2. **High thinking → dense internal reasoning, sparse external communication.** The model
   solves the problem internally but writes less readable, less commented code.

3. **MLX on Apple Silicon ≈ Ollama homelab** at think:low equivalent (~75-86 tok/s).
   MLX advantage: thinking is visible as text — useful for debugging and demos.

4. **gemma4:31b is too slow for interactive use** (17-20 tok/s, 56-117s). Acceptable for
   background batch tasks. Should not be used in any latency-sensitive pipeline.

5. **MoE efficiency**: all fast models (gpt-oss, qwen3.6:35b-a3b) activate only 3-4B params
   per token despite 20-35B total params. Local inference is economically viable.

---

## Recommendations for LLMOps pipeline

| Stage                            | Model             | Think   | Rationale                   |
| -------------------------------- | ----------------- | ------- | --------------------------- |
| Code generation (known patterns) | gpt-oss:20b       | low     | 7-9s, correct, cheap        |
| Design decisions / architecture  | gpt-oss:20b       | medium  | 13s, best tradeoff          |
| Batch quality review (no SLA)    | gemma4:31b        | default | Best reasoning per dollar   |
| Cost-sensitive cloud fallback    | DeepSeek V4 Flash | —       | $0.14/$0.28 per 1M tok      |
| Latency-critical path            | qwen3.6:35b-a3b   | false   | 334ms, no thinking overhead |
