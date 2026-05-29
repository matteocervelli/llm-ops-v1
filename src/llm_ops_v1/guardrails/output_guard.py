import re
from collections.abc import Mapping
from dataclasses import dataclass, field

DEFAULT_USD_PER_TOKEN = 0.000001

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4}(?!\w)")
_CODICE_FISCALE_RE = re.compile(
    r"\b[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]\b",
    flags=re.IGNORECASE,
)
_IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", flags=re.IGNORECASE)
_POLICY_CITATION_RE = re.compile(r"\[policy:([A-Za-z0-9_.:-]+)\]")


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reason: str
    check_name: str
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class GuardrailResponse:
    text: str
    confidence: float
    tokens: int
    budget_usd: float
    corpus: Mapping[str, str] = field(default_factory=dict)


def check_pii(text: str) -> GuardrailResult:
    for label, pattern in _pii_patterns().items():
        if pattern.search(text):
            return GuardrailResult(
                allowed=False,
                reason=f"PII detected: {label}",
                check_name="pii",
                metadata={"pii_type": label},
            )

    return GuardrailResult(allowed=True, reason="No PII detected.", check_name="pii")


def check_confidence(score: float, threshold: float = 0.7) -> GuardrailResult:
    if score < threshold:
        return GuardrailResult(
            allowed=False,
            reason=f"Confidence {score:.2f} is below threshold {threshold:.2f}.",
            check_name="confidence",
            metadata={"score": score, "threshold": threshold},
        )

    return GuardrailResult(
        allowed=True,
        reason="Confidence is within threshold.",
        check_name="confidence",
        metadata={"score": score, "threshold": threshold},
    )


def check_cost_cap(
    tokens: int,
    budget_usd: float,
    usd_per_token: float = DEFAULT_USD_PER_TOKEN,
) -> GuardrailResult:
    if tokens < 0 or budget_usd < 0 or usd_per_token < 0:
        return GuardrailResult(
            allowed=False,
            reason="Cost cap inputs cannot be negative.",
            check_name="cost_cap",
            metadata={
                "tokens": tokens,
                "budget_usd": budget_usd,
                "usd_per_token": usd_per_token,
            },
        )

    estimated_cost_usd = round(tokens * usd_per_token, 8)
    metadata = {
        "tokens": tokens,
        "budget_usd": budget_usd,
        "usd_per_token": usd_per_token,
        "estimated_cost_usd": estimated_cost_usd,
    }
    if estimated_cost_usd > budget_usd:
        return GuardrailResult(
            allowed=False,
            reason=(f"Estimated cost ${estimated_cost_usd:.6f} exceeds budget ${budget_usd:.6f}."),
            check_name="cost_cap",
            metadata=metadata,
        )

    return GuardrailResult(
        allowed=True,
        reason="Estimated cost is within budget.",
        check_name="cost_cap",
        metadata=metadata,
    )


def check_hallucination(text: str, corpus: Mapping[str, str]) -> GuardrailResult:
    cited_policy_ids = _POLICY_CITATION_RE.findall(text)
    missing_policy_ids = [policy_id for policy_id in cited_policy_ids if policy_id not in corpus]
    metadata = {
        "cited_policy_ids": cited_policy_ids,
        "missing_policy_ids": missing_policy_ids,
    }

    if missing_policy_ids:
        return GuardrailResult(
            allowed=False,
            reason="Cited policy does not exist in corpus.",
            check_name="hallucination",
            metadata=metadata,
        )

    return GuardrailResult(
        allowed=True,
        reason="All cited policies exist in corpus.",
        check_name="hallucination",
        metadata=metadata,
    )


@dataclass(frozen=True)
class OutputGuardrail:
    confidence_threshold: float = 0.7
    usd_per_token: float = DEFAULT_USD_PER_TOKEN

    def validate(self, response: GuardrailResponse) -> GuardrailResult:
        pii_result = check_pii(response.text)
        if not pii_result.allowed:
            return pii_result

        confidence_result = check_confidence(response.confidence, self.confidence_threshold)
        if not confidence_result.allowed:
            return confidence_result

        cost_result = check_cost_cap(response.tokens, response.budget_usd, self.usd_per_token)
        if not cost_result.allowed:
            return cost_result

        hallucination_result = check_hallucination(response.text, response.corpus)
        if not hallucination_result.allowed:
            return hallucination_result

        return GuardrailResult(
            allowed=True,
            reason="Output passed all guardrail checks.",
            check_name="output_guardrail",
            metadata={
                "checks": [
                    pii_result.check_name,
                    confidence_result.check_name,
                    cost_result.check_name,
                    hallucination_result.check_name,
                ]
            },
        )


def _pii_patterns() -> dict[str, re.Pattern[str]]:
    return {
        "email": _EMAIL_RE,
        "codice_fiscale": _CODICE_FISCALE_RE,
        "iban": _IBAN_RE,
        "phone": _PHONE_RE,
    }
