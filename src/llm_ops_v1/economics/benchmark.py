import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from llm_ops_v1.economics.commercial_models import get_pricing
from llm_ops_v1.economics.cost_calculator import CostBreakdown, estimate_token_cost

BenchmarkCall = Callable[[str], Awaitable[tuple[str, int, int]]]


@dataclass(frozen=True)
class BenchmarkJob:
    model_id: str
    call: BenchmarkCall


@dataclass(frozen=True)
class BenchmarkResult:
    model_id: str
    latency_seconds: float
    cost: CostBreakdown
    output_preview: str


async def benchmark_prompt(prompt: str, jobs: Sequence[BenchmarkJob]) -> list[BenchmarkResult]:
    results: list[BenchmarkResult] = []

    for job in jobs:
        start = time.perf_counter()
        output, prompt_tokens, output_tokens = await job.call(prompt)
        latency = round(time.perf_counter() - start, 3)
        pricing = get_pricing(job.model_id)
        cost = estimate_token_cost(pricing, prompt_tokens, output_tokens)
        results.append(
            BenchmarkResult(
                model_id=job.model_id,
                latency_seconds=latency,
                cost=cost,
                output_preview=output[:120],
            )
        )

    return results
