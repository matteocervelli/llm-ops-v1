# pyright: reportPrivateImportUsage=false

import asyncio
import os

import google.generativeai as genai

from llm_ops_v1.agents.token_based import CompletionResult


class GeminiGenerativeLanguageClient:
    def __init__(self, model: str = "gemini-2.5-flash", api_key: str | None = None) -> None:
        genai.configure(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(model)

    async def complete(self, prompt: str, system: str | None = None) -> CompletionResult:
        contents = [part for part in [system, prompt] if part]
        response = await asyncio.to_thread(self.model.generate_content, contents)
        usage = getattr(response, "usage_metadata", None)
        return CompletionResult(
            text=getattr(response, "text", ""),
            input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
            output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
        )
