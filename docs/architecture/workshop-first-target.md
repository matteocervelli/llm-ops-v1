# LLM Ops v1 - Workshop-First Target Design

Data: 2026-04-23

Questo documento resta valido come critica del repo e target architecture, ma da ora va letto insieme a [module-5-brief.md](/data/dev/demo/llm-ops-v1/docs/course/module-5-brief.md:1), che incorpora il recap WhatsApp del 23 aprile 2026 e ridefinisce il source of truth didattico del modulo 5.

## Discovery

### Checkpoint

Conditional go.

Il repo e recuperabile, ma non e ancora un sistema coerente. Oggi vende breadth prima di avere un backbone. Se lo porti pubblico cosi, il messaggio implicito e "production-ready scaffold"; quello che il codice dimostra invece e "raccolta di temi con alcuni moduli utili e molte promesse ancora non chiuse".

### Veri obiettivi del repo

1. Insegnare come portare un agente da PoC a runtime credibile senza introdurre complessita gratuita.
2. Fornire una base forkabile per un singolo `reference agent`, non un catalogo di archetipi.
3. Rendere visibili i tradeoff reali: costo, routing, evals, memoria, tracing, deploy, CI.
4. Supportare una live del 29 maggio 2026 con demo locali ripetibili e failure mode comprensibili.

### Utenti reali

1. Sviluppatore Python pragmatico che vuole un percorso chiaro da demo a produzione semplice.
2. Tech lead o founder che deve scegliere cosa rendere obbligatorio e cosa lasciare opzionale.
3. Partecipante alla live che vuole clonare il repo e far partire qualcosa senza chiavi reali.

Non serve davvero:

1. Team platform avanzati.
2. Organizzazioni multi-service con orchestrazione pesante.
3. Chi cerca un framework generale per agent engineering.

### Cosa il repo comunica oggi, e perche e un problema

1. Il README dice "production-ready" ([README.md](/data/dev/demo/llm-ops-v1/README.md:5)), ma il quickstart esegue solo unit evals isolate ([README.md](/data/dev/demo/llm-ops-v1/README.md:14)).
2. Il modulo agente principale crea il provider OpenAI all'import time ([src/llm_ops_v1/agents/base_agent.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/agents/base_agent.py:15)), quindi `uv run pytest` fallisce in collection senza `OPENAI_API_KEY`.
3. `docker-compose` alza una stack Langfuse completa ma il servizio `app` esegue solo test ([infrastructure/docker-compose.yml](/data/dev/demo/llm-ops-v1/infrastructure/docker-compose.yml:2)).
4. Il service systemd punta a `python -m llm_ops_v1.agents.auto_research` ([infrastructure/vps/agent.service](/data/dev/demo/llm-ops-v1/infrastructure/vps/agent.service:10)), ma quel modulo non espone un worker reale o una loop di processo ([src/llm_ops_v1/agents/auto_research.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/agents/auto_research.py:17)).
5. Le GitHub Actions fanno automazione mutativa prima di avere un sistema stabile: issue creation e branch cleanup automatico ([.github/workflows/auto-agent.yml](/data/dev/demo/llm-ops-v1/.github/workflows/auto-agent.yml:12)).

### Decisioni architetturali premature

1. Presentare tre storie deploy contemporanee (`Compose`, `VPS`, `Fly`) nel README prima di avere un runtime unico da deployare.
2. Mettere in root package sia headless wrappers sia vision integration sia auto-research come se fossero pari livello al core.
3. Introdurre `long_term` come vector store nel core ([src/llm_ops_v1/memory/long_term.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/memory/long_term.py:13)) quando il vincolo v1 dice esplicitamente di non partire da vector DB.
4. Dare a Langfuse una stack quasi completa in compose senza avere tracing integrato nel reference flow.
5. Fare regression workflow che commenta il PR anche se le regression stesse sono ancora mockate con `TestModel` ([tests/evals/regression/test_regression.py](/data/dev/demo/llm-ops-v1/tests/evals/regression/test_regression.py:17)).

### Rischi di scope creep

1. Confondere `repo del corso` con `template universale`.
2. Confondere `headless adapters` con `repo automation`.
3. Mescolare `evals`, `benchmarking` e `observability` come se fossero la stessa disciplina.
4. Portare in v1 integrazioni esterne fragili: Fabrica, serverless, Langfuse full stack, auto-research, cleanup automation.
5. Cercare di mostrare troppi runtime invece di un solo path credibile e un paio di estensioni.

### Stato reale per area

#### Production-ready enough for teaching

1. Cost model e calculator: chiari, piccoli, riusabili ([src/llm_ops_v1/economics/cost_calculator.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/economics/cost_calculator.py:4), [src/llm_ops_v1/economics/commercial_models.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/economics/commercial_models.py:4)).
2. Logging JSON minimo: semplice e leggibile ([src/llm_ops_v1/observability/structured_logging.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/observability/structured_logging.py:6)).
3. Session state ed episodic memory in-memory come contratti didattici iniziali ([src/llm_ops_v1/memory/short_term.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/memory/short_term.py:5), [src/llm_ops_v1/memory/episodic.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/memory/episodic.py:5)).

#### Demo-ready

1. Benchmark primitive ([src/llm_ops_v1/economics/benchmark.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/economics/benchmark.py:9)).
2. Token-based provider clients: utili come adapter sottili, non ancora robusti ([src/llm_ops_v1/agents/token_based/openai_client.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/agents/token_based/openai_client.py:8)).
3. Headless wrappers Claude/Codex: buoni come optional adapter, non come dipendenza di quickstart o CI ([src/llm_ops_v1/agents/claude_headless.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/agents/claude_headless.py:14), [src/llm_ops_v1/agents/codex_headless.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/agents/codex_headless.py:15)).
4. LLM judge con Claude: utile per mostrare il pattern, troppo dipendente da credenziali per il primo path ([src/llm_ops_v1/evals/llm_judge.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/evals/llm_judge.py:22)).

#### Placeholder o misleading

1. `production_agent` attuale ([src/llm_ops_v1/agents/base_agent.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/agents/base_agent.py:15)).
2. Vision client Fabrica ([src/llm_ops_v1/agents/vision_agent.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/agents/vision_agent.py:9)).
3. `long_term` vector store nel core ([src/llm_ops_v1/memory/long_term.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/memory/long_term.py:13)).
4. Langfuse setup come semplice `get_client()` wrapper ([src/llm_ops_v1/observability/langfuse_setup.py](/data/dev/demo/llm-ops-v1/src/llm_ops_v1/observability/langfuse_setup.py:1)).
5. `docker-compose` come pseudo-app ([infrastructure/docker-compose.yml](/data/dev/demo/llm-ops-v1/infrastructure/docker-compose.yml:2)).
6. `agent.service` come runtime production ([infrastructure/vps/agent.service](/data/dev/demo/llm-ops-v1/infrastructure/vps/agent.service:1)).
7. Auto-issue e stale branch cleanup ([.github/workflows/auto-agent.yml](/data/dev/demo/llm-ops-v1/.github/workflows/auto-agent.yml:1)).

## Recommended Design

### Posizionamento

Il repo deve diventare un `workshop-first modular monolith`.

Questo significa:

1. Un solo caso guida end-to-end.
2. Core piccolo, adapters opzionali.
3. Esempi e materiale del corso first-class.
4. Nessuna promessa di platform completeness.

### Target root structure

```text
.
├── src/llm_ops_v1/
│   ├── agent/
│   │   ├── reference_agent.py
│   │   ├── policies.py
│   │   └── tools.py
│   ├── economics/
│   │   ├── cost_calculator.py
│   │   ├── pricing_catalog.py
│   │   └── router.py
│   ├── memory/
│   │   ├── contracts.py
│   │   ├── session.py
│   │   └── episodic.py
│   ├── observability/
│   │   ├── logging.py
│   │   ├── tracing.py
│   │   └── events.py
│   ├── evals/
│   │   ├── contracts.py
│   │   ├── rubrics.py
│   │   └── judges/
│   ├── adapters/
│   │   ├── llm/
│   │   ├── memory/
│   │   ├── observability/
│   │   └── headless/
│   ├── runtime/
│   │   ├── cli.py
│   │   └── worker.py
│   └── __init__.py
├── examples/
│   ├── 01_quickstart_local/
│   ├── 02_evals/
│   ├── 03_langfuse_optional/
│   └── 04_headless_adapters/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── smoke/
│   └── fixtures/
├── infrastructure/
│   ├── docker-compose.yml
│   ├── vps/
│   └── extensions/
│       └── fly/
├── course/
│   ├── diagrams/
│   │   ├── mermaid/
│   │   └── excalidraw/
│   ├── live/
│   └── handouts/
├── scripts/
│   ├── ci/
│   ├── demo/
│   └── release/
└── docs/
    ├── architecture/
    └── decisions/
```

### Boundaries

#### Library code

Sta solo in `src/llm_ops_v1/`.

Deve contenere:

1. Reference agent.
2. Cost accounting e routing minimo.
3. Contratti memoria.
4. Tracing/logging abstractions.
5. Runtime entrypoint chiaro.

Non deve contenere:

1. Materiale del corso.
2. Sequenze numerate didattiche.
3. Workflow GitHub opachi.
4. Integrazioni speculative non usate dal case study.

#### Examples

Stanno in `examples/` e raccontano progressione didattica, non architettura interna.

Qui vanno:

1. Quickstart senza chiavi.
2. Evals locali.
3. Langfuse opzionale.
4. Headless adapters come estensione.

#### Tests

Tre livelli chiari:

1. `unit`: puro Python, nessuna chiave, nessun network.
2. `integration`: reference agent con fake adapters o local adapters.
3. `smoke`: demo locali eseguibili prima della live.

`tests/evals/...` oggi mescola tassonomie concettuali e tipologie di test. Va separato.

#### Infra

`infrastructure/` deve descrivere come eseguire davvero il runtime, non come far girare pytest in un container.

Path v1:

1. `docker-compose.yml` per demo locale con app/worker e Langfuse opzionale.
2. `vps/` per deploy principale con `systemd`.

Path estesi:

1. `extensions/fly/` o simile.

#### Course materials

`course/` diventa first-class.

Dentro:

1. `diagrams/mermaid/` per flow e sequence.
2. `diagrams/excalidraw/` per asset visivi della live.
3. `live/` per outline, talking points, demo order.

#### Automation

La logica va in `scripts/`. Le GitHub Actions devono solo chiamare script del repo.

Regola: niente automazione che apra issue, cancelli branch o invochi headless agents finche il runtime base non e stabile e osservabile.

### Cosa deve stare nel core v1

1. Un `reference agent` text-first con massimo 2-3 tool.
2. Provider selection minimale: mock/local first, hosted optional.
3. Cost tracking per request e per run.
4. Session state + episodic memory con contratti chiari.
5. Structured logging.
6. Tracing opzionale con Langfuse.
7. CLI o worker runtime eseguibile davvero.
8. Test green senza chiavi API.
9. Evals minime ripetibili e separate dai benchmark.
10. Deploy story primaria `VPS + systemd`.

### Cosa deve stare in v1.1 o in esempi separati

1. Headless Claude e Codex.
2. Langfuse full stack demo.
3. Serverless/Fly.
4. Vision/Fabrica.
5. Auto-research loop.
6. Multi-provider benchmark comparativi live.
7. Persistenza piu ricca della memoria.

### Separazioni richieste

#### Evals

Scopo: misurare se l'agente fa la cosa giusta.

Devono avere:

1. Dataset o fixtures.
2. Rubriche.
3. Judge contract.
4. Output di pass/fail e score.

Non devono inglobare benchmark o tracing.

#### Benchmarking

Scopo: costi, latenza, stabilita tra modelli o config.

Deve stare fuori da `evals/`, idealmente in `examples/` o `scripts/benchmark/`.

#### Memory

Per v1:

1. `SessionStore`.
2. `EpisodicStore`.
3. Adapter in-memory obbligatorio.

Fuori dal core iniziale:

1. Vector store.
2. Semantic retrieval.
3. RAG generico.

#### Observability

Layer distinti:

1. logging strutturato sempre disponibile.
2. tracing opzionale.
3. cost events collegati al reference flow.

#### Headless adapters

Devono stare in `adapters/headless/` e avere:

1. interfaccia comune.
2. feature flag o import opzionale.
3. zero impatto su quickstart e CI.

#### Repo automation

Fuori dal core. Deve stare in `scripts/ci/` o `scripts/repo/`.

Deve essere:

1. esplicita.
2. leggibile.
3. disattivabile.

## Scope Cuts

### Da togliere subito dal path principale

1. Auto issue creation su CI failure.
2. Stale branch cleanup automatico.
3. Vision/Fabrica dal core.
4. Fly.io dal README principale.
5. `long_term` vector store dal core story.
6. Narrazione "production-ready scaffold" finche quickstart e test non sono davvero coerenti.

### Da posticipare

1. Headless orchestration reale.
2. Auto-research agent operativo.
3. Full Langfuse stack nella demo principale.
4. Serverless deploy.
5. Benchmark provider live con chiavi multiple.

### Da tenere assolutamente per la live

1. Un case study unico e concreto.
2. Cost calculator e model-routing rationale.
3. Evals minime ma vere.
4. Memory semplice e spiegabile.
5. Logging e tracing opzionale.
6. Deploy `VPS + systemd`.
7. Diagrammi Mermaid ed Excalidraw nel repo.

### Troppo fragile da mostrare live

1. Qualsiasi flow che dipenda da provider esterni per far partire il quickstart.
2. Qualsiasi demo che richieda headless CLI installate sulla macchina dei partecipanti.
3. Qualsiasi benchmark in tempo reale su piu provider senza controllo di rate limit o credito.
4. Qualsiasi "production worker" che in realta esegue un modulo senza main loop.

## Decision Log

1. Scelta: repo `workshop-first`.
   Alternative scartate: framework generico, catalogo enciclopedico.
   Motivo: teachability e credibilita battono breadth.

2. Scelta: un solo `reference agent`.
   Alternative scartate: piu agenti tematici in parallelo.
   Motivo: un caso completo spiega meglio di cinque stub.

3. Scelta: quickstart senza chiavi API.
   Alternative scartate: quickstart con OpenAI/Anthropic obbligatori.
   Motivo: onboarding e CI non devono dipendere da segreti.

4. Scelta: inizializzazione lazy dei provider.
   Alternative scartate: provider creati all'import.
   Motivo: test collection e tooling locale devono funzionare sempre.

5. Scelta: `VPS + systemd` come deploy story primaria.
   Alternative scartate: Fly-first, K8s/ECS.
   Motivo: e il percorso piu pragmatico e insegnabile per il pubblico target.

6. Scelta: `Docker Compose` solo per dev/demo locale.
   Alternative scartate: farlo sembrare un ambiente production-like.
   Motivo: oggi serve solo a sostenere demo locali e servizi opzionali.

7. Scelta: `Fly.io` fuori dal path principale.
   Alternative scartate: tenerlo nel README al pari del VPS.
   Motivo: moltiplica i rami decisionali troppo presto.

8. Scelta: separare `evals` da `benchmarking`.
   Alternative scartate: un unico contenitore "quality".
   Motivo: misurano cose diverse e creano confusioni didattiche diverse.

9. Scelta: memoria v1 limitata a sessione + episodic.
   Alternative scartate: vector DB, RAG, long-term semantic search nel core.
   Motivo: il corso parla di produzione pragmatica, non di breadth infra.

10. Scelta: Langfuse importante ma opzionale.
    Alternative scartate: renderlo prerequisito del first run.
    Motivo: tracing utile, ma non deve bloccare la comprensione del flow base.

11. Scelta: Claude e Codex headless come adapters opzionali.
    Alternative scartate: dipendenze hard del runtime o della CI.
    Motivo: devono esistere nel design, non nel critical path.

12. Scelta: GitHub Actions sottili, logica nel repo.
    Alternative scartate: business logic in YAML o `github-script`.
    Motivo: leggibilita, testabilita, portabilita.

13. Scelta: `course/diagrams/{mermaid,excalidraw}` nel repo.
    Alternative scartate: diagrammi sparsi fuori repo o solo export PNG.
    Motivo: gli asset didattici devono essere versionati e diffabili.

14. Scelta: documentazione in italiano, codice e contratti in inglese.
    Alternative scartate: tutto in inglese o tutto in italiano.
    Motivo: allinea il repo al corso senza degradare naming tecnico e reuse.

15. Scelta: tagliare automazioni mutative fino a maturita reale.
    Alternative scartate: issue bot, branch janitor, auto delegation.
    Motivo: automazione prematura in un repo didattico sembra teatro, non ops.

## Execution Plan

### Milestone 1 - Repositioning

Finestra: 2026-04-24 -> 2026-05-01

1. Riscrivere positioning e quickstart.
2. Rimuovere claim `production-ready` non supportati.
3. Definire il `reference agent` e il caso guida.
4. Spostare o de-enfatizzare serverless, vision, auto-research.

Exit criteria:

1. Un lettore capisce in 2 minuti cosa il repo fa davvero.
2. Il quickstart non promette percorsi che il repo non sostiene.

### Milestone 2 - Core Runtime

Finestra: 2026-05-02 -> 2026-05-08

1. Rendere lazy il bootstrap dei provider.
2. Introdurre runtime vero: `cli` o `worker` eseguibile.
3. Tenere il core su un solo reference flow.

Exit criteria:

1. `uv run pytest` verde senza chiavi.
2. Esiste un entrypoint che fa partire il reference flow davvero.

### Milestone 3 - Quality Loops

Finestra: 2026-05-09 -> 2026-05-15

1. Separare test, evals e benchmark.
2. Introdurre smoke test locali.
3. Rendere le Actions semplici wrapper di script del repo.

Exit criteria:

1. CI lineare e leggibile.
2. Nessuna automazione mutativa opaca.

### Milestone 4 - Demo Infra

Finestra: 2026-05-16 -> 2026-05-22

1. `docker-compose` coerente con app/worker reali.
2. `systemd` su runtime effettivo.
3. Langfuse opzionale, non obbligatorio.

Exit criteria:

1. Demo locale ripetibile.
2. Story VPS credibile e documentata.

### Milestone 5 - Course Assets And Freeze

Finestra: 2026-05-23 -> 2026-05-27

1. Aggiungere diagrammi Mermaid ed Excalidraw sorgente.
2. Chiudere outline live e ordine demo.
3. Fare almeno due dry run locali complete.

Exit criteria:

1. Niente dipendenze improvvisate il giorno della live.
2. Ogni demo ha fallback predefinito.

### Demo locali da validare prima del 29 maggio 2026

1. Quickstart senza chiavi reali.
2. Reference agent con mock/local model.
3. Evals minime ripetibili.
4. Logging leggibile.
5. Tracing opzionale attivabile.
6. Deploy demo su VPS con `systemd`.

## Open Questions

1. Il reference runtime principale deve essere `CLI task worker` o `minimal HTTP service`?
   Default scelto: `CLI task worker`.
   Motivo: piu semplice da spiegare, deployare e testare in una live di 3 ore.

2. Il primo quickstart senza chiavi deve usare `mock/test model` o `Ollama`?
   Default scelto: `mock/test model` nel quickstart, `Ollama` come step successivo.
   Motivo: zero prerequisiti batte quasi-zero prerequisiti.

3. Fabrica/vision e davvero parte del corso o solo un'integrazione disponibile?
   Default scelto: integrazione opzionale fuori dal core.
   Motivo: non cambia la tesi del corso e aumenta solo fragilita.

4. Vuoi che il repo pubblico insegni anche repo automation GitHub o solo agent runtime ops?
   Default scelto: solo il minimo necessario per quality gates.
   Motivo: altrimenti il repo deraglia verso DevEx/automation showcase.
