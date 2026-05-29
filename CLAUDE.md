# llm-ops-v1

Guidance for Claude Code and other coding agents working in this repository.

## Repository Purpose

`llm-ops-v1` is the companion repository for the live session **Agents in
Production**. It demonstrates a small LLM Ops stack around a support-triage
agent: cost estimation, routing, memory, caching, evals, guardrails,
observability, dashboarding, CLI, and webhook runtime.

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

Provider keys are optional for local demos. Without keys, the triage path uses
deterministic fallback output.

## Structure

| Path | Contents |
| --- | --- |
| `src/llm_ops_v1/agents/` | Agent definitions, routing, webhook adapters, token clients |
| `src/llm_ops_v1/memory/` | Short-term, long-term, episodic, Redis Array memory |
| `src/llm_ops_v1/economics/` | Pricing, cost estimation, local model profiles |
| `src/llm_ops_v1/caching/` | Prompt-prefix cache keys and savings estimates |
| `src/llm_ops_v1/evals/` | LLM-as-a-Judge interface |
| `src/llm_ops_v1/guardrails/` | Deterministic output checks |
| `src/llm_ops_v1/dashboard/` | Streamlit dashboard data model, store, UI |
| `docs/` | Public notes, theory, resources, and presenter notes |
| `demos/` | Executable demo scripts |
| `infrastructure/` | Local Compose, VPS, serverless examples |

## Coding Conventions

- Python 3.12, `uv`, Ruff, Pyright basic mode.
- Absolute imports from `llm_ops_v1`.
- Type hints on function parameters and returns in `src/`.
- Keep source files under 500 lines and functions under 50 lines.
- Keep demo scripts runnable from repo root.
- Keep local credentials in `.env`; never commit real secrets or local runtime state.

## Security Notes

- `.env`, `.env.*`, `.claude/`, `.runtime/`, caches, screenshots, and temporary
  workspaces are local-only.
- `infrastructure/docker-compose.yml` is a local stack, not a production hardening
  baseline.
- Run `gitleaks protect --source . --redact --exit-code 1` before publication.
