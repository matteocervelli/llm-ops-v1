import pytest

from llm_ops_v1.evals.llm_judge import JudgeScore


class FakeJudge:
    async def judge_output(self, prompt: str, output: str, rubric: str) -> JudgeScore:
        del prompt, rubric
        passed = "TODO" not in output and len(output.strip()) > 20
        score = 8 if passed else 4
        rationale = (
            "Output is concrete and usable."
            if passed
            else "Output is incomplete or placeholder-like."
        )
        return JudgeScore(score=score, passed=passed, rationale=rationale)


@pytest.fixture
def fake_judge() -> FakeJudge:
    return FakeJudge()
