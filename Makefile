.PHONY: help test lint typecheck format-check quality \
        env-check stack stack-tmux up down logs langfuse-open \
        dashboard webhook worker notebook \
        demo load-test \
        servers-check redis-demo proxy-ollama

PROXY_PORT      ?= 4010
OLLAMA_BASE_URL ?= http://localhost:11434
COMPOSE_FILE    := infrastructure/docker-compose.yml
COMPOSE         := docker compose -f $(COMPOSE_FILE) --env-file .env
LANGFUSE_URL    ?= http://localhost:3001
WORKER_PORT     ?= 8080
N               ?= 8

# ── Help ─────────────────────────────────────────────────────────────────────

help: ## Show available commands
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*##"}; {printf "  %-22s %s\n", $$1, $$2}'

# ── Quality ──────────────────────────────────────────────────────────────────

test: ## Run the full test suite
	uv run pytest -q

lint: ## Run Ruff lint
	uv run ruff check .

format-check: ## Check formatting
	uv run ruff format --check .

typecheck: ## Run Pyright
	uv run pyright

quality: lint format-check typecheck test ## Run all local quality gates

# ── Environment ──────────────────────────────────────────────────────────────

env-check: ## Show which provider keys and services are configured
	@echo "=== Provider keys ==="
	@printf "  ANTHROPIC_API_KEY   : "; [ -n "$$ANTHROPIC_API_KEY"   ] && echo "set" || echo "not set (offline mode)"
	@printf "  OPENAI_API_KEY      : "; [ -n "$$OPENAI_API_KEY"      ] && echo "set" || echo "not set"
	@printf "  GEMINI_API_KEY      : "; [ -n "$$GEMINI_API_KEY"      ] && echo "set" || echo "not set"
	@printf "  OPENROUTER_API_KEY  : "; [ -n "$$OPENROUTER_API_KEY"  ] && echo "set" || echo "not set (deepseek)"
	@echo ""
	@echo "=== Langfuse ==="
	@printf "  LANGFUSE_PUBLIC_KEY : "; [ -n "$$LANGFUSE_PUBLIC_KEY" ] && echo "set" || echo "not set (tracing disabled)"
	@printf "  LANGFUSE_SECRET_KEY : "; [ -n "$$LANGFUSE_SECRET_KEY" ] && echo "set" || echo "not set"
	@echo ""
	@echo "=== Infrastructure ==="
	@printf "  Redis               : "; redis-cli ping 2>/dev/null | grep -q PONG && echo "running" || echo "not running  (make up)"
	@printf "  Langfuse            : "; curl -sf $(LANGFUSE_URL)/api/health >/dev/null 2>&1 && echo "running at $(LANGFUSE_URL)" || echo "not running  (make up)"

# ── Infrastructure ───────────────────────────────────────────────────────────

stack: ## Start everything: Docker infra + worker (bg) + dashboard (fg)
	$(MAKE) up
	$(MAKE) worker &
	$(MAKE) dashboard

stack-tmux: ## Start everything in a tmux session (3 windows: docker/worker/dashboard)
	@tmux new-session -d -s llm-ops -n infra 2>/dev/null || tmux kill-session -t llm-ops && tmux new-session -d -s llm-ops -n infra
	@tmux send-keys -t llm-ops:infra "make up && make logs" Enter
	@tmux new-window -t llm-ops -n worker
	@tmux send-keys -t llm-ops:worker "sleep 5 && make worker" Enter
	@tmux new-window -t llm-ops -n dashboard
	@tmux send-keys -t llm-ops:dashboard "sleep 5 && make dashboard" Enter
	@tmux select-window -t llm-ops:dashboard
	@tmux attach-session -t llm-ops

up: ## Start infra stack (Redis, Postgres, ClickHouse, MinIO, Langfuse) — excludes app container
	$(COMPOSE) up -d --scale app=0
	@echo ""
	@echo "  Redis    : localhost:6379"
	@echo "  Langfuse : $(LANGFUSE_URL)"
	@echo ""
	@echo "  Next: make dashboard   (Streamlit :8501)"
	@echo "        make worker      (async queue worker)"

down: ## Stop all docker compose services
	$(COMPOSE) down

logs: ## Follow docker compose logs
	$(COMPOSE) logs -f

langfuse-open: ## Open Langfuse in browser
	@echo "$(LANGFUSE_URL)"
	@xdg-open $(LANGFUSE_URL) 2>/dev/null || open $(LANGFUSE_URL) 2>/dev/null || true

# ── App processes ─────────────────────────────────────────────────────────────

dashboard: ## Start Streamlit dashboard on :8501
	uv run streamlit run src/llm_ops_v1/dashboard/app.py

webhook: ## Start FastAPI webhook on :$(WORKER_PORT)
	uv run uvicorn llm_ops_v1.agents.webhook_handler:app --reload --port $(WORKER_PORT)

worker: ## Start async queue worker
	uv run python -m llm_ops_v1.agents.worker

notebook: ## Launch JupyterLab with module-5-companion.ipynb
	uv run jupyter lab notebooks/module-5-companion.ipynb

# ── Demo shortcuts ────────────────────────────────────────────────────────────

demo: ## Run the 4-scenario demo suite in terminal
	uv run python demos/demo_suite.py

load-test: ## Run N parallel tickets via dispatch  (override: make load-test N=20)
	uv run python demos/load_test.py $(N)

# ── Legacy ───────────────────────────────────────────────────────────────────

redis-demo: ## Run the Redis Array shared-memory demo
	uv run python demos/redis_array_demo.py

proxy-ollama: ## Start Anthropic-compatible proxy backed by Ollama on :$(PROXY_PORT)
	PROXY_BACKEND=$(OLLAMA_BASE_URL) PROXY_TOOL_MODE=read-only PROXY_DEDUPE=1 \
	  uv run uvicorn demos.anthropic_proxy:app --port $(PROXY_PORT)

servers-check: ## Compile-check src and demos
	uv run python -m compileall -q src demos
