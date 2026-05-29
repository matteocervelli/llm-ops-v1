# Evaluator protocol — the single interface all judge implementations must satisfy.
# Using typing.Protocol instead of ABC keeps it structural: any class with a
# matching judge_output signature conforms, without inheriting from a base class.

from typing import Protocol, runtime_checkable

from llm_ops_v1.evals.llm_judge import JudgeScore


@runtime_checkable
class Evaluator(Protocol):
    async def judge_output(self, prompt: str, output: str, rubric: str) -> JudgeScore: ...
