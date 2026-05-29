# Agents in Production — Session 2

Companion repository for the live session **Agents in Production** (**29 maggio 2026**).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## What's Here

| Path                | Contents                                                                                         |
| ------------------- | ------------------------------------------------------------------------------------------------ |
| `src/llm_ops_v1/`   | Runtime package: agents, memory, evals, economics, caching, dashboard, monitoring, observability |
| `tests/`            | Unit, integration, regression, demo, and provider-client tests                                   |
| `docs/`             | Public session notes and case guide                                                              |
| `docs/theory/`      | Optional inference internals: prefill, decode, KV cache, quantization                            |
| `docs/resources/`   | Reading list and operational checklist                                                           |
| `notebooks/`        | Session companion notebooks (module-5-companion.ipynb)                                           |
| `demos/`            | Executable demo scripts                                                                          |
| `public/`           | Diagrams: Excalidraw sources and PNG exports                                                     |
| `scripts/diagrams/` | Diagram generation scripts                                                                       |
| `infrastructure/`   | Local Compose, VPS, and serverless examples                                                      |

## Setup

```bash
cp .env.example .env
# Fill the blank local-only secret values in .env before starting Compose.
uv sync
docker compose -f infrastructure/docker-compose.yml up -d
```

The local stack starts Postgres, Redis, ClickHouse, MinIO, and Langfuse. Ports are
bound to localhost by default.

## Run

```bash
uv run llm-ops triage "Il mio ordine e' in ritardo"
uv run streamlit run src/llm_ops_v1/dashboard/app.py
```

The CLI and dashboard work without provider keys by using deterministic demo
fallbacks. Add API keys in `.env` only for live provider calls.

## Modules

| #      | Topic                                      | Primary Doc                                                            |
| ------ | ------------------------------------------ | ---------------------------------------------------------------------- |
| 00     | Ticket-to-dashboard case guide, eval, HITL | [docs/00-caso-guida-eval-hitl.md](docs/00-caso-guida-eval-hitl.md)     |
| 01     | Cost estimation and model routing          | [docs/01-cost-and-routing.md](docs/01-cost-and-routing.md)             |
| 02     | Context, memory, and prompt caching        | [docs/02-context-memory-caching.md](docs/02-context-memory-caching.md) |
| 03     | Evals and LLM-as-a-Judge                   | [docs/03-evals-llm-as-a-judge.md](docs/03-evals-llm-as-a-judge.md)     |
| 04     | Monitoring and dashboard design            | [docs/04-monitoring-dashboard.md](docs/04-monitoring-dashboard.md)     |
| 05     | Scaling, resilience, and production ops    | [docs/05-scaling-resilience.md](docs/05-scaling-resilience.md)         |
| —      | Operational runbook                        | [docs/runbook.md](docs/runbook.md)                                     |
| Theory | LLM inference internals                    | [docs/theory/README.md](docs/theory/README.md)                         |

## Quality Gates

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest -q
```

## Session 1

Repository for **AI-Driven Development** (22 maggio 2026):
[matteocervelli/ai-dev-v1](https://github.com/matteocervelli/ai-dev-v1).

## License

[MIT](LICENSE)
