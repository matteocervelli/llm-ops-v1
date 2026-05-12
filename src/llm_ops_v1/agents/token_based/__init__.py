from dataclasses import dataclass


@dataclass(frozen=True)
class CompletionResult:
    text: str
    input_tokens: int
    output_tokens: int


from llm_ops_v1.agents.token_based.deepseek_client import DeepSeekOpenRouterClient  # noqa: E402
from llm_ops_v1.agents.token_based.ollama_client import OllamaChatClient  # noqa: E402
from llm_ops_v1.agents.token_based.openai_compat_client import OpenAICompatClient  # noqa: E402

__all__ = [
    "CompletionResult",
    "DeepSeekOpenRouterClient",
    "OllamaChatClient",
    "OpenAICompatClient",
]
