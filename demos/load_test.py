"""Load test — run N tickets in parallel via dispatch and print results."""

import asyncio
import sys
import time

sys.path.insert(0, "src")

from llm_ops_v1.agents.dispatch import available_models, dispatch

_TICKETS = [
    "Il mio pacco non e arrivato.",
    "Doppio addebito in fattura.",
    "L'app si blocca sui pagamenti.",
    "Voglio disdire il mio abbonamento.",
    "Non riesco a fare il login.",
    "Enterprise SSO non funzionante.",
    "Dove e la mia ricevuta fiscale?",
    "Il rimborso non e arrivato dopo 10 giorni.",
    "Aggiornare indirizzo di spedizione.",
    "Consegnato ma non ricevuto.",
    "Fattura con dati aziendali.",
    "Informazioni sbagliate dall assistente.",
    "Link reso non funziona.",
    "Account bloccato.",
    "Offerta non applicata.",
    "Prodotto sbagliato.",
    "Non scarico le istruzioni.",
    "Sito non disponibile.",
    "Codice promo non accettato.",
    "Help.",
]


async def run_one(ticket: str, idx: int, model_id: str | None) -> str:
    t = time.perf_counter()
    if model_id:
        r = await dispatch(ticket, model_id)
        ms = int((time.perf_counter() - t) * 1000)
        return f"  [{idx + 1:02d}] {r.text[:70]!r}  cost=${r.cost_usd:.5f} {ms}ms"
    return f"  [{idx + 1:02d}] [offline — no provider keys configured]"


async def main(n: int) -> None:
    models = available_models()
    mid = models[0] if models else None
    print(f"model={mid or 'none'}  tickets={n}")
    print()

    tasks = [run_one(_TICKETS[i % len(_TICKETS)], i, mid) for i in range(n)]
    t0 = time.perf_counter()
    results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - t0

    for line in results:
        print(line)
    print(f"\n  Total: {n} tickets in {elapsed:.1f}s")


n_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 8
asyncio.run(main(n_arg))
