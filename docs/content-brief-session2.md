# Content Brief — Sessione 2 (29 maggio 2026)

**Titolo:** LLM Ops — Agents in Production
**Durata:** 3 ore (165 min contenuto + 15 min pause)
**Pubblico:** Developer che hanno già un agente funzionante localmente, primo contatto strutturato con operatività
**Obiettivo:** Passare da "funziona sul mio laptop" a "regge nel tempo" — costi controllati, qualità misurabile, deploy ripetibile

---

## Blocco 1: Cold Open — Dashboard First (15min)

- **Key message:** Non partiamo dal codice, partiamo dal problema operativo. Questa è la vista che un team vuole avere quando l'agente è in produzione.

- **Demo artifact:**
  1. **Dashboard live (10 min):** 📊 `course/diagrams/excalidraw/23-dashboard-mockup.excalidraw` — mostra la control surface: run volume, latency, costi, eval score, escalation rate, confronto tra due versioni/provider. "Tutto ciò che costruiremo oggi alimenta questi numeri."
  2. **Perché LLMOps esiste (5 min):** 📊 `course/diagrams/excalidraw/17-llmops-layer-stack.excalidraw` — 5 layer operativi. Il passaggio da PoC a produzione non è un upgrade tecnico — è un cambio di domanda: da "funziona?" a "regge nel tempo?".

- **Esempio concreto:** Dashboard Streamlit del repo `llm-ops-v1` già configurata. Nessun setup live — aperta prima della sessione.

- **Cut:** Nessuna installazione Langfuse live. L'architettura di osservabilità è mostrata come concetto, non configurata da zero.

> 📚 **Reading list Blocco 1:** [How AI Is Transforming Work at Anthropic](https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic) · [Anthropic Economic Index — Primitives](https://www.anthropic.com/research/anthropic-economic-index-january-2026-report) · [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)

---

## Blocco 2: Scenario e Repo Orientation (15min)

- **Key message:** Il caso guida è un agente di ticket triage. Semplice, ma abbastanza reale da avere tutti i problemi operativi che contano.

- **Demo artifact:**
  1. **Scenario (5 min):** 📊 `course/diagrams/excalidraw/19-scenario-agent-io.excalidraw` — contratto I/O dell'agente: input (ticket testo + metadata), output (categoria + priorità + draft response). Mostra cosa può fallire: categoria sbagliata, risposta fuori tono, costo per ticket che esplode.
  2. **Repo walkthrough (10 min):** struttura `src/llm_ops_v1/` — `agents/`, `evals/`, `economics/`, `observability/`. Notebook companion. CLI entrypoint. "Ogni cartella risponde a uno dei 5 layer operativi."

- **Esempio concreto:**
  - `src/llm_ops_v1/agents/` — agente triage con Pydantic AI
  - `uv run python -m llm_ops_v1.agents.triage --ticket "..."` — output immediato

- **Cut:** Non si apre ogni file del repo. Il walkthrough è orientativo, non esaustivo.

---

## Blocco 3: Cost And Routing (25min)

- **Key message:** Il costo non è un dettaglio — è un vincolo di design. La scelta del modello è una decisione economica, non tecnica.

- **Demo artifact:**
  1. **Decision tree routing (10 min):** 📊 `course/diagrams/excalidraw/20-cost-routing.excalidraw` — hosted vs local/open weight, routing rationale, costo per request, volume math. Mostra il costo che scala con il volume.
  2. **Opusplan pattern (5 min):** Opus pianifica (15×), Sonnet implementa (3×). Su 200 token piano + 2000 token esecuzione: All-Opus $0.033 → Opusplan $0.008, risparmio 76%. Demo `router.py`: 3 ticket, 3 modelli, 3 costi stampati. "Rendi il routing visibile."
  3. **Headless batch con budget cap (10 min):** `claude -p` in parallelo con `--max-budget-usd 0.05` per ticket. Nessun invocazione runaway. Pattern per batch notturno ad alto volume.

- **Esempio concreto:**
  - `src/llm_ops_v1/economics/router.py` — routing con 3 modelli
  - `src/llm_ops_v1/economics/` — cost tracking, benchmark

- **Cut:** Nessun deep dive su provider pricing specifici. OpenRouter configurazione base mostrata, non spiegata in dettaglio.

> 📚 **Reading list Blocco 3:** [Mass Intelligence — From GPT-5 to Nano Banana](https://www.oneusefulthing.org/p/mass-intelligence) (Mollick: cost collapse) — ⚠️ **Gap**: manca fonte dedicata su OpenRouter routing e token budgeting — aggiungere da https://openrouter.ai/docs

---

## Blocco 4: Context, Memory And Caching (30min)

- **Key message:** La sessione è effimera, il sistema deve essere progettato per gestirlo. Cosa metti in context è una decisione economica oltre che tecnica.

- **Demo artifact:**
  1. **RAG/CAG/KG framing (10 min):** 📊 `course/diagrams/excalidraw/21-context-caching-strategy.excalidraw` — cosa cachare vs cosa no. System prompt (regole statiche, template) = **CAG** — sempre in context, zero latency. Ticket history = **RAG** — recuperato on demand. Customer tier → SLA rules = **KG** — non in v1, ma lo step naturale.
  2. **Prompt caching live (10 min):** 📊 `course/diagrams/excalidraw/28-prompt-cache-flow.excalidraw` — TTL 5 minuti. Se aspetti >5 min tra ticket, paghi full input cost da zero. Progetta il system prompt per essere massimamente stabile: ogni modifica invalida la cache per tutte le richieste inflight.
  3. **Memory pattern (10 min):** 📊 `course/diagrams/excalidraw/10-memory-flow.excalidraw` — continuazione da Session 1. Episodic memory minima. Cosa NON mettere in memoria (segreti, dati PII, stato che cambia spesso).

- **Esempio concreto:**
  - `src/llm_ops_v1/memory/` — short-term, long-term, episodic memory
  - Caching con `cache_control` nel system prompt dell'agente triage
  - [Karpathy LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) come pattern di riferimento per memory senza vector DB

> 📚 **Reading list Blocco 4:** [Karpathy LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) · [Embeddings in RAG LLMs](https://coralogix.com/ai-blog/understanding-the-role-of-embeddings-in-rag-llms/) · [Turn ANY Website into LLM Knowledge](https://www.youtube.com/watch?v=JWfNLF_g_V0) · [Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — ⚠️ **Gap**: manca fonte su CAG vs RAG distinction e KG framing

---

## Blocco 5: Evals And LLM-as-a-Judge (30min)

- **Key message:** Dalla "sensazione" alla misura. Un agente senza eval è un agente che non sai se funziona — finché non fallisce in prod.

- **Demo artifact:**
  1. **Rubrica e dataset piccolo (10 min):** 📊 `course/diagrams/excalidraw/22-eval-pipeline.excalidraw` — pipeline 4 step. Come costruire una rubrica: "Come scoreresti una risposta di triage perfetta?" Mostra il processo, non il risultato finale. Dataset minimo: 20-50 esempi con ground truth.
  2. **LLM-as-a-Judge live (10 min):** Score automatici su un batch di risposte. Limiti espliciti: cosa un LLM judge non può rilevare (tone drift sottile, bias sistematici su certi ticket, errori fattuali domain-specific).
  3. **Guardrails vs Evals (10 min):** Tabella comparativa — guardrails = singola risposta, real-time, block/escalate; evals = qualità aggregata, periodica, informa i cambiamenti. "Hai bisogno di entrambi. Guardrails senza evals = previeni disastri ma drifti lentamente. Evals senza guardrails = sai che la qualità degrada ma non puoi bloccare i singoli output cattivi."

- **Esempio concreto:**
  - `src/llm_ops_v1/evals/` + `tests/evals/` — LLM-as-judge, unit/integration/regression
  - Rubrica reale per l'agente triage: category accuracy, response tone, SLA compliance

- **Cut:** Framework di eval complessi (RAGAS, DeepEval internals). La sezione introduce il concetto e mostra un caso pratico — non è un corso su framework.

> 📚 **Reading list Blocco 5:** [Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents) (evals su tool) · [Anthropic Economic Index — Primitives](https://www.anthropic.com/research/anthropic-economic-index-january-2026-report) (5 primitivi di misura) · [AI Agents Learning Roadmap](https://www.youtube.com/watch?v=k-Cj6H6Zwos) (Langfuse, Pydantic AI) — ⚠️ **Gap critico**: manca fonte su LLM-as-Judge limits e rubric design — aggiungere https://hamel.dev/blog/posts/evals/

---

## Blocco 6: Dashboard Revisit (20min)

- **Key message:** Ricollegare tutto ai segnali. La dashboard non è un report — è un sistema di allerta che ti dice quando investigare.

- **Demo artifact:**
  1. **Rilettura segnali (10 min):** 📊 `course/diagrams/excalidraw/18-dashboard-signal-flow.excalidraw` + `23-dashboard-mockup.excalidraw` — da dove arrivano i numeri. Run volume → latency → costi → eval score → escalation rate. Come interpretare score e costi insieme. Quando investigare (threshold di allerta).
  2. **v1 → v1.1 (10 min):** "Guardando questa dashboard, cosa cambieresti?" Esercizio guidato: identifica 2-3 segnali che indicano un problema, proponi un cambiamento. Mostra come il ciclo di miglioramento diventa iterativo, non episodico.

- **Esempio concreto:**
  - Dashboard Streamlit con dati reali del run dimostrativo
  - Langfuse come estensione opzionale per team che vogliono più profondità

> 📚 **Reading list Blocco 6:** [Collaborating with AI Agents](https://arxiv.org/abs/2503.18238) (jagged frontier, come misurare) · [Microsoft New Future of Work 2025](https://www.microsoft.com/en-us/research/publication/new-future-of-work-report-2025/) (workslop, collective productivity) — ⚠️ **Gap**: manca fonte dedicata su osservabilità LLM/Langfuse — aggiungere https://langfuse.com/docs

---

## Blocco 7: Runtime, Deploy And Runbook (20min)

- **Key message:** Un agente che funziona ma non si può deployare non è in produzione. Il deployment non è un dettaglio finale — è una decisione che si prende all'inizio.

- **Demo artifact:**
  1. **3 livelli di maturità (10 min):** 📊 `course/diagrams/excalidraw/24-runtime-deploy-stack.excalidraw` — CLI (locale, dev) → Docker Compose (demo, staging) → VPS + systemd (produzione semplice, full control). K8s fuori scope — ha senso con molti servizi, più ambienti, team dedicato.
  2. **Runbook essenziale (10 min):** Cosa deve stare nel runbook minimo: come avviare, come fermare, come sapere se sta girando, dove guardare i log, come rollback. Live su `infrastructure/` del repo.

- **Esempio concreto:**
  - `infrastructure/` — Docker Compose, VPS config
  - Runbook template: 5 sezioni, una pagina

- **Cut:** Kubernetes, ECS, serverless (citati come esistenti, non approfonditi). Deploy automation CI/CD (cenno finale).

---

## Blocco 8: Project Handoff (10min)

- **Key message:** Il progetto individuale non è un esercizio — è la prova che sai fare tutto questo su un problema tuo.

- **Demo artifact:**
  1. **Criteri di credibilità (5 min):** Cosa deve finire nel repo: agente funzionante, eval con score, dashboard con almeno 3 metriche, runbook. "Non serve che sia perfetto — serve che sia misurabile."
  2. **Q&A guidato (5 min):** Raccolta delle domande emerse durante la sessione. Dove trovare supporto dopo.

- **Cut:** Nessuna review individuale dei progetti. Nessuna demo live di un progetto studente.

---

## Note Trasversali

**Stack osservabilità raccomandato:**

- Default: Streamlit locale (già nel repo)
- Estensione: Langfuse (setup in 15 min con Docker Compose)

**Gap fonti da colmare prima della sessione:**
| Topic | Fonte da aggiungere |
|-------|---------------------|
| OpenRouter routing | https://openrouter.ai/docs |
| LLM-as-Judge pratico | https://hamel.dev/blog/posts/evals/ |
| Langfuse setup | https://langfuse.com/docs |
| Guardrails framework | NeMo Guardrails docs |

**Timing totale:** 165 min contenuto (15+15+25+30+30+20+20+10) + 15 min pause = 3h
