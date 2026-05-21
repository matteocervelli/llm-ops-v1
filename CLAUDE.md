# llm-ops-v1

Scaffold LLM Ops per live session "Agents in Production" (**29 maggio 2026**).
Multi-provider agent routing, cost estimation, memory systems, evals con LLM judge, Langfuse observability.

## Setup

```bash
cp .env.example .env          # fill ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY
uv sync
docker-compose up             # Postgres, Redis, ClickHouse, Langfuse Web (:3000)
```

## Test

```bash
uv run pytest tests/evals/unit/         # fast — usa questi dopo ogni modifica
uv run pytest -m integration            # full agent flows
uv run pytest -m regression             # regression suite
```

## Struttura

| Path                            | Contenuto                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------ |
| `src/llm_ops_v1/`               | package principale                                                             |
| `src/llm_ops_v1/agents/`        | agent definitions (Pydantic AI)                                                |
| `src/llm_ops_v1/memory/`        | short_term, long_term, episodic                                                |
| `src/llm_ops_v1/evals/`         | LLM judge, metrics                                                             |
| `src/llm_ops_v1/economics/`     | cost router, provider selection                                                |
| `src/llm_ops_v1/observability/` | Langfuse tracing, structured logging                                           |
| `tests/evals/`                  | unit / integration / regression (marker separati)                              |
| `infrastructure/`               | Docker Compose, VPS systemd, Fly.io                                            |
| `demos/`                        | anthropic-proxy.py (Anthropic→OpenAI adapter :4010), thinking-bench, run-sheet |
| `resources/`                    | reading_list.md, survival_kit.md (materiali handout)                           |
| `course/`                       | diagrammi corso (submodule ai-dev)                                             |

## Convenzioni codice

- **Async-first**: `async def` ovunque, `pytest-asyncio` con `asyncio_mode = "auto"`
- **Agent pattern**: `Agent` da Pydantic AI + `@agent.tool` decorators + `AgentDependencies` dataclass tipizzato
- **Naming**: snake_case moduli, CamelCase classi, nomi test descrittivi
- **Ruff**: line-length 100, Python 3.12, select E/F/I/B/UP
- **Pyright**: strict — nessun `Any` implicito

## Supply chain exclusions

Pinned in `pyproject.toml` — **non rimuovere**:

- `mistralai!=2.4.6` — compromessa (Shai-Hulud 2026-05-11)
- `guardrails-ai!=0.10.1` — esegue codice remoto all'import
- `urllib3>=2.7.0` — CVE attivo nelle versioni precedenti

## Proxy Ollama (sviluppo locale)

```bash
make proxy-ollama              # adapter Anthropic→OpenAI su :4010
make claude-proxy-ollama       # Claude Code via proxy locale
```
