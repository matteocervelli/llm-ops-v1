# Repository Guidelines

## Project Structure

This repository is the companion project for **Agents in Production**. It combines
teaching material with a small, runnable LLM Ops reference implementation.

- `src/llm_ops_v1/` contains the Python package: agents, token clients, memory,
  caching, evals, guardrails, dashboard, economics, and observability.
- `tests/` contains unit, integration, regression, demo, and provider-client tests.
- `docs/` contains public session material.
- `docs/theory/` contains optional background notes for LLM inference internals.
- `docs/resources/` contains the reading list and operational checklist.
- `demos/` contains executable demo scripts.
- `public/` contains diagram sources and PNG exports.
- `scripts/diagrams/` contains diagram generator scripts.
- `infrastructure/` contains local Compose, VPS, and serverless examples.

## Commands

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest -q
uv run llm-ops triage "Il mio ordine e' in ritardo"
uv run streamlit run src/llm_ops_v1/dashboard/app.py
docker compose -f infrastructure/docker-compose.yml up -d
```

## Coding Standards

- Python 3.12, absolute imports from `llm_ops_v1`.
- Type hints on function parameters and returns in `src/`.
- Files should stay under 500 lines; functions should stay under 50 lines.
- Prefer dataclasses and small pure helpers for domain data.
- Keep provider/network wrappers thin and explicit.
- Avoid mutable defaults; use `default_factory`.
- No bare `except`; catch explicit exception types.
- Comments should explain why a choice exists, not restate the code.

## Tests

Use focused tests near the behavior being changed. Keep deterministic unit tests
separate from integration tests that need Redis or provider credentials.

Before publication or force-push, run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest -q
gitleaks protect --source . --redact --exit-code 1
```

## Security

Never commit `.env`, local credentials, local Claude/Codex state, shell history,
or runtime traces. Demo credentials in `.env.example` and Compose files must be
obviously local placeholders. Shared deployments must use environment variables
or a secrets manager.
