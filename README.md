# LLM Ops v1

Repository companion per la sessione live **"Agents in Production"** del **29 maggio 2026**.

Questo repo non è un tutorial. È un punto di partenza production-ready da forkare, rompere, adattare.

## Quick start

```bash
git clone https://github.com/matteocervelli/llm-ops-v1.git
cd llm-ops-v1
cp .env.example .env
uv sync
uv run pytest tests/evals/unit/
```

## Moduli

Nota: il codice è stato normalizzato sotto `src/llm_ops_v1/` per mantenere un layout Python valido e importabile.

| Folder                                 | Argomento                                                                        | Quando usarlo                                                              |
| -------------------------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `src/llm_ops_v1/economics`             | costi, routing, benchmark                                                        | quando devi stimare costi, confrontare provider o fare model routing       |
| `src/llm_ops_v1/evals` + `tests/evals` | evals LLM-as-judge, unit/integration/regression                                  | quando vuoi bloccare regressioni prima di mandare un agente in produzione  |
| `src/llm_ops_v1/memory`                | short-term, long-term, episodic memory                                           | quando il comportamento dell'agente dipende da stato e memoria persistente |
| `src/llm_ops_v1/agents`                | agenti Pydantic AI, wrapper headless, token-based clients, vision, auto-research | quando devi passare da demo locale a automazione reale                     |
| `src/llm_ops_v1/observability`         | Langfuse e logging strutturato                                                   | quando devi capire costi, latenza, errori e qualità in esercizio           |
| `infrastructure`                       | Docker Compose, VPS, serverless                                                  | quando devi fare deploy e scegliere il modello operativo                   |
| `.github/workflows`                    | CI, regression evals, repo automation                                            | quando vuoi introdurre disciplina operativa e automazioni GitHub           |
| `resources`                            | materiali di studio e checklist                                                  | quando prepari approfondimenti, demo e handout                             |

## Stack

Pydantic AI · Langfuse · Ollama · OpenRouter · Claude Agent SDK · Codex CLI SDK

## Infrastruttura — 3 livelli

| Livello        | Quando usarlo                                |
| -------------- | -------------------------------------------- |
| Docker Compose | dev locale e demo rapide                     |
| VPS + systemd  | produzione semplice, full control            |
| Fly.io         | serverless, deploy veloci e scala automatica |

K8s/ECS: fuori scope. Ha senso quando hai molti servizi, più ambienti e un team dedicato.

## Auto-research agent

Ispirato al pattern Karpathy: gap → ricerca → sintesi → aggiorna knowledge base → itera.

## Reading list

→ [resources/reading_list.md](resources/reading_list.md)

## LLM Ops Survival Kit

→ [resources/survival_kit.md](resources/survival_kit.md)
