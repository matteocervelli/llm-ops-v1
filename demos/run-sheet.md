# Run-Sheet — Sessione 1: AI-Driven Development

**Data:** 2026-05-22  
**Durata:** 4 ore (200 min contenuto + 40 min pause)  
**Pubblico:** Developer con esperienza coding, primo contatto strutturato con AI tools  
**Repo demo:** `llm-ops-v1` (fork già configurato con skill e hook attivi)  
**Macchina principale:** Studio Mac (arm64, MLX, Ollama locale)

---

## Timeline Overview

| Tempo     | Blocco                            | Durata | Rischio | Fallback              |
| --------- | --------------------------------- | ------ | ------- | --------------------- |
| 0:00–0:15 | 1. Cold Open                      | 15 min | ALTO    | demo registrata       |
| 0:15–1:20 | 2. Anatomia e Configurazione      | 65 min | MEDIO   | slides statiche       |
| 1:20–1:35 | **PAUSA**                         | 15 min | —       | —                     |
| 1:35–2:05 | 3. Persistent Memory              | 30 min | MEDIO   | walkthrough narrativo |
| 2:05–2:15 | **PAUSA**                         | 10 min | —       | —                     |
| 2:15–2:50 | 4. Modelli Alternativi            | 35 min | ALTO    | video pre-registrato  |
| 2:50–3:00 | **PAUSA**                         | 10 min | —       | —                     |
| 3:00–3:30 | 5. Harnessing — Workflow Completo | 30 min | MEDIO   | walkthrough narrativo |
| 3:30–3:35 | **PAUSA**                         | 5 min  | —       | —                     |
| 3:35–4:00 | 6. Pattern Esterni                | 25 min | BASSO   | slides statiche       |

**Totale:** 200 min contenuto + 40 min pause = 240 min = 4h ✓

---

## Checklist Pre-Sessione

Verificare **almeno 30 minuti prima** dell'inizio:

### Terminali e repo

- [ ] `llm-ops-v1` clonato e configurato (`cp .env.example .env`, chiavi inserite)
- [ ] `uv sync` eseguito, `uv run pytest tests/evals/unit/` verde
- [ ] `~/.claude/` presente con tutte le skill (`tree ~/.claude/skills/ | head -20`)
- [ ] `~/.codex/` presente con configurazione equivalente
- [ ] `code` (VS Code) aperto sul repo, terminale integrato pronto

### Servizi locali

- [ ] Ollama running: `ollama list` → `qwen3:30b-a3b` presente
- [ ] MLX server running (porta 8080): `curl http://localhost:8080/v1/models`
- [ ] Langfuse stack up: `cd infrastructure && docker compose up -d` → `http://localhost:3000`

### API keys (`.env`)

- [ ] `ANTHROPIC_API_KEY` — Claude Code funzionante
- [ ] `OPENAI_API_KEY` — Codex funzionante
- [ ] `OPENROUTER_API_KEY` — DeepSeek V4 Flash raggiungibile
- [ ] `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` + `LANGFUSE_HOST`

### Demo artifacts

- [ ] Tab browser: Langfuse dashboard pre-caricata
- [ ] File `~/.claude/skills/pre-commit.md` aperto in editor
- [ ] File `.claude-example/hooks/pre-bash.py` aperto in editor
- [ ] Demo registrata Block 1 pronta (path: `demos/recordings/block1-pipeline.mp4`)
- [ ] Demo registrata Block 4 pronta (path: `demos/recordings/block4-models.mp4`)
- [ ] Excalidraw diagrams aperti: struttura primitiva, flusso eventi hook

---

## Blocco 1: Cold Open (0:00–0:15)

**Rischio: ALTO** — la pipeline live dipende da Claude Code funzionante e repo configurato

### Timing interno

| Min       | Sotto-blocco             | Note                                                                   |
| --------- | ------------------------ | ---------------------------------------------------------------------- |
| 0:00–0:04 | Landscape tool (3–4 min) | Slide o Excalidraw: CLI / IDE / desktop / SDK                          |
| 0:04–0:05 | Frame narrativo (1 min)  | "Da writer a PM di agenti" — parlato, no slide                         |
| 0:05–0:15 | Pipeline live (10 min)   | `/discovery` → `/design` → `/implementation` → `/pre-commit` → `/ship` |
| 0:14–0:15 | Hook supply chain (30 s) | Mostra `pyproject.toml [tool.uv]` con quarantine                       |

### Demo steps — Pipeline live

```bash
# Repo già configurato, nessun setup live
cd ~/dev/demo/llm-ops-v1

# 1. Discovery di una feature minima (es. "aggiungi un campo costo alla risposta triage")
# Trigger: /discovery

# 2. Design automatico
# Trigger: /design

# 3. Implementazione TDD
# Trigger: /implementation

# 4. Quality gate
# Trigger: /pre-commit

# 5. Ship
# Trigger: /ship
```

### Fallback: ALTO

Se Claude Code non risponde o la pipeline si blocca:

1. **Primo fallback (30 s):** Apri `demos/recordings/block1-pipeline.mp4` — registrazione della stessa pipeline su repo identico. Commentala live mentre gira.
2. **Secondo fallback:** Mostra direttamente il repo su GitHub con la PR già creata. Naviga i diff. Spiega il ciclo a voce.

### Setup richiesto prima del blocco

- Claude Code attivo e autenticato
- Repo `llm-ops-v1` aperto in VS Code
- Terminale integrato visibile

---

## Blocco 2: Anatomia e Configurazione (0:15–1:20)

**Rischio: MEDIO** — il trigger live dell'hook è il punto più fragile

> ⚠️ **Timing warning:** questo blocco può espandersi a ~80 min. Comprimere: MCP (saltare, 2 min recuperati), context rot (3 min invece di 5). Margine: 10 min.

### Timing interno

| Min       | Sotto-blocco                    | Durata | Note                                                               |
| --------- | ------------------------------- | ------ | ------------------------------------------------------------------ |
| 0:15–0:18 | CLAUDE.md / instructions.md     | 3 min  | Livelli globale/workspace/progetto                                 |
| 0:18–0:22 | settings.json / config.toml     | 4 min  | Permission modes, approval policy                                  |
| 0:22–0:27 | Context rot                     | 5 min  | Paper/benchmark + exit prematura. **Taglia a 3 min se in ritardo** |
| 0:27–0:32 | Custom agents vs skills vs cmds | 5 min  | Tabella comparativa                                                |
| 0:32–0:35 | MCP vs CLI tools                | 3 min  | **Salta se in ritardo — non bloccante**                            |
| 0:35–0:45 | Skills — slash commands         | 10 min | `/pre-commit` su Claude vs Codex, terminale live                   |
| 0:45–0:55 | Hooks — 5 eventi                | 10 min | Trigger live: blocco `rm -rf`                                      |
| 0:55–1:05 | Rules + Prompt injection        | 10 min | `tdd.md`, `naming.md`; injection demo breve                        |
| 1:05–1:15 | Agents + Plugin                 | 10 min | Explore/Plan/general-purpose                                       |
| 1:15–1:20 | Buffer / Q&A                    | 5 min  | —                                                                  |

### Demo steps — Hook trigger live

```bash
# Mostra pre-bash.py prima
cat ~/.claude/hooks/handlers/bash.py

# Trigger: digita un comando pericoloso in Claude Code
# Claude Code tenterà: rm -rf /tmp/test
# Hook blocca con exit 1 + messaggio

# Poi mostra l'allow-list
cat .claude-example/settings.json | python3 -m json.tool
```

### Demo steps — Skill affiancata

```bash
# Affianca i due tool
tree ~/.claude/skills/ | grep pre-commit
tree ~/.codex/skills/ | grep pre-commit

# Apri entrambi i file in split view VS Code
```

### Fallback: MEDIO

Se l'hook non blocca il comando (misconfiguration, PATH problem):

1. Apri `~/.claude/hooks/handlers/bash.py` in editor e leggilo inline — la logica è autoesplicativa
2. Mostra il file `.claude-example/hooks/pre-bash.py` come riferimento
3. Spiega il meccanismo exit code 0/1/2 con slides statiche (Excalidraw: flusso eventi)

### Setup richiesto prima del blocco

- File `~/.claude/hooks/handlers/bash.py` identificato e leggibile
- VS Code split view funzionante
- Excalidraw diagram "flusso eventi PreToolUse" aperto in browser

---

## PAUSA (1:20–1:35, 15 min)

Verifica durante la pausa:

- [ ] Servizio Ollama ancora running
- [ ] `.claude/memory/local/continuation.md` presente nel repo demo (per Block 3)
- [ ] Timing attuale vs schedule — se Blocco 2 ha sforato, nota quanto

---

## Blocco 3: Persistent Memory (1:35–2:05)

**Rischio: MEDIO** — Stop hook deve scrivere continuation.md durante la demo

### Timing interno

| Min       | Sotto-blocco         | Durata |
| --------- | -------------------- | ------ |
| 1:35–1:45 | Stop hook live       | 10 min |
| 1:45–1:55 | Memory recall live   | 10 min |
| 1:55–2:05 | Strategie di memoria | 10 min |

### Demo steps — Stop hook

```bash
# Apri Claude Code sul repo demo
# Digita alcune istruzioni (es. "leggi il README e dimmi cosa fa questo repo")
# Chiudi la sessione Claude Code
# Mostra il file generato automaticamente
cat .claude/memory/local/continuation.md

# Poi mostra come session.py inietta questo file al prossimo avvio
# (non entrare nel codice Python — mostra solo il concetto)
```

### Demo steps — Memory recall

```bash
# In una nuova sessione Claude Code:
# /memory recall "authentication"

# Mostra il risultato: FTS5 match + Thesaurus score
# Poi apri un file memoria per mostrare la struttura frontmatter
head -20 ~/.claude/memory/project-content-brief-s1.md
```

### Fallback: MEDIO

Se lo Stop hook non scrive `continuation.md` (bug di configurazione):

1. Mostra un file `continuation.md` già generato da una sessione precedente (tienine uno in `demos/examples/continuation-example.md`)
2. Spiega il meccanismo a voce: "questo è quello che il nostro hook scrive — ecco il formato"
3. `/memory recall` può girare ugualmente — non dipende dallo Stop hook

### Setup richiesto prima del blocco

- Sessione Claude Code aperta sul repo demo (pronta da chiudere live)
- File `~/.claude/memory/` con almeno 2-3 file memoria reali
- `demos/examples/continuation-example.md` come backup

---

## PAUSA (2:05–2:15, 10 min)

Verifica durante la pausa:

- [ ] Ollama ancora running: `ollama list`
- [ ] MLX server ancora running: `curl -s http://localhost:8080/v1/models | python3 -m json.tool`
- [ ] OpenRouter raggiungibile: `curl -s https://openrouter.ai/api/v1/models | head -5`

---

## Blocco 4: Modelli Alternativi (2:15–2:50)

**Rischio: ALTO** — dipende da MLX locale + OpenRouter API attive contemporaneamente

### Timing interno

| Min       | Sotto-blocco                     | Durata |
| --------- | -------------------------------- | ------ |
| 2:15–2:25 | Panoramica modelli               | 10 min |
| 2:25–2:40 | Demo velocità locale (Qwen3 MLX) | 15 min |
| 2:40–2:45 | OpenCode                         | 5 min  |
| 2:45–2:50 | Configurazione                   | 5 min  |

### Demo steps — Qwen3 locale via MLX

```bash
# Verifica server running
curl http://localhost:8080/v1/models

# Apri settings.local.json per mostrare il redirect
cat ~/.claude/settings.local.json
# → ANTHROPIC_BASE_URL: "http://localhost:8080/v1"
# → ANTHROPIC_API_KEY: "ollama"

# Avvia Claude Code (punta a MLX automaticamente)
# Digita una query semplice — mostra token/s visibili nel log
```

### Demo steps — DeepSeek via OpenRouter

```bash
# Codex config
cat ~/.codex/config.toml
# → [providers.openrouter] con deepseek/deepseek-v4-flash

# Avvia Codex, mostra la stessa query
# Affianca: costo stimato vs locale (costo zero)
```

### Fallback: ALTO

Se MLX server non risponde o Qwen3 non disponibile:

1. **Primo fallback:** Apri `demos/recordings/block4-models.mp4` — registrazione con output reale di Qwen3 (token/s visibili). Commentala live.
2. **Secondo fallback:** Mostra solo Ollama (più semplice, già installato): `ollama run qwen3:8b "spiega cos'è LLMOps in 3 righe"`. Meno impressionante ma funzionante.
3. **Terzo fallback (solo OpenRouter giù):** Spiega il pricing teorico con la tabella in `src/llm_ops_v1/economics/commercial_models.py`. Nessuna demo live.

### Setup richiesto prima del blocco

- MLX server avviato e warm (almeno 1 query già inviata prima della sessione)
- `settings.local.json` con ANTHROPIC_BASE_URL configurato
- Tab browser con OpenRouter dashboard aperto (per mostrare il pricing reale)
- Video `demos/recordings/block4-models.mp4` pronto (quicktime o VLC)

---

## PAUSA (2:50–3:00, 10 min)

---

## Blocco 5: Harnessing — Workflow Completo (3:00–3:30)

**Rischio: MEDIO** — il ciclo completo dipende da Claude Code attivo

> ⚠️ **Timing warning:** Con Ralph Loop + pattern avanzati sale a ~40 min. Se i blocchi precedenti hanno sforato: comprimi il ciclo completo (salta `/release full` e `/health full`), o sposta Ralph Loop nel Blocco 6.

### Timing interno

| Min       | Sotto-blocco                    | Durata | Note                                                          |
| --------- | ------------------------------- | ------ | ------------------------------------------------------------- |
| 3:00–3:05 | Spec-driven dev                 | 5 min  | `/discovery` → `/design`                                      |
| 3:05–3:20 | Ciclo completo                  | 15 min | `/implementation` → `/pre-commit` → `/ship` → `/release full` |
| 3:20–3:23 | Reflection loop + quality gates | 3 min  | `/review` + gates non bypassabili                             |
| 3:23–3:28 | Ralph Loop + /loop nativo       | 5 min  | **Sposta in Blocco 6 se in ritardo**                          |
| 3:28–3:30 | Pattern avanzati (citazione)    | 2 min  | Worktrees, headless mode                                      |

### Demo steps — Ciclo completo

```bash
# Continua dalla pipeline del Cold Open (stessa repo, stesso task)
# Mostra CLAUDE.md sezione Workflow come "contratto"
grep -A 20 "## Workflow" ~/.claude/CLAUDE.md

# /implementation → TDD visibile (test rosso → verde)
# /pre-commit → quality gate output (ruff, pyright, pytest, security scan)
# /ship → commit + push + PR
# /release full → tag semantico + CHANGELOG aggiornato
```

### Fallback: MEDIO

Se Claude Code si blocca a metà pipeline:

1. Mostra l'output di una run precedente (tieni i log in `demos/examples/pre-commit-output.txt`)
2. Naviga il CHANGELOG già generato da una release reale
3. Spiega il workflow a voce usando `~/.claude/CLAUDE.md` come script — la sezione Workflow è autoesplicativa

### Setup richiesto prima del blocco

- Claude Code fresco (nuova sessione, context window vuota)
- Repo pulito con un task preparato per la demo (branch già creato, test da far diventare verde)

---

## PAUSA (3:30–3:35, 5 min)

---

## Blocco 6: Pattern Esterni (3:35–4:00)

**Rischio: BASSO** — tutto basato su slides e tabella statica

### Timing interno

| Min       | Sotto-blocco                   | Durata |
| --------- | ------------------------------ | ------ |
| 3:35–3:45 | I tre framework                | 10 min |
| 3:45–3:55 | Confronto affiancato           | 10 min |
| 3:55–3:57 | Perché me lo son fatto da solo | 2 min  |
| 3:57–4:00 | Il ruolo che cambia + debrief  | 3 min  |

### Demo steps

```bash
# Apri la tabella già scritta
cat ai-dev/docs/external-patterns.md

# Mostra la directory skills come prova dell'integrazione custom
tree ~/.claude/skills/ | wc -l
# → ~50+ skill custom
```

### Fallback: BASSO

Questo blocco è interamente narrativo + slides. Se il tempo è esaurito:

1. Salta la demo terminale (`tree ~/.claude/skills/`)
2. Comprimi confronto affiancato a 5 min (mostra solo 2 righe della tabella invece di tutte)
3. La chiusura "il ruolo che cambia" è obbligatoria — non tagliare

### Setup richiesto prima del blocco

- `ai-dev/docs/external-patterns.md` aggiornato con stelle GitHub attuali
- Browser con le 3 pagine GitHub dei framework aperte in tab separati

---

## Matrice Rischi

| Blocco  | Demo critica                       | Rischio | Mitigazione principale                      |
| ------- | ---------------------------------- | ------- | ------------------------------------------- |
| Block 1 | Pipeline live `/discovery`→`/ship` | ALTO    | Video `block1-pipeline.mp4` pronto          |
| Block 4 | Qwen3 su MLX (velocità token/s)    | ALTO    | Video `block4-models.mp4` + fallback Ollama |
| Block 2 | Trigger live hook pre-bash         | MEDIO   | Lettura inline codice + Excalidraw diagram  |

**Regola generale:** Se un demo live ALTO-rischio fallisce, passa al fallback entro **30 secondi** — non sprecare tempo a debuggare live.

---

## Note Timing Critiche

1. **Block 2 a rischio sforamento:** Se a 0:40 (25 min nel blocco) sei ancora sulle skills, salta MCP. Se a 1:05 hai ancora hooks e rules da coprire, comprimi context rot a 2 min.
2. **Block 5 a rischio sforamento:** Se arrivi al blocco con 5+ min di ritardo accumulato, salta `/release full` e `/health full`. Ralph Loop è comprimibile a 2 min (citazione verbale, no demo).
3. **Regola del buffer:** I 5 min di buffer in Block 2 (1:15–1:20) sono sacri — non riempirli con contenuto aggiuntivo.
