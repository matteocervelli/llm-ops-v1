.PHONY: mlx-27b mlx-35b mlx-gpt-oss mlx-gemma4 mlx-stop ollama-pull ollama-serve servers-check proxy-ollama proxy-mlx proxy-deepseek proxy-deepseek-full claude-proxy-ollama claude-proxy-mlx claude-proxy-deepseek claude-proxy-deepseek-full claude-proxy-deepseek-native claude-proxy-chat opencode-fallback

STUDIO          := studio
STUDIO_TMUX     := /opt/homebrew/bin/tmux
MLX_VENV        := ~/dev/services/thesaurus/.venv/bin/activate
MLX_HF_HOME     := ~/dev/.mlx-models
MLX_HOST        := 0.0.0.0
MLX_PORT        := 8080
MLX_SESSION_27B   := mlx-27b
MLX_SESSION_35B   := mlx-35b
MLX_SESSION_GPTOSS := mlx-gpt-oss
MLX_SESSION_GEMMA4 := mlx-gemma4
MLX_PYENV         := ~/.pyenv/versions/3.14.0/bin/mlx_lm.server
CLAUDE_PROXY_ENV  := CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK=1 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 CLAUDE_CODE_ENABLE_PROMPT_SUGGESTION=false CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1 CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1
CLAUDE_PROXY_TOOLS ?= Read,Glob,Grep,Bash
CLAUDE_PROXY_PROMPT := $$(cat demos/claude-proxy-tool-rules.md)
PROXY_TOOL_MODE ?= read-only
PROXY_OLLAMA_PORT ?= 4010
PROXY_MLX_PORT ?= 4001
PROXY_DEEPSEEK_PORT ?= 4002
OLLAMA_PROXY_MODEL ?= gpt-oss:20b
MLX_PROXY_MODEL ?= mlx-community/Qwen3.6-27B-OptiQ-4bit
DEEPSEEK_PROXY_MODEL ?= deepseek/deepseek-v4-flash

# ── MLX on Studio ─────────────────────────────────────────────────────────────

mlx-27b: ## Start MLX 27B on Studio via Tailscale (tmux, HTTP :8080)
	ssh $(STUDIO) " \
	  $(STUDIO_TMUX) kill-session -t $(MLX_SESSION_27B) 2>/dev/null; \
	  $(STUDIO_TMUX) new-session -d -s $(MLX_SESSION_27B) \
	    'source $(MLX_VENV) && \
	     HF_HOME=$(MLX_HF_HOME) mlx_lm.server \
	       --model mlx-community/Qwen3.6-27B-OptiQ-4bit \
	       --host $(MLX_HOST) --port $(MLX_PORT)' \
	"
	@echo "MLX 27B → http://studio4change.siamese-dominant.ts.net:$(MLX_PORT)/v1"
	@echo "Logs: ssh $(STUDIO) $(STUDIO_TMUX) attach -t $(MLX_SESSION_27B)"

mlx-35b: ## Start MLX 35B-A3B on Studio via Tailscale (tmux, HTTP :8080)
	ssh $(STUDIO) " \
	  $(STUDIO_TMUX) kill-session -t $(MLX_SESSION_35B) 2>/dev/null; \
	  $(STUDIO_TMUX) new-session -d -s $(MLX_SESSION_35B) \
	    'source $(MLX_VENV) && \
	     HF_HOME=$(MLX_HF_HOME) mlx_lm.server \
	       --model mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit \
	       --host $(MLX_HOST) --port $(MLX_PORT)' \
	"
	@echo "MLX 35B-A3B → http://studio4change.siamese-dominant.ts.net:$(MLX_PORT)/v1"
	@echo "Logs: ssh $(STUDIO) $(STUDIO_TMUX) attach -t $(MLX_SESSION_35B)"

mlx-gpt-oss: ## Start GPT-OSS 20B on Studio (MoE, think low/medium/high)
	ssh $(STUDIO) " \
	  $(STUDIO_TMUX) kill-session -t $(MLX_SESSION_GPTOSS) 2>/dev/null; \
	  $(STUDIO_TMUX) new-session -d -s $(MLX_SESSION_GPTOSS) \
	    'HF_HOME=$(MLX_HF_HOME) $(MLX_PYENV) \
	       --model mlx-community/gpt-oss-20b-MXFP4-Q8 \
	       --host $(MLX_HOST) --port $(MLX_PORT)' \
	"
	@echo "GPT-OSS 20B → http://studio4change.siamese-dominant.ts.net:$(MLX_PORT)/v1"
	@echo "Logs: ssh $(STUDIO) $(STUDIO_TMUX) attach -t $(MLX_SESSION_GPTOSS)"

mlx-gemma4: ## Start Gemma 4 31B on Studio
	ssh $(STUDIO) " \
	  $(STUDIO_TMUX) kill-session -t $(MLX_SESSION_GEMMA4) 2>/dev/null; \
	  $(STUDIO_TMUX) new-session -d -s $(MLX_SESSION_GEMMA4) \
	    'HF_HOME=$(MLX_HF_HOME) $(MLX_PYENV) \
	       --model mlx-community/gemma-4-27b-it-4bit \
	       --host $(MLX_HOST) --port $(MLX_PORT)' \
	"
	@echo "Gemma 4 31B → http://studio4change.siamese-dominant.ts.net:$(MLX_PORT)/v1"
	@echo "Logs: ssh $(STUDIO) $(STUDIO_TMUX) attach -t $(MLX_SESSION_GEMMA4)"

mlx-stop: ## Stop all MLX servers on Studio
	ssh $(STUDIO) " \
	  $(STUDIO_TMUX) kill-session -t $(MLX_SESSION_27B) 2>/dev/null; \
	  $(STUDIO_TMUX) kill-session -t $(MLX_SESSION_35B) 2>/dev/null; \
	  $(STUDIO_TMUX) kill-session -t $(MLX_SESSION_GPTOSS) 2>/dev/null; \
	  $(STUDIO_TMUX) kill-session -t $(MLX_SESSION_GEMMA4) 2>/dev/null; \
	  echo 'MLX sessions stopped' \
	"

# ── Ollama on homelab ──────────────────────────────────────────────────────────

ollama-pull: ## Pull all Ollama models
	ollama pull qwen3.6:27b
	ollama pull qwen3.6:35b-a3b
	ollama pull gpt-oss:20b
	ollama pull gemma4:31b

ollama-serve: ## Start Ollama bound to 0.0.0.0 (Tailscale-accessible)
	OLLAMA_HOST=0.0.0.0 ollama serve

# ── Anthropic proxy (Ollama/MLX → /v1/messages) ───────────────────────────────

proxy-ollama: ## Start Anthropic→OpenAI proxy for Ollama on :4010
	PROXY_BACKEND=http://localhost:11434 \
	  PROXY_TOOL_MODE=$(PROXY_TOOL_MODE) \
	  PROXY_DEDUPE=1 \
	  uv run uvicorn demos.anthropic-proxy:app --port $(PROXY_OLLAMA_PORT)
proxy-mlx: ## Start Anthropic→OpenAI proxy for MLX Studio on :4001
	PROXY_BACKEND=http://studio4change.siamese-dominant.ts.net:8080 \
	  PROXY_TOOL_MODE=$(PROXY_TOOL_MODE) \
	  PROXY_DEDUPE=1 \
	  uv run uvicorn demos.anthropic-proxy:app --port $(PROXY_MLX_PORT)
proxy-deepseek: ## Start Anthropic→OpenAI proxy for OpenRouter/DeepSeek on :4002
	PROXY_BACKEND=https://openrouter.ai/api \
	  PROXY_API_KEY=$$(cat ~/.config/openrouter/openrouter_api_key) \
	  SUPPRESS_MODELS=claude- \
	  PROXY_TOOL_MODE=$(PROXY_TOOL_MODE) \
	  PROXY_DEDUPE=1 \
	  uv run uvicorn demos.anthropic-proxy:app --port $(PROXY_DEEPSEEK_PORT)

proxy-deepseek-full: ## Start DeepSeek proxy with Claude Code's full tool schema exposed
	$(MAKE) proxy-deepseek PROXY_TOOL_MODE=full

claude-proxy-ollama: ## Launch Claude Code against local Ollama proxy (:4010)
	$(CLAUDE_PROXY_ENV) \
	  ANTHROPIC_BASE_URL=http://127.0.0.1:$(PROXY_OLLAMA_PORT) \
	  ANTHROPIC_AUTH_TOKEN=proxy \
	  claude --bare --model $(OLLAMA_PROXY_MODEL) --tools "$(CLAUDE_PROXY_TOOLS)" \
	    --append-system-prompt "$(CLAUDE_PROXY_PROMPT)"

claude-proxy-mlx: ## Launch Claude Code against MLX proxy (:4001)
	$(CLAUDE_PROXY_ENV) \
	  ANTHROPIC_BASE_URL=http://127.0.0.1:$(PROXY_MLX_PORT) \
	  ANTHROPIC_AUTH_TOKEN=proxy \
	  claude --bare --model $(MLX_PROXY_MODEL) --tools "$(CLAUDE_PROXY_TOOLS)" \
	    --append-system-prompt "$(CLAUDE_PROXY_PROMPT)"

claude-proxy-deepseek: ## Launch Claude Code against OpenRouter/DeepSeek proxy (:4002)
	$(CLAUDE_PROXY_ENV) \
	  ANTHROPIC_BASE_URL=http://127.0.0.1:$(PROXY_DEEPSEEK_PORT) \
	  ANTHROPIC_AUTH_TOKEN=proxy \
	  claude --bare --model $(DEEPSEEK_PROXY_MODEL) --tools "$(CLAUDE_PROXY_TOOLS)" \
	    --append-system-prompt "$(CLAUDE_PROXY_PROMPT)"

claude-proxy-deepseek-full: ## Launch Claude Code against DeepSeek with default/full tools
	$(MAKE) claude-proxy-deepseek CLAUDE_PROXY_TOOLS=default

claude-proxy-deepseek-native: ## Launch normal Claude Code against DeepSeek proxy for slash skills
	$(CLAUDE_PROXY_ENV) \
	  ANTHROPIC_BASE_URL=http://127.0.0.1:$(PROXY_DEEPSEEK_PORT) \
	  ANTHROPIC_AUTH_TOKEN=proxy \
	  claude --model $(DEEPSEEK_PROXY_MODEL) \
	    --append-system-prompt "$(CLAUDE_PROXY_PROMPT)"

claude-proxy-chat: ## Launch Claude Code text-only against DeepSeek proxy (:4002)
	$(CLAUDE_PROXY_ENV) \
	  ANTHROPIC_BASE_URL=http://127.0.0.1:$(PROXY_DEEPSEEK_PORT) \
	  ANTHROPIC_AUTH_TOKEN=proxy \
	  claude --bare --model $(DEEPSEEK_PROXY_MODEL) --tools "" \
	    --append-system-prompt "$(CLAUDE_PROXY_PROMPT)"

opencode-fallback: ## Print the OpenCode fallback runbook
	@sed -n '1,220p' demos/opencode-fallback.md
# ── Smoke test ─────────────────────────────────────────────────────────────────

servers-check: ## Verify all model backends are reachable
	bash demos/test-alternative-models.sh

# ── Help ───────────────────────────────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*##"}; {printf "  %-18s %s\n", $$1, $$2}'
