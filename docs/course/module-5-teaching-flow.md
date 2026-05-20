# Module 5 Teaching Flow

Data: 2026-04-23

## Principle

La dashboard non va lasciata solo alla fine.

Va mostrata all'inizio come `control surface`, poi riaperta durante il modulo per spiegare da dove arrivano i segnali.

## Recommended 3-Hour Structure

### 1. Cold Open - Dashboard First

> 📊 `course/diagrams/excalidraw/23-dashboard-mockup.excalidraw` — mostra all'inizio come control surface

Durata: 10-15 minuti

Obiettivo:

partire dal problema operativo, non dal codice.

Mostra:

1. run volume;
2. latency;
3. costi;
4. score eval;
5. escalation rate;
6. magari un confronto tra due versioni o due provider.

Messaggio:

`questa e la vista che un team vuole avere quando l'agente e in produzione`

### 2. Why LLMOps Exists

> 📊 `course/diagrams/excalidraw/17-llmops-layer-stack.excalidraw` — 5 layer operativi

Durata: 15-20 minuti

Obiettivo:

spiegare perche un PoC non basta.

Temi:

1. costi che crescono con il volume;
2. qualita che driftano;
3. latenza;
4. operativita;
5. runbook;
6. differenza tra "funziona una volta" e "regge nel tempo".

### 3. Repo And Scenario Orientation

> 📊 `course/diagrams/excalidraw/19-scenario-agent-io.excalidraw` — contratto I/O agente triage

Durata: 15 minuti

Obiettivo:

presentare il caso guida e la struttura del repo.

Mostra:

1. scenario ticket triage;
2. repo structure;
3. notebook companion;
4. CLI entrypoint;
5. dashboard surface.

### 4. Cost And Routing

> 📊 `course/diagrams/excalidraw/20-cost-routing.excalidraw` — decision tree + volume math

Durata: 25 minuti

Obiettivo:

far vedere il primo layer operativo.

Mostra:

1. hosted vs local/open weight;
2. model routing rationale;
3. costo per request;
4. volume math.

### 5. Context, Memory And Caching

> 📊 `course/diagrams/excalidraw/21-context-caching-strategy.excalidraw` — cosa cachare vs cosa no

Durata: 30 minuti

Obiettivo:

far vedere il secondo layer operativo.

Mostra:

1. session state;
2. episodic memory minima;
3. cosa tenere statico per il caching;
4. cosa non mettere in memoria.

### 6. Evals And LLM-as-a-Judge

> 📊 `course/diagrams/excalidraw/22-eval-pipeline.excalidraw` — pipeline 4 step

Durata: 30 minuti

Obiettivo:

portare il discorso dalla "sensazione" alla misura.

Mostra:

1. rubrica;
2. dataset piccolo;
3. score automatici;
4. limiti di `LLM-as-a-Judge`.

### 7. Dashboard Revisit

> 📊 `course/diagrams/excalidraw/18-dashboard-signal-flow.excalidraw` + `23-dashboard-mockup.excalidraw`

Durata: 20 minuti

Obiettivo:

ricollegare tutti i pezzi ai segnali.

Mostra:

1. da dove arrivano i numeri;
2. come interpretare score e costi;
3. quando investigare;
4. cosa cambieresti tra v1 e v1.1.

### 8. Runtime, Deploy And Runbook

> 📊 `course/diagrams/excalidraw/24-runtime-deploy-stack.excalidraw` — 3 livelli di maturità

Durata: 15-20 minuti

Obiettivo:

chiudere la storia operativa.

Mostra:

1. CLI o worker;
2. `Compose` per demo;
3. `VPS + systemd` come path principale;
4. runbook essenziale.

### 9. Project Handoff

Durata: 10 minuti

Obiettivo:

collegare il modulo al progetto individuale.

Mostra:

1. cosa deve finire nel repo degli studenti;
2. che metriche devono mostrare;
3. che cosa basta per essere credibili.

## Delivery Surfaces

1. dashboard all'inizio e alla fine;
2. notebook per walkthrough guidato;
3. terminale per i comandi chiave;
4. repo come base di tutto.

## Default Dashboard Stack

Default raccomandato:

1. `Streamlit` o dashboard locale semplice come primary surface;
2. `Langfuse` come estensione o deep-dive opzionale.

Motivo:

1. Streamlit ti da controllo totale sulla storia didattica;
2. Langfuse e ottimo, ma non deve diventare prerequisito della live.
