---
name: ticket-triage
description: Classify a support ticket, draft a reply, and decide reply/ask_clarification/escalate. Use when triaging customer tickets or demoing the support triage agent from the LLMOps reference scenario.
---

# Ticket Triage Skill

Run the support triage agent against a customer ticket and return structured output.

## Workflow

1. Read the ticket text from the user prompt
2. Call `run_support_triage_agent(prompt, deps)` from `src/llm_ops_v1/agents/base_agent.py`
3. Parse and display the four required output fields

## Required Output Fields

Every triage response must include:

- **Category** — one of: `billing_issue`, `shipping_delay`, `technical_problem`, `other`
- **Reply draft** — concise, empathetic response addressed to the customer
- **Decision** — one of: `reply`, `ask_clarification`, `escalate`
- **Estimated cost** — USD cost for this API call (e.g. `$0.0003`)

## Example Invocations

**Billing ticket:**

> User: "I was charged twice for my subscription this month."
> → Category: billing_issue | Decision: escalate (involves refund)

**Shipping delay:**

> User: "My order hasn't arrived in 10 days."
> → Category: shipping_delay | Decision: reply (provide tracking update)

**Technical issue:**

> User: "The export button doesn't work on Safari."
> → Category: technical_problem | Decision: ask_clarification (browser version?)

## Running Without an API Key

When no `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set, the agent uses `TestModel`
and returns a deterministic placeholder response — useful for CI and offline demos.

## Quick Start

```python
import asyncio
from llm_ops_v1.agents.base_agent import run_support_triage_agent, SupportTriageDependencies

deps = SupportTriageDependencies(ticket_id="demo-001", customer_tier="standard")
result = asyncio.run(run_support_triage_agent("I was charged twice.", deps))
print(result)
```
