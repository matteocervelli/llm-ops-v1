.PHONY: mlx-27b mlx-35b mlx-stop ollama-pull ollama-serve servers-check

STUDIO          := studio
MLX_VENV        := ~/dev/services/thesaurus/.venv/bin/activate
MLX_HF_HOME     := ~/dev/.mlx-models
MLX_HOST        := 0.0.0.0
MLX_PORT        := 8080
MLX_SESSION_27B := mlx-27b
MLX_SESSION_35B := mlx-35b

# ── MLX on Studio ─────────────────────────────────────────────────────────────

mlx-27b: ## Start MLX server on Studio with Qwen3.6-27B (background via nohup)
	ssh $(STUDIO) "source $(MLX_VENV) && \
	  HF_HOME=$(MLX_HF_HOME) nohup mlx_lm.server \
	    --model mlx-community/Qwen3.6-27B-OptiQ-4bit \
	    --host $(MLX_HOST) --port $(MLX_PORT) \
	  > /tmp/mlx-27b.log 2>&1 & echo \$$!"
	@echo "MLX 27B avviato su Studio — porta $(MLX_PORT)"
	@echo "Logs: ssh $(STUDIO) tail -f /tmp/mlx-27b.log"

mlx-35b: ## Start MLX server on Studio with Qwen3.6-35B-A3B (background via nohup)
	ssh $(STUDIO) "source $(MLX_VENV) && \
	  HF_HOME=$(MLX_HF_HOME) nohup mlx_lm.server \
	    --model mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit \
	    --host $(MLX_HOST) --port $(MLX_PORT) \
	  > /tmp/mlx-35b.log 2>&1 & echo \$$!"
	@echo "MLX 35B-A3B avviato su Studio — porta $(MLX_PORT)"
	@echo "Logs: ssh $(STUDIO) tail -f /tmp/mlx-35b.log"

mlx-stop: ## Stop MLX server on Studio
	ssh $(STUDIO) "pkill -f 'mlx_lm.server' && echo 'MLX stopped' || echo 'nessun processo MLX attivo'"

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
