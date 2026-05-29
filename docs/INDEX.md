# Docs index

## Materiale sessione

| File                                                         | Contenuto                                                              |
| ------------------------------------------------------------ | ---------------------------------------------------------------------- |
| [00-caso-guida-eval-hitl.md](00-caso-guida-eval-hitl.md)     | Caso guida ticket-to-dashboard, eval, HITL                             |
| [01-cost-and-routing.md](01-cost-and-routing.md)             | Cost estimation, routing keyword + cost-aware                          |
| [02-context-memory-caching.md](02-context-memory-caching.md) | Context, memoria, prefix cache, response cache                         |
| [03-evals-llm-as-a-judge.md](03-evals-llm-as-a-judge.md)     | Evals deterministiche, LLM-as-judge, RAGAS, golden set, drift          |
| [04-monitoring-dashboard.md](04-monitoring-dashboard.md)     | Dashboard Streamlit, KPI, Langfuse, drift PSI, Prometheus              |
| [05-scaling-resilience.md](05-scaling-resilience.md)         | Scaling, code distribuita, rate limiting, circuit breaker, autoscaling |
| [runbook.md](runbook.md)                                     | Runbook operativo: segnali, prime azioni, rollback                     |

## Teoria (opzionale)

Internals LLM: prefill/decode, KV cache, quantizzazione, MoE — [theory/README.md](theory/README.md)

## Risorse

| File                                                   | Contenuto                                                  |
| ------------------------------------------------------ | ---------------------------------------------------------- |
| [resources/reading_list.md](resources/reading_list.md) | Letture di approfondimento per ogni modulo                 |
| [resources/survival_kit.md](resources/survival_kit.md) | Checklist operativa: pre-deploy, in esercizio, pre-scaling |

## Notebook

| File                                                                           | Contenuto                                      |
| ------------------------------------------------------------------------------ | ---------------------------------------------- |
| [../notebooks/module-5-companion.ipynb](../notebooks/module-5-companion.ipynb) | Lab Module 5: evals, drift, alerting, Langfuse |

## Codice chiave per modulo

| Modulo         | Path sorgente                                                                              |
| -------------- | ------------------------------------------------------------------------------------------ |
| Cost + routing | `src/llm_ops_v1/economics/`, `src/llm_ops_v1/agents/router.py`                             |
| Response cache | `src/llm_ops_v1/caching/response_cache.py`                                                 |
| Resilienza     | `src/llm_ops_v1/agents/resilience.py`, `agents/context.py`                                 |
| Scaling        | `src/llm_ops_v1/agents/rate_limit.py`, `agents/queue.py`, `agents/worker.py`               |
| Evals          | `src/llm_ops_v1/evals/` (deterministic, llm_judge, runner, datasets, drift, ragas_adapter) |
| Alerting       | `src/llm_ops_v1/monitoring/alerts.py`                                                      |
| Observability  | `src/llm_ops_v1/observability/` (structured_logging, langfuse_setup)                       |
| Dashboard      | `src/llm_ops_v1/dashboard/`                                                                |
