from llm_ops_v1.agents.token_based import CompletionResult
from llm_ops_v1.economics.router import OpenRouterClient


class DeepSeekOpenRouterClient:
    """DeepSeek V4 Flash via OpenRouter, adapted to the CompletionResult contract."""

    def __init__(
        self,
        model: str = "deepseek/deepseek-v4-flash",
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self._router = OpenRouterClient(api_key=api_key)

    async def complete(self, prompt: str, system: str | None = None) -> CompletionResult:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        raw = await self._router.chat_completion(model=self.model, messages=messages)
        text = raw["choices"][0]["message"]["content"]
        usage = raw.get("usage", {})
        return CompletionResult(
            text=text,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )
