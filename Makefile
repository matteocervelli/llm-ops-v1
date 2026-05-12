.PHONY: mlx-27b mlx-35b mlx-stop ollama-pull ollama-serve servers-check

STUDIO          := studio
STUDIO_TMUX     := /opt/homebrew/bin/tmux
MLX_VENV        := ~/dev/services/thesaurus/.venv/bin/activate
MLX_HF_HOME     := ~/dev/.mlx-models
MLX_HOST        := 0.0.0.0
MLX_PORT        := 8080
MLX_SESSION_27B := mlx-27b
MLX_SESSION_35B := mlx-35b

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

mlx-stop: ## Stop MLX server on Studio
	ssh $(STUDIO) " \
	  $(STUDIO_TMUX) kill-session -t $(MLX_SESSION_27B) 2>/dev/null; \
	  $(STUDIO_TMUX) kill-session -t $(MLX_SESSION_35B) 2>/dev/null; \
	  echo 'MLX sessions stopped' \
	"

# ── Ollama on homelab ──────────────────────────────────────────────────────────

ollama-pull: ## Pull Qwen3.6 models into local Ollama
	ollama pull qwen3.6:27b
	ollama pull qwen3.6:35b-a3b

ollama-serve: ## Start Ollama bound to 0.0.0.0 (Tailscale-accessible)
	OLLAMA_HOST=0.0.0.0 ollama serve

# ── Smoke test ─────────────────────────────────────────────────────────────────

servers-check: ## Verify all model backends are reachable
	bash demos/test-alternative-models.sh

# ── Help ───────────────────────────────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*##"}; {printf "  %-18s %s\n", $$1, $$2}'
