# LLM Ops Survival Kit

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
