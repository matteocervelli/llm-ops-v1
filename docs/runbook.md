# Runbook operativo — LLM Ops v1

Incident response per il triage agent in produzione.

## Segnali e prime azioni

### Latenza p95 alta

**Sintomo:** p95 latency > 5000 ms nel dashboard (pannello KPI o alert `p95_latency_ms`).

**Prime azioni:**

1. Controlla lo status del provider (Anthropic: status.anthropic.com, OpenAI: status.openai.com).
2. Verifica `LLM_OPS_CLAUDE_MAX_BUDGET_USD` — un cap troppo basso può causare timeout forzati.
3. Controlla la profondità della coda se stai usando il path async (`GET /webhook/ticket/{id}` — se molti job sono in "pending", il worker è in ritardo).
4. Riavvia il servizio distribuito: `systemctl restart llm-ops-v1`.
5. Se il problema è del provider: il circuit breaker apre automaticamente dopo `failure_threshold` (default 5) fallimenti consecutivi.

### Cost drift in salita

**Sintomo:** `avg_cost_usd` sopra soglia, o trend in crescita nel grafico costo/run.

**Prime azioni:**

1. Controlla `cache_hit_ratio` — un calo del ratio significa meno cache hit (vedi sezione cache).
2. Controlla il routing: se i ticket complessi aumentano, più job vanno a Sonnet invece di Haiku.
3. Verifica `DAILY_SPEND_CAP_USD` — se non impostato, non c'è freno automatico.
4. Controlla se un prompt è cambiato e ha invalidato la cache prefix (chiave SHA-256 cambia).

### Eval score in calo

**Sintomo:** `avg_eval_score` scende sotto la soglia (default 5.0), o la regression suite fallisce.

**Prime azioni:**

1. Esegui il golden set manualmente: `uv run pytest tests/evals/regression/ -v`.
2. Se il deterministic judge passa, il problema è probabilmente nel modello live o nel prompt runtime.
3. Controlla se il provider ha cambiato il modello di default (provider drift).
4. Se usi un judge live, confronta modello, rubric e dataset con l'ultima run stabile.

### Escalation surge

**Sintomo:** `escalation_rate` > 50% o alert `escalation_rate`.

**Prime azioni:**

1. Controlla se i ticket in ingresso hanno cambiato pattern (data drift — PSI alert `psi_action`).
2. Verifica il routing: `decide_form()` escalate su ticket ambigui — se molti arrivano senza keyword di topic, vengono escalati.
3. Guarda i prompt delle ultime 10 richieste nel tab "Recent runs" del dashboard.

### Circuit breaker aperto

**Sintomo:** le risposte del webhook ritornano `{"error": "Circuit is open; call blocked."}`.

**Prime azioni:**

1. Il breaker si chiude automaticamente dopo `recovery_timeout` (default 30s) se il provider è tornato disponibile.
2. Forza la recovery: riavvia il processo webhook (risetterà lo state in-memory).
3. Verifica il provider con un curl diretto prima di riaprire.

### Coda bloccata / worker fermo

**Sintomo:** `GET /webhook/ticket/{id}` ritorna `"status": "pending"` indefinitamente.

**Prime azioni:**

1. Verifica che il servizio sia attivo: `systemctl status llm-ops-v1`.
2. Verifica Redis: `redis-cli -u $REDIS_URL ping`.
3. Controlla i log del servizio: `journalctl -u llm-ops-v1 -n 50`.
4. Se usi il worker async separato, riavvialo con il comando previsto dal tuo deploy.

## Dashboard da monitorare

| Dashboard         | URL                     | Cosa guarda                           |
| ----------------- | ----------------------- | ------------------------------------- |
| LLM Ops Streamlit | `http://localhost:8501` | KPI, eval score, cost, latency, cache |
| Langfuse traces   | `$LANGFUSE_HOST`        | Trace per-request, span, usage token  |

## Rollback

Se un deploy introduce una regressione:

1. `git revert <commit>` e redeploy: `./infrastructure/vps/deploy.sh`.
2. Il golden regression test gira in CI su ogni PR — usa il report per identificare la causa.
3. Se il problema è un cambio di prompt: ripristina `SUPPORT_TRIAGE_SYSTEM_PROMPT` in `agents/base_agent.py`.
