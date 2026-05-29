from dataclasses import dataclass


@dataclass(frozen=True)
class CompletionResult:
    text: str
    input_tokens: int
    output_tokens: int


from llm_ops_v1.agents.token_based.anthropic_client import AnthropicMessagesClient  # noqa: E402
from llm_ops_v1.agents.token_based.deepseek_client import DeepSeekOpenRouterClient  # noqa: E402
from llm_ops_v1.agents.token_based.gemini_client import GeminiGenerativeLanguageClient  # noqa: E402
from llm_ops_v1.agents.token_based.ollama_client import OllamaChatClient  # noqa: E402
from llm_ops_v1.agents.token_based.openai_client import OpenAIChatClient  # noqa: E402
from llm_ops_v1.agents.token_based.openai_compat_client import OpenAICompatClient  # noqa: E402

__all__ = [
    "AnthropicMessagesClient",
    "CompletionResult",
    "DeepSeekOpenRouterClient",
    "GeminiGenerativeLanguageClient",
    "OllamaChatClient",
    "OpenAIChatClient",
    "OpenAICompatClient",
]
