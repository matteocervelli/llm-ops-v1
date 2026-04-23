# Modulo 5 Refactor Roadmap

Data: 2026-04-23

## Premessa

No: il primo documento architetturale non era ancora basato sul recap WhatsApp, perche in quel momento l'audio non era stato trascritto.

Questo roadmap invece parte esplicitamente da:

1. brief del modulo 5;
2. slide del corso;
3. stato reale del repo;
4. tua preferenza per `repo + collaboration + GitHub + notebook/Colab/Jupyter + CLI`.

## North Star

Portare `llm-ops-v1` da repo-catalogo a `teaching system` per il modulo 5:

1. coerente con una live online di 3 ore;
2. abbastanza serio da sembrare reale;
3. abbastanza leggero da poter essere capito e riforkato;
4. abbastanza strutturato da sostenere il progetto individuale finale.

## Struttura Di Output Raccomandata

Il corso deve avere tre superfici distinte e coerenti:

### 1. Repository Canonico

Serve per:

1. codice;
2. test;
3. infra;
4. materiale del corso;
5. documentazione;
6. progetto individuale forkabile.

### 2. Notebook Companion

Serve per:

1. progressive reveal della lezione;
2. demo ripetibili;
3. esercizi rapidi;
4. collaborazioni o condivisione live.

Regola: il notebook importa o invoca il repo. Non reimplementa il sistema.

### 3. Slide + Dashboard Prototype

Servono per:

1. spiegare il perche;
2. mostrare segnali operativi;
3. chiudere la lezione con una vista manageriale e operativa.

## Decisioni Da Prendere In Ordine

### Decisione 1 - Superficie primaria della live

Default raccomandato:

1. repo come base;
2. notebook come regia;
3. CLI come prova finale.

Perche:

1. solo repo e troppo asciutto per una live;
2. solo notebook e troppo fragile e poco riusabile;
3. repo + notebook da il miglior compromesso tra didattica e credibilita.

### Decisione 2 - Caso guida unico

Default raccomandato:

un solo `reference agent/service`.

Deve coprire:

1. richiesta utente;
2. costo;
3. contesto/memoria;
4. caching;
5. eval;
6. score/monitoring.

### Decisione 3 - Runtime principale

Default raccomandato:

`CLI task runner` o `minimal worker`, non HTTP app come path principale.

Perche:

1. si demoa meglio in 3 ore;
2. e piu semplice da deployare;
3. lascia meno rumore infrastrutturale.

### Decisione 4 - Dashboard

Default raccomandato:

dashboard prototipale, non full observability suite, ma mostrata subito in apertura della live.

Opzioni pragmatiche:

1. `Streamlit` o vista locale semplice come primary demo surface;
2. `Langfuse` opzionale;
3. export statico per slide.

### Decisione 5 - Collaborazione live

Default raccomandato:

notebook condivisibile, ma repo sempre centrale.

Opzioni pratiche:

1. Colab per friction bassa;
2. JupyterLab RTC se vuoi ambiente piu controllato;
3. Codespaces/JupyterLab come extra, non come requisito.

## Piano Di Refactor

### Fase 1 - Riallineamento Documentale

Obiettivo:

ripulire il framing prima di toccare troppo codice.

Deliverable:

1. brief modulo 5;
2. roadmap refactor;
3. backlog issue;
4. lista fonti per slide;
5. README riposizionato.

### Fase 2 - Spine Della Demo

Obiettivo:

rendere eseguibile il caso guida senza segreti.

Deliverable:

1. lazy model bootstrap;
2. test green senza API key;
3. reference agent piccolo;
4. comando CLI chiaro;
5. notebook companion che usa quel comando o quel package.

### Fase 3 - LLMOps Core

Obiettivo:

mostrare le discipline del modulo, non solo un agente.

Deliverable:

1. cost calculator leggibile;
2. un path di caching;
3. memory/context shaping minimale;
4. eval suite essenziale;
5. score output esportabile.

### Fase 4 - Visibility Layer

Obiettivo:

chiudere il modulo con monitoraggio e segnali.

Deliverable:

1. dashboard prototype;
2. logging strutturato;
3. tracing opzionale;
4. runbook essenziale.

Nota didattica:

la dashboard entra prima nella narrazione della live, ma tecnicamente viene completata quando esistono gia segnali sensati da mostrare.

### Fase 5 - Demo Hardening

Obiettivo:

eliminare il rischio di live failure.

Deliverable:

1. smoke tests locali;
2. dev path in compose;
3. deploy story `VPS + systemd`;
4. fallback demo registrabili;
5. prova generale integrale.

## Backlog Di Issue Consigliato

### Issue 1 - Reposition repo around module 5

Scopo:

allineare README, docs e naming al modulo reale `LLMOps e Operativita`.

Done when:

1. non ci sono piu claim incoerenti con il corso;
2. la home del repo spiega audience, formato e use case.

### Issue 2 - Lock live delivery format

Scopo:

decidere ufficialmente `repo + notebook + CLI`.

Done when:

1. esiste una decisione scritta;
2. e chiaro cosa sta nel notebook e cosa no.

### Issue 3 - Fix zero-key quickstart

Scopo:

far partire il repo senza provider reali.

Done when:

1. `uv run pytest` non richiede `OPENAI_API_KEY`;
2. quickstart locale usa mock/test model.

### Issue 4 - Define the reference service scenario

Scopo:

scegliere il caso guida unico del modulo.

Done when:

1. esiste uno scenario documentato;
2. ogni demo del modulo si aggancia a quello scenario.

### Issue 5 - Split evals from tests and benchmarks

Scopo:

rendere leggibile il layer qualita.

Done when:

1. `tests`, `evals`, `benchmarks` non sono piu mescolati;
2. ogni cartella ha uno scopo evidente.

### Issue 6 - Build notebook companion

Scopo:

preparare una superficie didattica condivisibile.

Done when:

1. esiste almeno un notebook ufficiale;
2. il notebook richiama codice del repo;
3. puo essere eseguito localmente e, se vuoi, in Colab.

### Issue 7 - Add cost and caching demos

Scopo:

mostrare due discipline LLMOps molto concrete.

Done when:

1. c'e un esempio di cost accounting;
2. c'e un esempio di caching spiegabile in pochi minuti.

### Issue 8 - Add context and memory optimization demo

Scopo:

far vedere che memoria e contesto non sono slogan.

Done when:

1. esiste un before/after;
2. i tradeoff sono misurabili o almeno osservabili.

### Issue 9 - Add LLM-as-a-Judge path

Scopo:

mostrare eval continua, non solo testing statico.

Done when:

1. esiste una rubrica;
2. esiste almeno uno score automatico;
3. il risultato e visualizzabile.

### Issue 10 - Add dashboard prototype

Scopo:

chiudere il modulo con una vista operativa.

Done when:

1. costi, score e run sono visibili in un posto solo;
2. la demo non dipende da una piattaforma complessa.

### Issue 11 - Simplify CI and automation

Scopo:

togliere automazioni premature e opache.

Done when:

1. niente branch cleanup automatico;
2. niente auto-issue non essenziali;
3. Actions sottili che chiamano script del repo.

### Issue 12 - Prepare VPS deploy and runbook

Scopo:

chiudere la storia operativa.

Done when:

1. esiste un runtime deployabile davvero;
2. `systemd` punta a un processo reale;
3. esiste un runbook minimo.

### Issue 13 - Prepare course assets

Scopo:

trattare i materiali didattici come parte del prodotto.

Done when:

1. esistono diagrammi Mermaid;
2. esistono sorgenti Excalidraw;
3. esiste outline della live.

### Issue 14 - Dry runs and teaching hardening

Scopo:

verificare il modulo come esperienza, non solo come codice.

Done when:

1. hai una run da 90 minuti e una da 180 minuti;
2. conosci i punti fragili;
3. hai fallback per ogni demo critica.

## Ordine Operativo Consigliato

1. chiudere brief e scelte di formato;
2. fissare il caso guida;
3. sistemare quickstart e runtime base;
4. costruire notebook companion;
5. aggiungere costi, caching, memoria;
6. aggiungere evals e score;
7. aggiungere dashboard prototype;
8. rifinire CI, deploy e runbook;
9. preparare asset e dry run.

## Domande Che Cambiano Davvero Il Disegno

1. Vuoi che il notebook sia solo demo o anche consegnabile agli studenti?
   Default: demo + handout, ma il repo resta consegnabile.

2. Vuoi usare Colab come piattaforma ufficiale o solo come compatibilita opzionale?
   Default: compatibilita opzionale, non source of truth.

3. Vuoi che la dashboard sia locale/statica o appoggiata a Langfuse?
   Default: locale/statica first, Langfuse second.

4. Vuoi che gli studenti eseguano davvero il deploy o che vedano solo la story?
   Default: vedere la story e avere gli artefatti pronti, non eseguire tutti il deploy live.
