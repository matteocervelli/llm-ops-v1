import os

from openai import AsyncOpenAI

from llm_ops_v1.agents.token_based import CompletionResult


class OpenAIChatClient:
    def __init__(self, model: str = "gpt-5.5", api_key: str | None = None) -> None:
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    async def complete(self, prompt: str, system: str | None = None) -> CompletionResult:
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system or "You are a concise production assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        message = response.choices[0].message.content or ""
        usage = response.usage
        return CompletionResult(
            text=message,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
