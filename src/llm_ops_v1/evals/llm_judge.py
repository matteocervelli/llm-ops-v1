import json
import os

from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field


class JudgeScore(BaseModel):
    score: int = Field(ge=1, le=10)
    passed: bool
    rationale: str


def _extract_text_block(blocks: list[object]) -> str:
    for block in blocks:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            return text
    return ""


class ClaudeJudge:
    def __init__(self, model: str = "claude-sonnet-4-5", api_key: str | None = None) -> None:
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    async def judge_output(self, prompt: str, output: str, rubric: str) -> JudgeScore:
        evaluation_prompt = {
            "rubric": rubric,
            "prompt": prompt,
            "output": output,
            "response_schema": JudgeScore.model_json_schema(),
        }
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system="You are a strict evaluator. Return JSON only.",
            messages=[{"role": "user", "content": json.dumps(evaluation_prompt)}],
        )
        text_block = _extract_text_block(list(response.content))
        return JudgeScore.model_validate_json(text_block)
