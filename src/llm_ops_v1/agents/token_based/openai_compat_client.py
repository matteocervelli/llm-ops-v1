from openai import AsyncOpenAI

from llm_ops_v1.agents.token_based import CompletionResult


class OpenAICompatClient:
    """OpenAI-compatible client for local servers (MLX, vLLM, etc.)."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "no-key-required",
    ) -> None:
        self.model = model
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def complete(self, prompt: str, system: str | None = None) -> CompletionResult:
        messages = [
            {"role": "system", "content": system or "You are a concise production assistant."},
            {"role": "user", "content": prompt},
        ]
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=messages,
        )
        message = response.choices[0].message.content or ""
        usage = response.usage
        return CompletionResult(
            text=message,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
