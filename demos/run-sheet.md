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
- [ ] Excalidraw diagrams aperti: `ai-dev/course/diagrams/excalidraw/02-struttura-primitiva.excalidraw`, `ai-dev/course/diagrams/excalidraw/03-flusso-eventi-hook.excalidraw`
- [ ] Landscape aperto: `ai-dev/course/diagrams/excalidraw/01-landscape-tool-modello.excalidraw`
- [ ] Pipeline bespoke hub aperta: `ai-dev/course/diagrams/excalidraw/04-pipeline-spec-driven.excalidraw`

---

## Ponte Pedagogico — "18 Steps" come livello zero

Ref: articolo virale "How to Actually Use Claude" (18 tips). Utile come base di partenza per pubblico eterogeneo — molti partecipanti potrebbero essere a questo livello.

### Concetti chiave da citare (non da mostrare come slide)

| Tip articolo               | Concetto                                    | Come lo usiamo nella demo                                                                                                                                            |
| -------------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| #4 "Not a search engine"   | Claude è un thinking partner, non Google    | Aggancio narrativo Block 1: la pipeline non è "chiedi e ricevi" — è un workflow                                                                                      |
| #5 "Ask questions first"   | Fai raccogliere contesto prima di agire     | `/discovery` fa esattamente questo — chiede prima di progettare                                                                                                      |
| #7 "Sparring partner"      | Chiedi a Claude di attaccare le tue idee    | `/review` + `/code-review` come gate adversariale                                                                                                                    |
| #8 "Extended Thinking"     | Ragionamento step-by-step visibile          | Mostrabile live in qualsiasi blocco — brain icon                                                                                                                     |
| #9 "Claude writes prompts" | Meta-prompting: Claude scrive prompt per sé | Le nostre skill SONO prompt che Claude esegue — livello successivo                                                                                                   |
| "Interview pattern"        | Prima di implementare, fai intervistare te  | Prompt: "Interview me about X using AskUserQuestion, then write SPEC.md" → poi sessione fresca per implementare. `/discovery` + `/design` lo fanno sistematicamente. |

### Percorso narrativo (da citare verbalmente, non come slide)

```
Livello 0: "Smetti di usarlo come Google" (articolo tip 4-5)
Livello 1: "Dagli contesto persistente" (articolo: Projects → noi: CLAUDE.md + memory)
Livello 2: "Automatizza i pattern" (noi: rules/, hooks, skills)
Livello 3: "Fallo lavorare in autonomia" (noi: agents, /loop, team)
```

> **Nota presenter:** Non mostrare l'articolo. Usa i concetti come ponte verbale: "Molti di voi probabilmente usano Claude come chat — oggi vi mostro cosa succede quando lo trattate come un collega junior a cui avete dato un onboarding completo." Questo cattura sia i principianti (che si riconoscono) sia gli avanzati (che vogliono vedere il livello successivo).

### Angolo "Vibe Coding" — sicurezza come guardrail strutturale

Ref: post virale "If you're about to launch a vibe coded app… read this first" — checklist sicurezza per chi shippa app generate da AI senza revisione.

Il post propone di promptare manualmente Claude per controlli sicurezza. Noi lo facciamo in modo strutturale:

| Problema "vibe coding"     | Loro: prompt manuale                     | Noi: infrastruttura                                            |
| -------------------------- | ---------------------------------------- | -------------------------------------------------------------- |
| Security headers + posture | "Review my app as a security specialist" | `/security-verify scan` — SAST automatico                      |
| OWASP compliance           | "Review against OWASP standards"         | `/security-verify owasp` — check sistematico A01-A10           |
| Credential leaks           | "Check for credential leaks"             | Deny rules `Read(**/.env*)` in settings.json + scanner grep    |
| API keys in frontend       | "Ensure no API keys exposed"             | Deny rules + scanner (nota: gap su `.js/.ts`, solo `.py` oggi) |
| Runtime output leak        | Non menzionato                           | `.env.test` con dummy values per test runner                   |
| Supply chain               | Non menzionato                           | `/supply-chain-audit` + `sfw` + lockfile guards                |

> **Talking point Block 2:** "Il vibe coding funziona fino a quando non funziona. La differenza tra un hobby project e un prodotto è che i controlli non sono opzionali — sono infrastruttura. Quel post dice 'prompta Claude per la sicurezza'. Noi lo facciamo, ma come gate automatico che non puoi dimenticare."
>
> **I 3 vettori di leak (talking point):** "I segreti non escono solo quando l'agente legge .env. Ci sono 3 vie: (1) lettura diretta del file — bloccata dalle deny rules. (2) Output runtime — un test fallisce e logga l'header Authorization con il token reale. (3) Grep/search — Claude cerca una funzione e il match include una riga di config con credenziali. Per il vettore 2: usate .env.test con dummy values. Per il 3: le deny rules bloccano anche Grep su pattern protetti."
>
> **Gap onesto da citare (credibilità):** "Il nostro scanner oggi copre secret detection solo su file Python. JS/TS è un gap noto. Un tool come truffleHog o detect-secrets farebbe entropy-based detection su tutto. La nostra è una baseline, non una soluzione completa — ma è infinitamente meglio di niente."
>
> **Tassonomia dei segreti — perché copriamo pattern diversi (20s):** "Non tutti i segreti sono uguali. Tier 1: `.env` con Stripe key — costa soldi in secondi. Tier 2: `.ssh/`, `.aws/` — abilita account takeover. Tier 3: `.vscode/settings.json` con token, SQLite con dati utente — informazioni che non dovrebbero essere pubbliche. Le nostre deny rules coprono tutti e tre i livelli, non solo il Tier 1."
>
> **`.gitignore` non è una macchina del tempo (30s):** "Una trappola comune: si commette `.env` per sbaglio, si aggiunge `.gitignore`, si pensa di essere a posto. Ma `git log --all -- .env` mostra tutto ciò che è mai stato committato. I bot che scansionano GitHub lo trovano in minuti. La regola: se un segreto è entrato nella history, ruota la credenziale — non basta il gitignore. Per pulire la history serve `git filter-repo` o BFG Repo-Cleaner, e poi force push. È chirurgia, non igiene."

---

## Blocco 1: Cold Open (0:00–0:15)

**Rischio: ALTO** — la pipeline live dipende da Claude Code funzionante e repo configurato

### Timing interno

| Min       | Sotto-blocco             | Note                                                                                                             |
| --------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| 0:00–0:04 | Landscape tool (3–4 min) | 📊 `ai-dev/course/diagrams/excalidraw/01-landscape-tool-modello.excalidraw` + `05-livelli-pedagogici.excalidraw` |
| 0:04–0:05 | Frame narrativo (1 min)  | "Da writer a PM di agenti" — parlato, no slide                                                                   |
| 0:05–0:15 | Pipeline live (10 min)   | 📊 `ai-dev/course/diagrams/excalidraw/04-pipeline-spec-driven.excalidraw` — mostra prima il big picture          |
| 0:14–0:15 | Hook supply chain (30 s) | Mostra `pyproject.toml [tool.uv]` con quarantine                                                                 |

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

> **Nota presenter:** Apri con "Claude è un junior dev estremamente competente ma con amnesia totale — ogni sessione parte da zero." Questa frase (da un post virale con 350+ upvote) cattura il problema che CLAUDE.md, skills e memory risolvono. Usala come aggancio narrativo.
>
> **Aneddoto:** Un dev ha iniziato con un BEST_PRACTICES.md da 1400+ righe. Claude lo ignorava. Ristrutturando in skills < 500 righe ciascuna con resource files, token efficiency migliorata 40-60%. Questo è esattamente il pattern `.claude-example/` vs monolite.
>
> **Talking point CLAUDE.md — pesate il vostro config (30s):** "Prima di scrivere il vostro CLAUDE.md, fate `wc -w` su quello che state per caricare. Ogni parola viene letta da Claude a ogni singolo turno. Un CLAUDE.md da 5000 parole × 200 turni a settimana = un milione di token a settimana solo di regole. La domanda giusta non è 'cosa voglio dire a Claude' ma 'cosa deve sapere Claude ad ogni turno, per ogni task'. Tutto il resto va nelle rules scoped per progetto, o nelle skill che si caricano solo quando servono."

### Timing interno

| Min       | Sotto-blocco                | Durata | Note                                                                                             |
| --------- | --------------------------- | ------ | ------------------------------------------------------------------------------------------------ |
| 0:15–0:18 | CLAUDE.md / instructions.md | 3 min  | 📊 `09-directory-claude.excalidraw` + `08-repo-prima-dopo.excalidraw` — struttura e before/after |
| 0:18–0:22 | settings.json / config.toml | 4 min  | Permission modes, approval policy. **+15s:** `/fast` (stesso Opus 2.5x velocità, $30/$150 MTok)  |
| 0:22–0:27 | Context rot                 | 5 min  | 📊 `06-context-rot.excalidraw` — curva qualità/costo. **Taglia a 3 min se in ritardo**           |

> **Talking point Context Rot — il budget residuale (30s):** "Ogni turno Claude paga un biglietto d'ingresso: system prompt, CLAUDE.md, rules, schema dei tool, tutta la cronologia della conversazione. I token produttivi — quelli che rispondono alla vostra domanda — sono il residuo. Al messaggio 30 di una chat, state pagando 29 messaggi di re-lettura prima che Claude inizi a pensare alla vostra domanda. È per questo che session fresche e `/compact` esistono — non per pulizia, ma per economia."
>
> **Talking point — il costo lineare della conversazione (20s):** "Se ogni scambio costa ~500 token, il messaggio 30 costa 30× il messaggio 1. Non perché Claude sia lento — perché deve rileggere tutto. La regola pratica: oltre 15-20 messaggi, o fate `/compact` o aprite una sessione nuova con un riassunto. Il doppio-ESC vi fa ripescare il prompt senza accumulare cronologia."

| 0:27–0:32 | Custom agents vs skills vs cmds | 5 min | 📊 `07-agents-skills-commands.excalidraw` — tabella comparativa 3 colonne |
| 0:32–0:35 | MCP vs CLI tools | 3 min | **Salta se in ritardo — non bloccante** |
| 0:35–0:45 | Skills — slash commands | 10 min | `/pre-commit` su Claude vs Codex, terminale live |
| 0:45–0:55 | Hooks — 5 eventi | 10 min | 📊 `02-struttura-primitiva.excalidraw` + `03-flusso-eventi-hook.excalidraw` — trigger live |
| 0:55–1:05 | Rules + Prompt injection | 10 min | `tdd.md`, `naming.md`; injection demo breve |
| 1:05–1:15 | Agents + Plugin | 10 min | Explore/Plan/general-purpose |
| 1:15–1:20 | Buffer / Q&A | 5 min | — |

### Demo steps — settings.json (0:18–0:22)

```bash
cat .claude-example/settings.json | python3 -m json.tool
```

> **Talking points settings.json (versione anti-blog-post):**
>
> **3 livelli, merge automatico:** `~/.claude/settings.json` (globale) → `.claude/settings.json` (progetto, in git) → `.claude/settings.local.json` (locale, gitignored). Le regole si fondono; deny vince sempre, indipendentemente dal livello.
>
> **`Shift+Tab` per ciclare i mode live:** senza toccare config puoi passare da `default` → `acceptEdits` → `plan` direttamente in sessione. Utile per passare in read-only durante un'analisi.
>
> **`ask` array (il terzo pannello):** oltre ad allow e deny esiste `ask` — `"ask": ["Bash(git commit *)"]` vuol dire "esegui, ma mostrami cosa sta per committare e chiedi conferma ogni volta". Utile per azioni che vuoi autorizzare ma non automatizzare ciecamente.
>
> **Wildcard gotcha:** `Write(src/*)` copre solo un livello di directory. `Write(src/**)` è ricorsivo. Nei deny, usate `**` — sbagliare livello lascia aperte cartelle nested.
>
> **Deny chirurgici vs categorie:** copiare `"Bash(docker *)"` da un articolo blocca anche `docker ps` e `docker logs` (read-only). `"Bash(chmod *)"` blocca `chmod +x script.sh` che è innocuo. Regola: deny sulle **azioni distruttive specifiche**, non sulle categorie di tool. Il nostro `Bash(git push --force *)` è un esempio corretto — blocca l'azione, non il tool.

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

> **Cautionary tale (2 min):** Un Prettier hook PostToolUse sembra innocuo, ma ogni file modificato genera un `<system-reminder>` con le righe cambiate. Un caso reale documentato: 160k token consumati in 3 round — un file da 4000 righe formattato ha prodotto un system-reminder da 1890 righe per volta. Lezione: **"The context window is a public good"** (Anthropic docs). Ogni token che non contribuisce alla risposta ne degrada la qualità. Noi usiamo `formatters.yaml` ma con consapevolezza del costo (PostToolUse su Edit, non su ogni keystroke).
>
> **Nota presenter:** Se le skills non si attivano automaticamente in modo affidabile, un UserPromptSubmit hook può analizzare il prompt e iniettare reminder sulle skills rilevanti. Nel nostro setup non serve perché le 72 skills si attivano nativamente, ma è un workaround documentato dalla community per chi inizia con poche skills poco specifiche.

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
3. Spiega il meccanismo exit code 0/1/2 con `ai-dev/course/diagrams/excalidraw/03-flusso-eventi-hook.excalidraw`

### Setup richiesto prima del blocco

- File `~/.claude/hooks/handlers/bash.py` identificato e leggibile
- VS Code split view funzionante
- `ai-dev/course/diagrams/excalidraw/03-flusso-eventi-hook.excalidraw` aperto in browser

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
| --------- | -------------------- | ------ | ------------------------------------ |
| 1:35–1:45 | Stop hook live       | 10 min | 📊 `10-memory-flow.excalidraw`       |
| 1:45–1:55 | Memory recall live   | 10 min |
| 1:55–2:05 | Strategie di memoria | 10 min | 📊 `11-strategie-memoria.excalidraw` |

> **Pattern alternativo (community):** Per chi non ha un memory system automatizzato, il "dev-docs triplet" funziona: per ogni feature creare `plan.md` (il piano accettato), `context.md` (file chiave, decisioni), `tasks.md` (checklist). Aggiornare ad ogni compaction, finire la sessione con "continue" nella successiva. Meccanismo manuale ma efficace — il nostro `continuation.md` + `/memory recall` lo automatizza.

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
| --------- | -------------------------------- | ------ | ---------------------------------------------------------------------- |
| 2:15–2:25 | Panoramica modelli               | 10 min | 📊 `12-model-pricing.excalidraw` + `13-model-decision-tree.excalidraw` |
| 2:25–2:40 | Demo velocità locale (Qwen3 MLX) | 15 min |
| 2:40–2:45 | OpenCode                         | 5 min  |
| 2:45–2:50 | Configurazione                   | 5 min  |

### Talking point — Dual-system benchmark reale (2 min, opzionale nell'intro Panoramica)

> **Aggancio narrativo (da usare nell'apertura del blocco):** "Prima di vedere i modelli open, un dato dalla scorsa settimana: qualcuno ha fatto girare GPT 5.5 su Codex e Opus 4.7 su Claude Code sugli stessi 4 task. Runtime totale: 21 minuti vs 41. Output token: 70k vs 250k. GPT $3 più economico. Sembra chiaro? Poi guardi il solar system: Opus più pulito, $1 meno, 1 minuto in più. E su SWE-Bench Pro — fix di issue reali GitHub — Opus vince ancora. La domanda giusta non è quale modello è il migliore. È: per questo task specifico, in questo contesto, qual è il fit?"

> **Talking point harness (30s):** "L'autore del test lo ammette esplicitamente: 'this is an agentic harness comparison as much as a pure model comparison.' Codex e Claude Code non sono uguali. Quando qualcuno dice 'GPT è più veloce di Claude', la domanda giusta è: su quale harness? Con quale configurazione? Il modello è il motore. L'harness è il telaio. Oggi vi mostro come funziona il telaio."

> **Collegamento context rot (Blocco 2, cross-ref):** "GPT 5.5 produce 3.5x meno output token per risultati comparabili. Meno output = meno cronologia = sessione più lunga prima del degrado. Ma Codex ha 400k di context contro 1M di Claude Code. Un modello conciso in una finestra piccola può saturare prima di uno verboso in una grande. Non esiste ottimizzazione senza misurare tutti e due gli assi."

> **Nota presenter:** Questo talking point dura 2 min. Usarlo nell'apertura di Panoramica se il blocco è in orario. Tagliare se si è in ritardo di 5+ min — il messaggio chiave (scelta per tipo di task) viene comunque dalle slide `12-model-pricing.excalidraw` + `13-model-decision-tree.excalidraw`.

### Demo steps — Qwen3 locale via MLX

```bash
# Verifica server running
curl http://localhost:8080/v1/models

# Avvia proxy Anthropic→OpenAI in un terminale
make proxy-mlx

# Avvia Claude Code in modalità ridotta/read-only
make claude-proxy-mlx

# Smoke prompt:
# "List the files in this repository, then read README.md and summarize it in 5 bullets."
```

### Demo steps — DeepSeek via OpenRouter

```bash
# Avvia proxy DeepSeek
make proxy-deepseek

# Avvia Claude Code contro il proxy, con traffico non essenziale disabilitato
make claude-proxy-deepseek

# Se il tool-use di Claude Code non è stabile:
make opencode-fallback
```

### Fallback: ALTO

Se MLX server non risponde o Qwen3 non disponibile:

1. **Primo fallback:** passa a OpenCode con `demos/opencode-fallback.md` per la demo tool-use su modelli non-Claude.
2. **Secondo fallback:** Apri `demos/recordings/block4-models.mp4` — registrazione con output reale di Qwen3 (token/s visibili). Commentala live.
3. **Terzo fallback:** Mostra solo Ollama: `ollama run qwen3:8b "spiega cos'è LLMOps in 3 righe"`.
4. **Quarto fallback (solo OpenRouter giù):** Spiega il pricing teorico con la tabella in `src/llm_ops_v1/economics/commercial_models.py`. Nessuna demo live.

### Setup richiesto prima del blocco

- MLX server avviato e warm (almeno 1 query già inviata prima della sessione)
- Proxy Claude Code verificato con `make proxy-mlx` + `make claude-proxy-mlx`
- Tab browser con OpenRouter dashboard aperto (per mostrare il pricing reale)
- Video `demos/recordings/block4-models.mp4` pronto (quicktime o VLC)

---

## PAUSA (2:50–3:00, 10 min)

---

## Blocco 5: Harnessing — Workflow Completo (3:00–3:30)

**Rischio: MEDIO** — il ciclo completo dipende da Claude Code attivo

> ⚠️ **Timing warning:** Con Ralph Loop + pattern avanzati sale a ~40 min. Se i blocchi precedenti hanno sforato: comprimi il ciclo completo (salta `/release full` e `/health full`), o sposta Ralph Loop nel Blocco 6.

### Timing interno

| Min       | Sotto-blocco                    | Durata | Note                                                                                 |
| --------- | ------------------------------- | ------ | ------------------------------------------------------------------------------------ |
| 3:00–3:05 | Spec-driven dev                 | 5 min  | 📊 `04-pipeline-spec-driven.excalidraw` + `14-context-engineering-layers.excalidraw` |
| 3:05–3:20 | Ciclo completo                  | 15 min | `/implementation` → `/pre-commit` → `/ship` → `/release full`                        |
| 3:20–3:23 | Reflection loop + quality gates | 3 min  | `/review` + gates non bypassabili                                                    |
| 3:23–3:28 | Ralph Loop + /loop nativo       | 5 min  | 📊 `15-ralph-loop.excalidraw` — **Sposta in Blocco 6 se in ritardo**                 |
| 3:28–3:30 | Pattern avanzati (citazione)    | 2 min  | Worktrees, headless mode                                                             |

> **Tips pratici da dare ai partecipanti:**
>
> - **"Don't lead in your prompts"** — Claude dice quello che pensi di voler sentire. Chiedi "analizza questa funzione" non "questa funzione è buona, vero?"
> - **Double-ESC trick** — premi ESC due volte per ripescare prompt precedenti e ri-promptare con la conoscenza di cosa NON vuoi. Spesso il secondo tentativo è molto migliore.
> - **"Sometimes just step in"** — se Claude lotta da 30 min su qualcosa che risolveresti in 2, risolvilo tu. Non è una sconfitta, è orchestrazione.

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

> **Nota presenter:** Far revisionare a Claude il proprio codice è un pattern sottovalutato. Un dev che ha fatto un rewrite da 300k LOC da solo dice che è stato il cambiamento più impattante dopo planning e dev-docs: "catching critical errors, missing implementations, inconsistent code, and security flaws." Nel nostro workflow corrisponde a `/review` + `/code-review` come gate prima di `/ship`.

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
| --------- | ------------------------------ | ------ | --------------------------------------- |
| 3:35–3:45 | I tre framework                | 10 min | 📊 `16-framework-comparison.excalidraw` |
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

| Blocco  | Demo critica                       | Rischio | Mitigazione principale                                     |
| ------- | ---------------------------------- | ------- | ---------------------------------------------------------- |
| Block 1 | Pipeline live `/discovery`→`/ship` | ALTO    | Video `block1-pipeline.mp4` pronto                         |
| Block 4 | Qwen3 su MLX (velocità token/s)    | ALTO    | Video `block4-models.mp4` + fallback Ollama                |
| Block 2 | Trigger live hook pre-bash         | MEDIO   | `03-flusso-eventi-hook.excalidraw` + lettura inline codice |

**Regola generale:** Se un demo live ALTO-rischio fallisce, passa al fallback entro **30 secondi** — non sprecare tempo a debuggare live.

---

## Note Timing Critiche

1. **Block 2 a rischio sforamento:** Se a 0:40 (25 min nel blocco) sei ancora sulle skills, salta MCP. Se a 1:05 hai ancora hooks e rules da coprire, comprimi context rot a 2 min.
2. **Block 5 a rischio sforamento:** Se arrivi al blocco con 5+ min di ritardo accumulato, salta `/release full` e `/health full`. Ralph Loop è comprimibile a 2 min (citazione verbale, no demo).
3. **Regola del buffer:** I 5 min di buffer in Block 2 (1:15–1:20) sono sacri — non riempirli con contenuto aggiuntivo.

---

## Risorse da Condividere ai Partecipanti

### Plugin: `claude-code-setup` (consigliato per chi parte da zero)

**Repo:** `https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-code-setup`

Plugin ufficiale Anthropic, read-only. Analizza il progetto e suggerisce:

- Quali **hook** installare (auto-format, block sensitive files)
- Quali **skill** attivare (plan, test, review)
- Quali **MCP server** aggiungere (Context7, Playwright)
- Quali **subagent** configurare (security, accessibility)

**Installazione:** `claude plugin install claude-code-setup` (o via settings.json)

**Perché consigliarlo:** è il ponte tra "ho Claude Code" e "ho Claude Code configurato". Per chi nella sala è al livello zero dell'articolo "18 Steps", questo plugin fa il lavoro di analisi iniziale che altrimenti richiederebbe leggere tutta la documentazione.

> **Nota presenter:** Citare nel Block 2 (dopo aver mostrato la propria configurazione): "Se questo vi sembra tanto da configurare a mano, c'è un plugin ufficiale che analizza il vostro progetto e vi suggerisce da dove partire." Non fare demo live del plugin — solo citazione + link nella slide risorse.
