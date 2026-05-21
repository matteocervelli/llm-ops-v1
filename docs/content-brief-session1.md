# Content Brief — Sessione 1 (22 maggio 2026)

**Titolo:** AI-Driven Development  
**Durata:** 4 ore (200 min contenuto + 40 min pause)  
**Pubblico:** Developer con esperienza coding, primo contatto strutturato con AI tools  
**Obiettivo:** Portare a casa un setup operativo e un modello mentale per usare AI tools come sistemi configurabili, non chatbot

---

## Blocco 1: Cold Open (15min)

- **Key message:** Per farli lavorare bene bisogna sistemarli bene — questi tool non sono chatbot, sono sistemi configurabili. E mentre parliamo, i registry NPM stanno bruciando: il modo in cui li configuri è già un tema di sicurezza.

- **Demo artifact:**
  1. **Landscape (3-4 min):** 📊 `ai-dev/course/diagrams/excalidraw/01-landscape-tool-modello.excalidraw` + `05-livelli-pedagogici.excalidraw` — Modalità di uso degli coding agent — CLI (Claude Code, Codex, OpenCode), IDE extension (Cursor, Windsurf, VS Code Copilot), desktop app (Claude, ChatGPT), Claude Agent SDK (programmabile, per infrastruttura di team). Positioning: "oggi parliamo di CLI perché è dove hai il controllo massimo — ma tutto quello che vedi scala fino all'SDK."
  2. **Frame narrativo (1 min):** "Da oggi non siete più writer — siete PM di un gruppo di dipendenti agenti. Voi decidete le priorità, le feature, le storie. Loro eseguono." Poi parte la demo.
  3. **Pipeline live (10 min):** 📊 `ai-dev/course/diagrams/excalidraw/04-pipeline-spec-driven.excalidraw` — `/discovery` → `/design` → `/implementation` → `/pre-commit` → `/ship` su un task semplice. Gira su repo già configurato, senza setup live.
  4. **Hook supply chain (30 sec):** "Mentre parliamo, i registry NPM bruciano. Il nostro setup blocca i pacchetti compromessi via constraints. Questo è ciò che intendiamo per 'configurare bene'."

- **Esempio concreto:** Il repo `llm-ops-v1` — fork esistente, skill già installate, hook attivi. `pyproject.toml [tool.uv]` con le quarantine (`mistralai!=2.4.6`, `guardrails-ai!=0.10.1`).

- **Cut:** Nessuna spiegazione delle singole skill o hook (vengono dopo). Non si entra nell'SDK. Il landscape è un posizionamento, non un benchmark.

---

## Blocco 2: Claude Code + Codex — Anatomia e Configurazione (65min)

- **Key message:** Due tool, lo stesso modello mentale — CLAUDE.md/instructions.md, skills, hooks, rules. Imparare uno significa capire entrambi.

- **Demo artifact:** Struttura primitiva per primitiva. Per ogni primitiva:
  - Link alla documentazione ufficiale (Claude Code docs, Codex docs)
  - Template scheletro minimo (es. struttura di una skill Markdown, struttura di un hook JSON)
  - Confronto reale: la stessa skill nel repo `~/.claude/skills/` vs `~/.codex/skills/` (es. `/pre-commit` su Claude Code vs equivalente su Codex)
  - Momento terminale: `tree ~/.claude/` vs `tree ~/.codex/` affiancati, poi trigger live di un hook che blocca un comando pericoloso
  - 📊 `ai-dev/course/diagrams/excalidraw/02-struttura-primitiva.excalidraw` — struttura primitiva hub-spoke
  - 📊 `ai-dev/course/diagrams/excalidraw/03-flusso-eventi-hook.excalidraw` — flusso PreToolUse exit codes 0/1/2
  - 📊 `ai-dev/course/diagrams/excalidraw/08-repo-prima-dopo.excalidraw` — before/after configurazione
  - 📊 `ai-dev/course/diagrams/excalidraw/09-directory-claude.excalidraw` — struttura `~/.claude/`
  - 📊 `ai-dev/course/diagrams/excalidraw/06-context-rot.excalidraw` — curva degradazione qualità/costo
  - 📊 `ai-dev/course/diagrams/excalidraw/07-agents-skills-commands.excalidraw` — tabella comparativa

- **Esempio concreto:**
  - `CLAUDE.md` (globale `~/.claude/CLAUDE.md`) vs `instructions.md` (`~/.codex/instructions.md`)
  - Skill reale: `~/.claude/skills/pre-commit.md` vs `~/.codex/skills/pre-commit` — stessa logica, file identici o quasi
  - Hook di sicurezza: `~/.claude/hooks/handlers/bash.py` (blocca `rm -rf`, `--no-verify`) vs `~/.codex/hooks/handlers/safety.py` — mostra l'exit code convention (0/1/2)
  - `settings.json` (Claude Code) vs `hooks.json` (Codex) con `PreToolUse`/`PostToolUse` affiancati
  - Rules: `~/.claude/rules/tdd.md` vs `~/.codex/rules/tdd.rules` — lo stesso vincolo su due formati

- **Primitive coperte (in sequenza):**
  1. Behavioral contract — `CLAUDE.md` (3 livelli: globale / workspace / progetto) vs `instructions.md`

  **→ Bridge: Prompt Engineering ≠ Chatting (8-10 min)**

  Prima di passare alla configurazione, un aggancio alla disciplina. Lo slide dal video Anthropic Summit mostra la struttura a 10 livelli di un prompt serio:

  | Layer (API)                          | Equivalente nel nostro setup CLI            |
  | ------------------------------------ | ------------------------------------------- |
  | 1. Task context                      | Sezione `## Style` e ruolo in CLAUDE.md     |
  | 2. Tone context                      | `## Style` ("Direct. No cheerleading.")     |
  | 3. Background data & docs            | Rules files + project CLAUDE.md             |
  | 4. Detailed task description & rules | `~/.claude/rules/*.md` (27+ files)          |
  | 5. Examples                          | Few-shot inline nelle skill                 |
  | 6. Conversation history              | Context window + memory system (→ Blocco 3) |
  | 7. Immediate task / request          | Il prompt dell'utente / slash command       |
  | 8. Thinking step by step             | Adaptive thinking del modello               |
  | 9. Output formatting                 | XML tags nelle skill, structured output     |
  | 10. Prefilled response               | Deprecato in Claude 4.6+ — nota storica     |

  Key message: _"State già facendo prompt engineering — il CLAUDE.md è il vostro system prompt persistente."_

  **Console/Workbench (1 min):** Mostra screenshot. "Per chi costruisce applicazioni API, questo è il banco di prova interattivo. Per chi usa la CLI, il banco di prova è il CLAUDE.md + una sessione live." Basta — non vendere, solo posizionare.

  **Gap check su nostro setup (2 min):** Due punti deboli che queste best practice illuminano:
  - _Più esempi nelle rules_: le nostre rules sono dichiarative ("write tests first") senza before/after. Anthropic dice "few-shot examples dramatically improve accuracy". Margine di miglioramento reale.
  - _Validazione esterna_: la sezione "Overeagerness" dei docs Anthropic raccomanda ufficialmente le stesse regole del nostro `## Style` ("don't add features beyond asked"). Non siamo opinionati — siamo allineati.
  2. Configurazione — `settings.json` + permission modes vs `config.toml` + approval policy/sandbox
  3. **Context rot (5 min):** fenomeno: sessione lunga → più token di input → costo crescente + output quality che degrada. Dati di ricerca (paper/benchmark). Exit prematura. Motivazione per tutto il sistema di hooks e memoria.
  4. **Custom agents vs skills vs commands (5 min):** tabella comparativa — Skill (slash command Markdown, workflow riusabile), Command (alias breve, una riga), Agent (subagent con modello e tool propri, context isolato). Quando usare quale.
  5. **MCP vs CLI tools (3 min):** MCP = protocollo per dare tool esterni agli agenti (database, API, filesystem). CLI tools = comandi bash. Le skill del setup usano entrambi. Tools riducono il contesto rispetto a chiamate API raw.
  6. Skills — slash commands Markdown (`/pre-commit`, `/fix`, `/ship`, `/discovery`) — stessa implementazione su entrambi
  7. Hooks — 5 eventi (PreToolUse, PostToolUse, SessionStart, Stop, Notification); tipi: command / prompt / agent; exit codes 0/1/2
  8. Rules — Markdown behavioral constraints (27 su Claude, formato `.rules` su Codex)
  9. Agents + Plugin — subagenti specializzati (Explore/Plan/general-purpose) + plugin come bundle
  10. **Prompt injection (2 min):** rischio concreto — input malevolo che reindirizza il comportamento dell'agente. Mitigazione: hooks di validazione, permission model restrittivo, no bypass.

- **Cut:** Non si apre il codice interno degli handler Python. Non si fa `/plugin install` live. Il Memory system è rimandato al Blocco 3. Worktrees rimandati al Blocco 5.

> ⚠️ **Nota timing:** Con le aggiunte, questo blocco sale a ~80 min. Comprimere a 65 min significa tagliare MCP (2 min) e accorciare context rot (3 min invece di 5).

---

## Blocco 3: Persistent Memory (30min)

- **Key message:** La sessione è effimera, il sistema deve essere persistente — il tuo job è costruire l'infrastruttura di memoria attorno all'agent.

- **Demo artifact:**
  1. **Stop hook live (10 min):** 📊 `ai-dev/course/diagrams/excalidraw/10-memory-flow.excalidraw` — Termina una sessione Claude Code davanti agli studenti → apri `.claude/memory/local/continuation.md` → mostra cosa è scritto automaticamente (branch, commit recenti, file uncommitted). Poi avvia una nuova sessione e mostra come `session.py` inietta quel contesto nel system prompt.
  2. **Memory recall live (10 min):** `/memory recall "authentication"` — mostra il risultato (FTS5 + Thesaurus) con i file di memoria trovati. Poi apri un file memoria Markdown con frontmatter YAML per mostrare la struttura.
  3. **Strategie di memoria (10 min):** 📊 `ai-dev/course/diagrams/excalidraw/11-strategie-memoria.excalidraw` — Context window limits + tradeoff compaction vs continuità. Perché non compattare per default (azzera il caching). Le 3 strategie: continuation (breve, auto), memory recall (strutturata, on-demand), sessione lunga senza compaction (costosa ma cache-friendly).

- **Esempio concreto:**
  - `.claude/memory/local/continuation.md` — generato automaticamente dall'hook Stop
  - `~/.claude/memory/` — file Markdown con frontmatter YAML (`name`, `description`, `type: feedback/project/user/reference`)
  - `~/.claude/hooks/handlers/memory.py` — mostra solo il concetto (scrive al termine della sessione), non il codice interno
  - `/memory recall` output — risultato FTS5 con snippet e score di rilevanza

- **Cut:** Thesaurus semantic search (rimandato a Module 5). Schema SQLite FTS5 (`CREATE VIRTUAL TABLE`) e codice `memory_db.py` — disponibili se richiesti, non nella demo principale. Atrium integration fuori scope.

---

## Blocco 4: Modelli Alternativi (35min)

- **Key message:** Non sei vincolato a un provider né a un tool — la stessa primitiva (skill, hook, rule) gira su Claude Code (Claude), Codex (GPT), OpenCode (modelli open). La scelta del modello è una decisione economica e di privacy, non tecnica.

- **Demo artifact:**
  1. **Panoramica modelli (10 min):** Tabella comparativa commerciali vs open. Claude (Haiku/Sonnet/Opus) su Claude Code, GPT (4.1-mini, o3) su Codex, Qwen3/DeepSeek/Llama via OpenCode o Ollama. Excalidraw per la mappa tool ↔ modello.
  2. **Demo velocità locale (15 min):** Qwen3 30B-A3B su MLX (Studio Mac) — mostra la velocità token/s a zero costo, zero network. DeepSeek V4 Flash via OpenRouter — mostra la stessa query con pricing reale. Setup fatto prima della sessione (Claude Code usato per l'installazione).
  3. **OpenCode (5 min):** Terza CLI open-source che usa modelli aperti (Qwen3, Llama, DeepSeek locali). Installazione mostrata o già fatta, panoramica config.
  4. **Configurazione (5 min):** `settings.local.json` con `ANTHROPIC_BASE_URL` → Ollama, `config.toml` Codex con `[providers.openrouter]`.

- **Esempio concreto:**
  - `~/.claude/settings.local.json` con `ANTHROPIC_BASE_URL: "http://localhost:11434/v1"` e `ANTHROPIC_API_KEY: "ollama"`
  - `~/.codex/config.toml` con `[providers.openrouter]` e modello `deepseek/deepseek-v4-flash`
  - Tabella routing dalla regola `~/.claude/rules/model-selection.md` (haiku → esplorazione, sonnet → implementazione, opus → architettura, locale → privacy/costo zero)

- **Cut:** Benchmark formali e numeri di accuracy — non è una review accademica. Gemini e i modelli Google rimangono nella panoramica ma non si approfondiscono. Fine-tuning e modelli custom fuori scope.

---

## Blocco 5: Harnessing — Il Workflow Completo (30min)

- **Key message:** CLAUDE.md non è documentazione — è il contratto che definisce come il sistema si comporta dall'inizio alla fine del ciclo. Il workflow codificato nel CLAUDE.md è il prodotto.

- **Demo artifact:** Continuazione della pipeline avviata nel Cold Open. Il workflow è spec-driven: si decide cosa fare (spec/storia), poi si delega l'esecuzione.
  1. **Spec-driven dev (5 min):** 📊 `ai-dev/course/diagrams/excalidraw/04-pipeline-spec-driven.excalidraw` + `ai-dev/course/diagrams/excalidraw/14-context-engineering-layers.excalidraw` — `/discovery` → `/design` — da idea a feature spec strutturata. Il developer come specifier: "decidi le priorità e le storie, non scrivi il codice."
  2. **Ciclo completo (15 min):** `/implementation` (TDD) → `/pre-commit` (quality gates: lint, test, security) → `/ship` → `/pr-merge` → `/release full` (tag semantico, CHANGELOG) → `/health full` → `/docs full`
  3. **Reflection loop + quality gates (3 min):** `/review` post-implementation come reflection automatica. `/pre-commit` come gate non bypassabile.
  4. **Ralph Wiggum Loop + /loop nativo (5 min):** 📊 `ai-dev/course/diagrams/excalidraw/15-ralph-loop.excalidraw` — alternativa leggera al workflow manuale. `/loop` nativo di Claude Code per cicli ripetitivi. Ralph Loop = script bash + Stop hook per agent loop autonomo senza interazione.
  5. **Pattern avanzati — citazione (2 min):** git worktrees per isolamento task rischiosi, headless mode (`claude -p`, `codex exec`) per CI/CD e automazione non interattiva, GitHub Action con agente headless.

- **Esempio concreto:**
  - `~/.claude/CLAUDE.md` — sezione Workflow che definisce l'intera pipeline
  - `~/.claude/rules/tdd.md` — red-green-refactor obbligatorio
  - Output reale di `/release full` — tag git, CHANGELOG aggiornato
  - Script Ralph Loop: bash + Stop hook per loop autonomo

- **Cut:** Operations post-deploy (`/ops`) fuori scope, è territorio Module 5. Semantic versioning in dettaglio (cenno in /release full).

> ⚠️ **Nota timing:** Con Ralph Loop + pattern avanzati, questo blocco sale a ~40 min. Valutare se accorciare il workflow completo o spostare Ralph Loop nel Blocco 6.

---

## Blocco 6: Pattern Esterni — Citazione (25min)

- **Key message:** Steal patterns, don't adopt frameworks — questi tool esistono, risolvono problemi reali, ma il tuo setup opinionato batte sempre il framework generico.

- **Demo artifact:**
  1. **I tre framework (10 min):** 📊 `ai-dev/course/diagrams/excalidraw/16-framework-comparison.excalidraw` — GSD (59K+ stelle), BMAD (9 agenti), Superpowers (150K+ stelle, plugin ufficiale Anthropic).
  2. **Confronto affiancato (10 min):** Tabella "problema → come lo risolve GSD/BMAD/Superpowers → come lo risolve il nostro setup". Per ogni riga, mostra che il tuo setup ha già quella soluzione — e spesso più integrata.
  3. **Perché me lo son fatto da solo (5 min):** Il tuo setup è calibrato sul workflow reale (Forgejo, Atrium, Thesaurus, Fabrica). I framework sono generici. La genericità è un costo nascosto.

- **Esempio concreto:**
  - `ai-dev/docs/external-patterns.md` — la tabella di confronto già scritta
  - Link GitHub ai tre framework con stelle attuali (GSD, BMAD, Superpowers)
  - `~/.claude/skills/` — 50+ skill custom come controprova: "questo livello di integrazione non esiste in nessun framework generico"

- **Demo artifact:**
  1. **I tre framework (10 min):** GSD (59K+ stelle — risolve context rot), BMAD (9 agenti specializzati in pipeline agile), Superpowers (150K+ stelle, plugin ufficiale Anthropic — 5 fasi obbligatorie). Dove si complementano, criteri di scelta tra loro.
  2. **Confronto affiancato (8 min):** Tabella "problema → soluzione GSD/BMAD/Superpowers → come il nostro setup lo risolve". Il setup custom batte il framework generico perché è calibrato sul workflow reale.
  3. **Il ruolo che cambia (5 min):** Chiusura della giornata. "Da writer a specifier/orchestrator/reviewer. Cosa sopravvive dei principi classici: le decisioni architetturali, il giudizio sulla qualità, la responsabilità del prodotto." Da tool individuale a infrastruttura di team.
  4. **Debrief (2 min):** Dove serve l'intervento umano. Quando la struttura è giustificata e quando no.

- **Esempio concreto:**
  - `ai-dev/docs/external-patterns.md` — tabella di confronto già scritta
  - Link GitHub ai tre framework con stelle attuali
  - `~/.claude/skills/` — 50+ skill custom come controprova dell'integrazione custom

- **Cut:** Installazione live di nessun framework. Demo comparativa live Superpowers vs Ralph Loop — tagliata. Deep dive BMAD internals. La risposta a "quale framework adotto?" è: "capisci cosa risolvono e costruisci il tuo".

---
