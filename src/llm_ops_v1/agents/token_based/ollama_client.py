import os

import ollama

from llm_ops_v1.agents.token_based import CompletionResult


class OllamaChatClient:
    def __init__(
        self,
        model: str = "qwen3.6:27b",
        host: str | None = None,
    ) -> None:
        self.model = model
        self.client = ollama.AsyncClient(
            host=host or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )

    async def complete(self, prompt: str, system: str | None = None) -> CompletionResult:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = await self.client.chat(model=self.model, messages=messages)
        return CompletionResult(
            text=response.message.content or "",
            input_tokens=response.prompt_eval_count or 0,
            output_tokens=response.eval_count or 0,
        )
