# Reading List — AI-Dev + LLM-Ops

Fonti organizzate per sessione e topic. Le fonti con ★ sono prioritarie per chi ha poco tempo.

---

## SESSION 1: AI-Driven Development

### Blocco 1 — Cold Open: Landscape e Dati

**Ufficiali Anthropic**

- ★ [How AI Is Transforming Work at Anthropic](https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic) — 132 engineer surveyed, 50% boost, 60% usage, 27% "wouldn't have done otherwise"
- ★ [Estimating AI productivity gains](https://www.anthropic.com/research/estimating-productivity-gains) — +80% task speed, extrapolato a +1.8% US labour growth

**Ricerche contrastanti (dati onesti)**

- [METR — Experienced OS Dev Productivity](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) — AI ha causato -19% più lento nonostante i dev credessero +20%
- [METR — Changing Experiment Design](https://metr.org/blog/2026-02-24-uplift-update/) — parziale ritrattazione
- [GitHub Copilot Productivity](https://arxiv.org/abs/2302.06590) — RCT 95 dev: +55.8% task completion speed

**Landscape e narrativa**

- ★ [Andrej Karpathy: Software Is Changing (Again)](https://www.youtube.com/watch?v=LCEmiRjPEtQ) — Software 3.0, YC AI Startup School
- [Karpathy — 2025 LLM Year in Review](https://karpathy.bearblog.dev/year-in-review-2025/) — 6 paradigm shifts, RLVR, jagged intelligence
- [36 AI Coding Agents & IDEs](https://x.com/d4m1n/status/1894841072963952657) — panoramica comparativa
- [Supply Chain Attacks: Python Developers Hacked](https://www.encryptionconsulting.com/the-new-era-of-supply-chain-attacks-python-developers-hacked-in-sophisticated-supply-chain-attack/) — contesto per hook supply chain

---

### Blocco 2 — Claude Code + Codex: Anatomia e Configurazione

**Ufficiali Claude Code**

- ★ [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices) — CLAUDE.md, context management, session workflow, anti-pattern
- [CLAUDE.md reference](https://code.claude.com/docs/en/memory) — behavioral contract, struttura, importazioni
- [Sub-agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents) — subagenti custom, memory frontmatter, agent definitions, foreground vs background
- [Agent Teams](https://docs.anthropic.com/en/docs/claude-code/agent-teams) — coordinazione multi-sessione (research preview): lead, teammate, task list, mailbox

**MCP & Tool design**

- ★ [Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents) — prototipazione, eval, iterazione con Claude Code
- [MCP Deep Dive — Future of AI Tooling](https://a16z.com/a-deep-dive-into-mcp-and-the-future-of-ai-tooling/) — standard aperto, marketplace, agentic workflow
- [MCP 10x Cursor workflow](https://x.com/jasonzhou1993/status/1893514487136952688) — MCP concreto: browser console, Replicate, Supabase, Figma

**Prompt Engineering**

- [Prompt Engineering](https://readwise-assets.s3.amazonaws.com/media/wisereads/articles/prompt-engineering/22365_3_Prompt-Engineering_v7-1.pdf) — Google whitepaper (Lee Boonstra): zero-shot, few-shot, chain of thought, temperature
- ★ [A1] [Claude Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — Anthropic set 2025: long-horizon reasoning, state tracking, "right altitude" per system prompt (no hardcoded brittle, no troppo vago), agentic systems

**Sicurezza**

- [17 security checks VIBE → PRODUCTION](https://x.com/Kaamiiaar/status/1902342578185630000) — checklist incollabile in Claude Code
- [Web App Security Checklist](https://x.com/cj_zZZz/status/1903107031814279293) — 36 app testate con AI
- [Obsidian: Less is safer](https://obsidian.md/blog/less-is-safer/) — filosofia dependency minimalista
- [Antirez — Secure Auth / DJI + Claude Code](https://www.youtube.com/watch?v=97FV7kvG-s8) — prompt injection, incidente reale

---

### Blocco 3 — Persistent Memory

- ★ [Karpathy LLM Wiki (gist)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — pattern raw/ → wiki/ senza vector DB
- [Self-Evolving Claude Code Memory](https://www.youtube.com/watch?v=7huCP6RkcY4) — Cole Medin: implementazione Karpathy con Claude Code
- [Karpathy 10x'd Claude Code](https://www.youtube.com/watch?v=sboNwYmH3AY) — Nate Herk: LLM Wiki + Obsidian

---

### Blocco 4 — Modelli Alternativi

- ★ [Mass Intelligence — From GPT-5 to Nano Banana](https://www.oneusefulthing.org/p/mass-intelligence) — Mollick: GPT-4 $50/M → GPT-5 Nano $0.14/M, 1B persone con AI frontier

---

### Blocco 5 — Harnessing

- ★ [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — Anthropic: initializer + coding agent, multi-context-window
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — workflow vs agents, start simple, transparency
- [Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents) — pattern composabili, team reali
- ★ [A2] [Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk) — Anthropic set 2025: loop gather→act→verify, agentic search vs semantic, compaction, subagents, visual feedback, LLM-as-judge. Nota: Claude Code SDK rinominato Claude Agent SDK
- [My LLM codegen workflow](https://harper.blog/2025/02/16/my-llm-codegen-workflow-atm/) — spec → plan → execute in discrete loop
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — Ralph Loop ispirazione: AI agenti su ML research in loop autonomo
- [Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — caching, TTL, auto-caching

---

### Blocco 6 — Pattern Esterni e Ruolo che Cambia

- ★ [Product management on the AI exponential](https://claude.com/blog/product-management-on-the-ai-exponential) — Cat Wu (Claude Code PM): sprint corti, demo-first, test ad ogni nuovo modello
- [Vibe Coding](https://x.com/karpathy/status/1886192184808149383) — Karpathy: tweet originale, anti-pattern
- [Collaborating with AI Agents](https://arxiv.org/abs/2503.18238) — 2,234 partecipanti: +50% output ma jagged frontier (immagini peggiori)
- [AI Doesn't Reduce Work — It Intensifies It](https://hbr.org/2026/02/ai-doesnt-reduce-work-it-intensifies-it) — Berkeley Haas: intensificazione, non riduzione
- [How Humans and AI Are Working Together](https://hbr.org/2018/07/collaborative-intelligence-humans-and-ai-are-joining-forces) — HBR: 1,500 aziende, 5 principi
- [Lean and AI](https://www.lean.org/the-lean-post/articles/lean-and-ai/) — Matt Savas: AI amplifica il problem-solving capability, non lo sostituisce

---

## SESSION 2: LLM Ops — Agents in Production

### Architettura e Pattern Agenti

- ★ [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — workflow vs agents, start simple, transparency
- ★ [Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents) — pattern composabili da decine di team reali
- ★ [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — initializer + coding agent per sessioni multi-ora
- [LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) — Lilian Weng: planning, memory, tool use (fondamentale)
- [AI Agents Learning Roadmap](https://www.youtube.com/watch?v=k-Cj6H6Zwos) — Cole Medin: Langfuse, Pydantic AI, RAG agent

### MCP & Tool Design

- ★ [Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents) — prototipazione, evals, iterazione
- [MCP Deep Dive](https://a16z.com/a-deep-dive-into-mcp-and-the-future-of-ai-tooling/) — a16z: architettura, marketplace, future

### Evals & Produttività

- ★ [Anthropic Economic Index — Economic Primitives](https://www.anthropic.com/research/anthropic-economic-index-january-2026-report) — 5 primitivi: task complexity, skills, context, autonomy, success rate
- [Anthropic Economic Index — Learning Curves](https://www.anthropic.com/research/economic-index-march-2026-report) — fluency longitudinale, diversificazione uso
- [AI-Assisted Software Dev: 3 Field Experiments](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4945566) — 4,867 dev: +26% completed tasks
- [Generative AI at Work](https://www.nber.org/papers/w31161) — Brynjolfsson: 5,172 support agents, +14%, novice boost
- [RCTs and Human Uplift Studies](https://arxiv.org/abs/2603.11001) — meta-paper: perché le misurazioni RCT si stanno rompendo
- [Goldman Sachs — No Economy-Wide Relationship](https://fortune.com/2026/03/03/goldman-earnings-ai-anxiety-no-meaningful-impact-productivity-economy-30-percent-in-2-areas/) — macro vs micro
- [Microsoft New Future of Work 2025](https://www.microsoft.com/en-us/research/publication/new-future-of-work-report-2025/) — ~100 studi, workslop, produttività collettiva
- [AI Adoption — European Firms](https://www.bis.org/publ/work1325.htm) — BIS: 12K+ firm, +4% labour prod.
- [AI, Productivity, Labor Markets](https://laweconcenter.org/resources/ai-productivity-and-labor-markets-a-review-of-the-empirical-evidence/) — miglior sintesi indipendente
- [Collaborating with AI Agents](https://arxiv.org/abs/2503.18238) — 2,234 partecipanti, jagged frontier

### Context Engineering

- ★ [A3] [Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — Anthropic set 2025: context rot (n² attention, degradazione graduale), "right altitude" per system prompt, just-in-time retrieval vs semantic, 3 leve per long-horizon (compaction, structured note-taking, sub-agent architecture), progressive disclosure
- ★ [A2] [Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk) — vedi anche Blocco 5 Session 1. Sezione verify loop: rules-based, visual feedback, LLM-as-judge

### Memory & RAG

- ★ [Karpathy LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — raw/ → wiki/ pattern
- [Embeddings in RAG LLMs](https://coralogix.com/ai-blog/understanding-the-role-of-embeddings-in-rag-llms/) — semantic chunking, context window
- [Turn ANY Website into LLM Knowledge](https://www.youtube.com/watch?v=JWfNLF_g_V0) — Crawl4AI, Pydantic AI agent
- [Build Your Own RAG Locally](https://hackernoon.com/a-tutorial-on-how-to-build-your-own-rag-and-how-to-run-it-locally-langchain-ollama-streamlit) — Langchain + Ollama + Streamlit

### Economics & Model Routing

- ★ [Mass Intelligence — From GPT-5 to Nano Banana](https://www.oneusefulthing.org/p/mass-intelligence) — Mollick: cost collapse, 1B persone con frontier AI

---

## Gap — Fonti da aggiungere al vault

Questi topic sono nei moduli ma non hanno fonti dedicate nel vault. Da cercare e salvare:

| Topic                        | Fonti consigliate                                                       |
| ---------------------------- | ----------------------------------------------------------------------- |
| **Langfuse**                 | https://langfuse.com/docs — setup, tracing, scores, datasets            |
| **OpenRouter**               | https://openrouter.ai/docs — pricing, routing, fallback                 |
| **LLM-as-Judge**             | Hamel Husain: https://hamel.dev/blog/posts/evals/ · già coperto in [A2] |
| **Guardrails**               | NeMo Guardrails docs, Guardrails AI docs                                |
| **Token budgeting**          | Anthropic pricing + case study costi in produzione                      |
| **Model routing strategies** | OpenRouter docs + routing pattern blog post                             |
