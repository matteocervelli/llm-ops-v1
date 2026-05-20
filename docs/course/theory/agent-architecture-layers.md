# Agent Architecture — The 7 Layers

Teaching reference for Module 5. Maps the abstract framework to the support triage reference scenario.

## The Framework

An agent is not a fixed object with a fixed architecture. It is a space of possibilities. The 7 layers are a _pool_ — each query activates a different subset.

> "L'agente non ha una forma. Ha dei percorsi." — pinperepette, 2026

---

## Layer 1: Input / Context

**What it is**: Everything that enters the system before the model processes the prompt.
Sources: user prompt, conversation history, internal data (files, DB), external events (webhooks, schedulers), external data (APIs, sensors).

**In the support triage agent**:

- Input: the ticket (subject + body + customer metadata)
- Context: previous tickets from same customer (episodic memory), service catalog (CAG static)
- Events: webhook POST `/webhook/ticket` (Layer 1 event-driven — see Agent SDK prototype)

**What breaks without it**: Agent has no context. Each ticket treated as if the customer has never contacted support before.

---

## Layer 2: Context Construction

Three techniques, three objectives:

| Technique                                | Purpose                                   | In triage agent                                                                     |
| ---------------------------------------- | ----------------------------------------- | ----------------------------------------------------------------------------------- |
| **CAG** (Context-Augmented Generation)   | Pre-built static context                  | System prompt with triage rules, escalation policy, response templates              |
| **RAG** (Retrieval-Augmented Generation) | On-demand semantic retrieval              | Fetch similar past tickets to inform current response                               |
| **KG** (Knowledge Graph)                 | Entity relationships, multi-hop reasoning | Not used in v1 — would enable "customer belongs to enterprise tier → different SLA" |

**Prompt caching lives here**: the CAG (system prompt) is the cache-eligible content. Keep it static, maximize cache hit rate.

**What breaks without it**: Agent hallucinates policy details, invents escalation paths that don't exist, doesn't recognize repeat customers.

---

## Layer 3: Orchestration

Who decides and how.

| Pattern              | When to use                        | In triage agent                                     |
| -------------------- | ---------------------------------- | --------------------------------------------------- |
| **Single agent**     | Simple, predictable tasks          | Password reset → Haiku direct response              |
| **Planner-executor** | Complex tasks needing a plan first | Multi-issue ticket → Sonnet with planning           |
| **Multi-agent**      | Parallel specialist work           | Classifier + responder + cost estimator in parallel |

**The router** (`router.py` — see issue #[Module5|10]):

```python
def decide_form(ticket: str) -> AgentForm:
    if is_simple(ticket):   return AgentForm.SINGLE_HAIKU
    if is_complex(ticket):  return AgentForm.PLANNER_SONNET
    return AgentForm.ESCALATE  # confidence < 0.7
```

**What breaks without it**: Every ticket gets the same agent regardless of complexity. Simple tickets waste Sonnet tokens. Complex tickets get Haiku and produce poor responses.

---

## Layer 4: Tools / Actions

The agent's hands. Without tools, the agent talks.

**In the triage agent**:

- DB lookup: `get_customer_history(customer_id)` — previous tickets
- Cost estimator: `estimate_cost(model, input_tokens, output_tokens)` — for logging
- Escalation: `create_escalation_ticket(ticket_id, reason)` — creates a new ticket in the system
- Knowledge base: `search_kb(query)` — finds relevant documentation

**Contract for each tool**: schema input, output format, expected errors. If the tool schema changes without updating the agent, the tool call fails silently or with a cryptic error.

---

## Layer 5: Output / Results

**In the triage agent**: classification (billing/shipping/technical/other), draft response, decision (reply/ask_clarification/escalate), estimated cost.

**Side-effect chain**: one ticket processing produces:

- 1 classification stored in DB
- 1 draft response (text)
- 1 cost log entry in Langfuse
- Optionally: 1 escalation ticket created

**Output audit trail** (see dashboard update): log each output with type, channel, outcome, cost. Enables the Module 5 operational dashboard.

---

## Layer 6: Evaluation & Control (Guardrails)

Two distinct mechanisms:

**Runtime guardrails** (per-response, real-time):

- PII check: response contains another customer's phone → block
- Confidence threshold: classifier < 0.7 → escalate instead of respond
- Cost cap: single ticket exceeds $X → block, log, escalate
- Hallucination check: response cites "policy X" → verify policy exists

**Evals** (aggregate, periodic):

- LLM-as-Judge: score response quality on a dataset of past tickets
- Rubric: accuracy, tone, completeness, escalation rate
- Trigger: weekly, or on model change, or after prompt update

**The key difference**: guardrails protect _individual responses_. Evals measure _aggregate quality_. You need both. Guardrails without evals = you prevent disasters but drift slowly. Evals without guardrails = you know quality is degrading but can't stop individual bad outputs.

---

## Layer 7: Memory (Transversal)

Memory crosses all layers. Three tiers:

| Tier             | Implementation                             | TTL              | Use in triage                                    |
| ---------------- | ------------------------------------------ | ---------------- | ------------------------------------------------ |
| **Short-term**   | `RedisSessionState` (Hash)                 | Session duration | Current ticket context, conversation turns       |
| **Episodic**     | `EpisodicMemory` (Redis List)              | 7 days           | Customer ticket history — "3rd ticket this week" |
| **Prompt cache** | Anthropic `cache_control` on system prompt | 5 min            | Amortize system prompt cost across tickets       |

**The corruption tradeoff**: every summarization replaces original context with a compression. Episodic memory records events but not verbatim exchanges. The source of truth is the ticket database — agent memory is an operational aid, not an archive.

**Redis Array (future)**: ARSET/ARGREP merged 2026-05-14. Enables shared memory between parallel agents — one agent's findings become immediately queryable by others.

---

## The 4 Forms of the Triage Agent

| Form           | Trigger                            | Layers active                                | ~Cost       |
| -------------- | ---------------------------------- | -------------------------------------------- | ----------- |
| **Direct**     | Simple ticket, high confidence     | 1,2(CAG),3(single-Haiku),4,5,6(PII+cost)     | $0.001      |
| **Considered** | Complex ticket                     | 1,2(CAG+RAG),3(planner-Sonnet),4,5,6(full),7 | $0.02       |
| **Escalated**  | Low confidence or policy violation | 1,2,3→escalate,5,6                           | $0.005      |
| **Analyzed**   | Batch eval run                     | 1,2,3,4,5,6(judge),7                         | $0.10/batch |

Same system. Same code. Different paths per ticket.
