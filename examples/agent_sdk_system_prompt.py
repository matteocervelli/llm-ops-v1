"""
Agent SDK — System Prompt con struttura a 10 layer + XML tags

Questo esempio mostra come costruire un system prompt completo
per un agente di code review usando l'Anthropic Python SDK.
Ogni sezione corrisponde a un layer della struttura consigliata.

Refs:
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/
  - 18-prompt-structure-standalone.excalidraw
  - 17-prompt-engineering-bridge.excalidraw
"""

import anthropic

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
# Struttura: <role> → <tone> → <context> → <rules> → <examples> → <output_format>
# Layers 7-8 (request + thinking) arrivano dal messaggio utente, non dal system prompt.
# Layer 10 (prefilled response) è deprecato in Claude 4.6+ — non usare.

SYSTEM_PROMPT = """\
<role>
Sei un agente esperto di code review specializzato in Python e sicurezza.
Il tuo obiettivo è analizzare il codice fornito, identificare bug,
vulnerabilità di sicurezza e problemi di qualità.
</role>

<tone>
Diretto e costruttivo. Segnala i problemi chiaramente.
Proponi fix concreti dove possibile. Nessuna introduzione ridondante.
</tone>

<context>
Stai lavorando su una codebase Python in produzione.
Le issue di sicurezza hanno priorità assoluta.
Usa OWASP Top 10 come riferimento per le vulnerabilità.
</context>

<rules>
- Controlla sempre le vulnerabilità di sicurezza PRIMA di qualsiasi altra cosa
- Segnala credenziali hardcoded o secrets come CRITICO — stop immediato
- Verifica che le funzioni pubbliche abbiano type hints
- Controlla che l'error handling sia appropriato ai boundary (input utente, API esterne)
- Se un file non ha problemi, scrivi esplicitamente "Nessun problema trovato"
- Non inventare problemi che non esistono nel codice fornito
</rules>

<examples>
<example>
<input>
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    return db.execute(query)
</input>
<review>
CRITICO: SQL injection — usa query parametrizzate.

```python
def get_user(user_id: int) -> dict | None:
    return db.execute("SELECT * FROM users WHERE id = ?", [user_id])
```

AVVISO: Mancano type hints sul parametro e sul return.
</review>
</example>

<example>
<input>
def calculate_total(items: list[dict]) -> float:
    return sum(item["price"] * item["qty"] for item in items)
</input>
<review>
Nessun problema trovato.
</review>
</example>
</examples>

<output_format>
Struttura ogni review così:

CRITICO: [vulnerabilità sicurezza o data loss]
ERRORE: [bug che rompono la funzionalità]
AVVISO: [type hints mancanti, error handling carente, codice poco chiaro]
INFO: [suggerimenti di miglioramento, non obbligatori]

Se non ci sono issue in una categoria, ometti quella categoria.
Inserisci il fix corretto in un blocco ```python``` per ogni CRITICO ed ERRORE.
</output_format>
"""

# ── USER PROMPT TEMPLATE ───────────────────────────────────────────────────────
# Layer 7: Immediate task/request — wrappato in XML tag per separarlo dal contesto
# Layer 8: Thinking step by step — istruzione esplicita di ragionare prima di rispondere

USER_PROMPT_TEMPLATE = """\
<code_to_review filename="{filename}">
{code}
</code_to_review>

Prima analizza la sicurezza riga per riga, poi la correttezza, poi la qualità.
Ragiona step by step prima di scrivere la review.
"""

# ── SDK CALL ───────────────────────────────────────────────────────────────────


def review_code(filename: str, code: str) -> str:
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        cache_control={"type": "ephemeral"},  # auto-caching: SYSTEM_PROMPT cached after first call
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    filename=filename,
                    code=code,
                ),
            }
        ],
    )

    return response.content[0].text


# ── DEMO — codice intenzionalmente problematico per il code review agent ───────

BAD_CODE_EXAMPLE = """
import os

# DEMO: credenziale hardcoded — vulnerabilità intenzionale per la demo
API_KEY = "sk-prod-abc123xyz"

def fetch_data(user_input):
    # DEMO: concatenazione SQL non sicura — vulnerabilità intenzionale
    query = "SELECT * FROM logs WHERE user = " + user_input
    return db.execute(query)

def process_items(items):
    total = 0
    for item in items:
        total = total + item["price"]
    return total
"""

if __name__ == "__main__":
    print(review_code("app/data.py", BAD_CODE_EXAMPLE))
