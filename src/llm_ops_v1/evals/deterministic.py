# Deterministic judge — zero-dependency, CI-safe evaluator.
# Moved from dashboard/demo_runner.py so the eval layer is independent of the UI.
# Use this in regression suites where calling a real LLM would be too slow or costly.
# Scoring: 8 (pass) / 4 (fail) — intentionally coarse; it is a structural check,
# not a semantic one. See ClaudeJudge for semantic scoring.

from llm_ops_v1.evals.llm_judge import JudgeScore

_ACTION_KEYWORDS = ("decision:", "reply", "escalate", "clarif")


def evaluate(prompt: str, output: str) -> JudgeScore:
    """Sync entry point — use from sync callers (dashboard, CLI)."""
    intent_terms = _required_terms_for_prompt(prompt)
    output_lower = output.lower()
    word_count = len(output.split())
    has_action = any(kw in output_lower for kw in _ACTION_KEYWORDS)
    is_relevant = not intent_terms or any(t in output_lower for t in intent_terms)
    passed = word_count >= 8 and "TODO" not in output and has_action and is_relevant
    score = 8 if passed else 4
    rationale = (
        "Euristica zero-key: output sostanziale con azione presente."
        if passed
        else "Euristica zero-key: output incompleto, senza azione o fuori tema."
    )
    return JudgeScore(score=score, passed=passed, rationale=rationale)


class DeterministicJudge:
    """Rule-based judge: word-count + action-keyword + intent-match + no-TODO.

    Implements the Evaluator Protocol (async). For sync callers use `evaluate()`.
    """

    async def judge_output(self, prompt: str, output: str, rubric: str) -> JudgeScore:  # noqa: ARG002
        return evaluate(prompt, output)


def _required_terms_for_prompt(prompt: str) -> tuple[str, ...]:
    p = _norm(prompt)
    if any(
        t in p
        for t in (
            "modifica",
            "modificare",
            "aggiungere",
            "togliere",
            "ricalcolare",
            "pagare",
            "rate",
            "dilazione",
        )
    ):
        return ("modifica", "pagamento", "billing", "ordine", "ricalcolare", "totale")
    if any(t in p for t in ("fattura", "fatturazione", "billing", "addebito")):
        return ("fattura", "billing", "addebito", "rimborso")
    if any(t in p for t in ("login", "errore", "app", "down", "bloccata")):
        return ("tecnico", "login", "errore", "screenshot", "app")
    if any(t in p for t in ("reso", "restituire", "rimborso")):
        return ("reso", "restituire", "prodotto", "motivo")
    if any(t in p for t in ("spedizione", "ritardo", "tracking", "ordine")):
        return ("spedizione", "ritardo", "tracking", "ordine")
    return ()


def _norm(text: str) -> str:
    lowered = text.lower()
    for ch in ("'", "'", ".", ",", ";", ":", "-", "_"):
        lowered = lowered.replace(ch, " ")
    return " ".join(lowered.split())
