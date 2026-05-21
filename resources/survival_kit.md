# LLM Ops Survival Kit

## Claude Code — Context Management

- Imposta `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70` nel tuo shell. Default ~95%: Claude compatta solo quando il context è quasi pieno e la qualità è già degradata. Al 70% compatta prima, sessioni lunghe restano più coerenti.
- Claude Code ha 4 tier di compaction: Snip (truncation cache-preserving), Micro (clearing tool results datati), Full (summarization, questo è `/compact`), Reactive Collapse (emergenza su 413). `/compact` forza il Tier 3 — usalo nei break naturali, non aspettare che scatti da solo.
- `claude --bare` bypassa tutto (hooks, plugin, memoria): startup ~400ms invece di 3-4s. Per query rapide una-tantum.

## Prima del deploy

- Hai un budget massimo per richiesta, sessione e cliente.
- Hai almeno un unit eval e un regression eval che bloccano merge stupidi.
- Sai cosa logghi e cosa non logghi per privacy e costi.
- Hai timeout, retry e fallback chiari.
- Hai distinto stato di sessione, memoria lunga e cronologia eventi.

## In esercizio

- Misura latenza p50 e p95, non solo media.
- Traccia costo per task, non solo costo giornaliero.
- Se un agente usa tool, osserva anche i tool call falliti.
- Se il prompt cresce, controlla subito cache hit e context bloat.
- Se la qualità cala, non cambiare tre cose insieme.

## Prima di scalare

- Definisci workload stateless vs stateful.
- Decidi quando basta una VPS e quando serve serverless.
- Se introduci multi-agent, misura costo coordinazione oltre al costo token.
- Se usi modelli locali, considera anche il costo infrastrutturale e operativo.
- Non introdurre Kubernetes solo per sembrare enterprise.
