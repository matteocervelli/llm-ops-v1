# Reference Scenario - Support Triage And Response Agent

Data: 2026-04-23

## Decision

Il caso guida ufficiale del modulo 5 e:

`un agente di support triage e response drafting per ticket operativi`

Non e un chatbot generico. Non e un multi-agent system. Non e un research agent.

## Perche Questo Scenario

Serve bene il modulo perche rende naturali tutti i temi LLMOps:

1. volume di richieste nel tempo;
2. costo per ticket e per giorno;
3. code e carico variabile;
4. contesto cliente e sessione;
5. caching di parti statiche;
6. evals su qualita, correttezza ed escalation;
7. dashboard con KPI comprensibili;
8. runbook ed escalation operativa.

## Cosa Fa Il Reference Agent

Input:

1. ticket o richiesta utente;
2. priorita;
3. contesto cliente minimo;
4. knowledge snippets o policy snippets;
5. storico essenziale della conversazione.

Output:

1. categoria del ticket;
2. bozza di risposta;
3. decisione `reply / ask_clarification / escalate`;
4. costo stimato;
5. score o segnali di qualita;
6. trace/run id.

## Perche Non Altri Scenari

### Non autoresearch

E troppo affascinante e troppo fragile.

Sposta il fuoco su:

1. repository automation;
2. autonomous loops;
3. headless orchestration.

Questo e interessante, ma non e il cuore del modulo 5.

### Non code agent

E troppo vicino al tema "agent engineering" del resto del corso e rischia di trascinare:

1. tool use complesso;
2. codice non deterministico;
3. discussioni troppo ampie su benchmark da coding.

### Non general business copilot

E troppo vago.

Ti serve un caso con KPI e failure mode chiari.

## Mapping Didattico

### Costi

1. costo per ticket;
2. costo per classe di ticket;
3. hosted vs local/open weight.

### Caching

1. policy e system prompt statici;
2. rubriche eval statiche;
3. knowledge fragments ricorrenti.

### Context And Memory

1. session state per conversazione;
2. episodic memory corta;
3. customer context limitato e spiegabile.

### Evals

1. correttezza della classificazione;
2. qualita della risposta;
3. correttezza della decisione di escalation.

### Dashboard

1. volume run;
2. costi;
3. latency;
4. eval scores;
5. escalation rate;
6. cache hit ratio.

## Architettura Minima Del Caso Guida

1. un runtime CLI che processa richieste da fixture o file;
2. un layer agent molto piccolo;
3. adapters per model provider;
4. score exporter;
5. dashboard locale prototipale;
6. tracing opzionale.

## Demo Sequence Fit

Questo scenario funziona bene sia in:

1. notebook;
2. terminale;
3. dashboard.

Questa e la ragione principale per cui e il caso guida giusto.
