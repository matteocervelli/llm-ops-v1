import os

from anthropic import AsyncAnthropic

from llm_ops_v1.agents.token_based import CompletionResult


def _extract_text_block(blocks: list[object]) -> str:
    for block in blocks:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            return text
    return ""


class AnthropicMessagesClient:
    def __init__(self, model: str = "claude-sonnet-4-5", api_key: str | None = None) -> None:
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    async def complete(self, prompt: str, system: str | None = None) -> CompletionResult:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=800,
            system=system or "You are a concise production assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        text = _extract_text_block(list(response.content))
        return CompletionResult(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
