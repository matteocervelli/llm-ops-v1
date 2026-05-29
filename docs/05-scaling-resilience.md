# Scaling e resilienza in produzione

Questo documento descrive i pattern "a scala" che vanno oltre il codice demo
presente nel repo. Il codice demo implementa versioni minimali di ciascun
concetto (vedi `agents/resilience.py`, `agents/queue.py`, `agents/rate_limit.py`);
qui trovi come evolvere ciascuno verso un sistema operativo più robusto.

## Da coda in-memory a coda distribuita

Il demo usa `InMemoryQueue` (un `deque` Python) e `RedisStreamsQueue` (Redis Streams).
Redis Streams è già at-least-once grazie ai consumer group e agli ACK espliciti.

Per scalare a più worker in parallelo:

- Aggiungi più istanze del worker con consumer diversi nello stesso group (`CONSUMER = f"worker-{os.getpid()}"`)
- Redis garantisce che ogni messaggio venga consegnato a un solo consumer nel group
- Imposta `MAX_DELIVERY_COUNT` e un dead-letter stream (`llmops:jobs-dlq`) per i job che falliscono ripetutamente

Per scalare oltre Redis:

- **AWS SQS**: drop-in con visibilità timeout e DLQ nativa
- **Google Pub/Sub**: messaggi ordinati per topic, ack asincrono
- **Kafka**: per throughput molto alto e replay storico

## Rate limiting distribuito

Il demo usa `InMemoryBucket` (per-process, si resetta al riavvio) e `RedisBucket` (condiviso tra istanze con Lua atomic).

Per produzione multi-replica:

- Usa `RedisBucket` — il Lua script garantisce atomicità anche con N worker simultanei
- Esponi `Retry-After` header (già implementato nel webhook) — i client devono rispettarlo
- Considera rate limit a più livelli: per IP, per API key, per customer tier

**Backpressure**: quando il rate limiter restituisce 429, il client dovrebbe aspettare `Retry-After` secondi prima di riprovare. Se la coda si riempie più velocemente di quanto il worker la svuoti, aumenta il numero di worker o abbassa il rate limit.

## Circuit breaker e fallback chain

Il demo implementa un circuit breaker `closed → open → half-open` con soglie configurabili.

Pattern aggiuntivi per produzione:

**Bulkhead**: isola i pool di connessioni per provider. Se il pool di Anthropic è esaurito, le chiamate a OpenAI continuano senza interferenza.

**Hedging**: invia la stessa request a due provider in parallelo, usa la prima risposta, cancella l'altra. Riduce la latenza p99 a costo di costo raddoppiato. Ha senso solo per le chiamate più critiche (es. customer enterprise).

**Dead-letter**: i job che falliscono N volte vanno in `llmops:jobs-dlq`. Un processo separato legge il DLQ, notifica gli ops, e permette replay manuale dopo che il provider è tornato disponibile.

## Compressione e gestione del contesto

Il demo usa `agents/context.py` con una euristica word-count 1.3× per la stima
e il trimming dei policy snippet.

Per produzione:

- Usa un tokenizer reale (`tiktoken` per OpenAI, `client.messages.count_tokens(...)` per Claude) — la stima 1.3× è accurata al 10-15%, insufficiente per prompt vicini al limite
- Implementa una strategia di summarization: quando i policy snippet eccedono il budget, chiama un modello leggero (Haiku) per condensarli prima di passarli al modello principale
- Per conversazioni multi-turno: usa una finestra scorrevole con summary del contesto precedente

## Autoscaling

Per autoscaling:

- **Fly.io** (`infrastructure/serverless/fly.toml`): `auto_stop_machines = "stop"` + `auto_start_machines = true` + `min_machines_running = 0` — scale-to-zero, si avvia on demand. Latenza di cold start ~1-2s.
- **Kubernetes HPA**: scala il numero di pod worker in base alla profondità della coda (metrica custom via Prometheus `keda_scaledobject_*` con KEDA).
- **Regola pratica**: monitora la latenza p95. Se supera 2× il baseline con carico normale, aggiungi istanze.

Metriche chiave da esporre:

- `llmops_request_total{model, backend, status}` — counter
- `llmops_latency_ms{model, backend}` — histogram (p50/p95/p99)
- `llmops_cost_usd_total{model}` — counter
- `llmops_cache_hit_total` e `llmops_cache_miss_total` — counter
- `llmops_queue_depth` — gauge (letto da Redis XLEN)

Alertmanager regole:

- `p95_latency > 5000ms` per 5 minuti → canale di reperibilità
- `cache_hit_ratio < 0.5` per 15 minuti → canale operativo
- `error_rate > 5%` per 2 minuti → canale di reperibilità
