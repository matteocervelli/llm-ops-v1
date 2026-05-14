# OpenCode Fallback for Non-Claude Tool Use

Use this fallback if Claude Code still fails the proxy smoke tests with DeepSeek,
Ollama, or MLX after the reduced tool surface and proxy repairs are enabled.

## Decision Gate

Move the live non-Claude tool-use demo to OpenCode if either of these still fails:

- Claude Code renders two full assistant responses for one user turn.
- Claude Code receives malformed tool input such as `Bash {}` or `Read {}`.

Keep Claude Code available for text-only or read-only comparison with:

```bash
make proxy-deepseek
make claude-proxy-chat
```

## OpenRouter / DeepSeek

Configure OpenCode with an OpenAI-compatible provider pointing at OpenRouter:

```text
base_url: https://openrouter.ai/api/v1
api_key: $OPENROUTER_API_KEY
model: deepseek/deepseek-v4-flash
```

Run the demo from the project root and ask for a small, inspectable task:

```bash
opencode
```

Suggested smoke prompt:

```text
List the files in this repository, then read README.md and summarize the project in 5 bullets.
```

## Local Ollama / MLX

For local OpenAI-compatible endpoints, use the local `/v1` URL and the exact model
name served by the backend:

```text
base_url: http://localhost:11434/v1
api_key: no-key-required
model: gpt-oss:20b
```

or:

```text
base_url: http://studio4change.siamese-dominant.ts.net:8080/v1
api_key: no-key-required
model: qwen3.6:27b
```

## Demo Positioning

Use Claude Code for the Anthropic-native workflow, Codex for GPT-native workflow,
and OpenCode for the open/local model workflow. The fallback is a model portability
demo, not a claim that every model is reliable with Claude Code's full tool set.
