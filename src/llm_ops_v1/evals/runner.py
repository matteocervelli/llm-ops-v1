"""Eval runner — runs a dataset through an evaluator and returns aggregate scores.

Supports both DeterministicJudge (offline, CI-safe) and ClaudeJudge (live, API-required).
Results are written to DashboardStore when a store is provided.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from llm_ops_v1.evals.datasets import GoldenExample
from llm_ops_v1.evals.llm_judge import JudgeScore
from llm_ops_v1.evals.protocol import Evaluator
from llm_ops_v1.evals.rubrics import SUPPORT_TRIAGE_RUBRIC


@dataclass(frozen=True)
class EvalResult:
    example_id: str
    prompt: str
    output: str
    expected_action: str
    detected_action: str
    score: int
    passed: bool
    rationale: str
    action_correct: bool


@dataclass(frozen=True)
class EvalSummary:
    total: int
    pass_rate: float  # fraction of examples where score.passed
    avg_score: float
    action_accuracy: float  # fraction where detected_action == expected_action
    results: list[EvalResult]
    timestamp: datetime


def _detect_action(output: str) -> str:
    lower = output.lower()
    if "escalate" in lower:
        return "escalate"
    if "clarif" in lower:
        return "ask_clarification"
    return "reply"


async def run_eval(
    dataset: list[GoldenExample],
    evaluator: Evaluator | None = None,
    agent_fn: object = None,
) -> EvalSummary:
    """Run evaluator over dataset.

    If agent_fn is provided it is called as agent_fn(prompt) -> str to generate
    the output; otherwise a placeholder output is used (deterministic test mode).
    evaluator defaults to DeterministicJudge if omitted.
    """
    from llm_ops_v1.evals.deterministic import DeterministicJudge

    judge: Evaluator = evaluator or DeterministicJudge()
    results: list[EvalResult] = []

    for ex in dataset:
        if agent_fn is not None:
            import asyncio

            if asyncio.iscoroutinefunction(agent_fn):
                output: str = await agent_fn(ex.prompt)  # type: ignore[call-arg]
            else:
                output = agent_fn(ex.prompt)  # type: ignore[call-arg]
        else:
            # Deterministic test mode: synthesise a minimal passing output.
            output = f"decision: reply — responding to: {ex.prompt}"

        rubric = SUPPORT_TRIAGE_RUBRIC
        score: JudgeScore = await judge.judge_output(ex.prompt, output, rubric)
        detected = _detect_action(output)

        results.append(
            EvalResult(
                example_id=ex.id,
                prompt=ex.prompt,
                output=output,
                expected_action=ex.expected_action,
                detected_action=detected,
                score=score.score,
                passed=score.passed,
                rationale=score.rationale,
                action_correct=(detected == ex.expected_action),
            )
        )

    total = len(results)
    pass_rate = sum(1 for r in results if r.passed) / total if total else 0.0
    avg_score = sum(r.score for r in results) / total if total else 0.0
    action_accuracy = sum(1 for r in results if r.action_correct) / total if total else 0.0

    return EvalSummary(
        total=total,
        pass_rate=pass_rate,
        avg_score=avg_score,
        action_accuracy=action_accuracy,
        results=results,
        timestamp=datetime.now(UTC),
    )
