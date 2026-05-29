from llm_ops_v1.guardrails import (
    GuardrailResponse,
    OutputGuardrail,
    check_confidence,
    check_cost_cap,
    check_hallucination,
    check_pii,
)


def test_check_pii_allows_safe_text() -> None:
    result = check_pii("Your order is delayed. We will update tracking within 2 hours.")

    assert result.allowed is True
    assert result.check_name == "pii"


def test_check_pii_blocks_email_phone_codice_fiscale_and_iban() -> None:
    samples = [
        ("Contact another customer at mario.rossi@example.com.", "email"),
        ("Call another customer at +39 345 123 4567.", "phone"),
        ("Customer codice fiscale RSSMRA85M01H501Z appears in the reply.", "codice_fiscale"),
        ("Refund should go to IT60X0542811101000000123456.", "iban"),
    ]

    for sample, pii_type in samples:
        result = check_pii(sample)

        assert result.allowed is False
        assert result.check_name == "pii"
        assert result.metadata["pii_type"] == pii_type
        assert "PII" in result.reason


def test_check_confidence_blocks_scores_below_threshold() -> None:
    result = check_confidence(0.69)

    assert result.allowed is False
    assert result.check_name == "confidence"
    assert "below" in result.reason


def test_check_confidence_allows_scores_at_threshold() -> None:
    result = check_confidence(0.7)

    assert result.allowed is True


def test_check_cost_cap_blocks_estimated_spend_over_budget() -> None:
    result = check_cost_cap(tokens=1_000, budget_usd=0.0005, usd_per_token=0.000001)

    assert result.allowed is False
    assert result.check_name == "cost_cap"
    assert result.metadata["estimated_cost_usd"] == 0.001


def test_check_cost_cap_allows_estimated_spend_within_budget() -> None:
    result = check_cost_cap(tokens=1_000, budget_usd=0.002, usd_per_token=0.000001)

    assert result.allowed is True


def test_check_cost_cap_blocks_negative_inputs() -> None:
    result = check_cost_cap(tokens=-1, budget_usd=0.002)

    assert result.allowed is False
    assert result.check_name == "cost_cap"
    assert "negative" in result.reason


def test_check_hallucination_requires_cited_policy_ids_in_corpus() -> None:
    corpus = {"SLA-4H": "Standard SLA: respond within 4 hours."}

    result = check_hallucination("We follow [policy:SLA-24H].", corpus)

    assert result.allowed is False
    assert result.check_name == "hallucination"
    assert result.metadata["missing_policy_ids"] == ["SLA-24H"]


def test_check_hallucination_allows_existing_policy_ids() -> None:
    corpus = {"SLA-4H": "Standard SLA: respond within 4 hours."}

    result = check_hallucination("We follow [policy:SLA-4H].", corpus)

    assert result.allowed is True


def test_output_guardrail_validate_runs_checks_in_order_and_stops_at_first_failure() -> None:
    response = GuardrailResponse(
        text="Contact another customer at +39 345 123 4567. We follow [policy:SLA-24H].",
        confidence=0.2,
        tokens=100_000,
        budget_usd=0.0001,
        corpus={},
    )

    result = OutputGuardrail().validate(response)

    assert result.allowed is False
    assert result.check_name == "pii"


def test_output_guardrail_validate_allows_clean_response() -> None:
    response = GuardrailResponse(
        text="We will update tracking within 2 hours under [policy:SLA-4H].",
        confidence=0.9,
        tokens=200,
        budget_usd=0.01,
        corpus={"SLA-4H": "Standard SLA: respond within 4 hours."},
    )

    result = OutputGuardrail().validate(response)

    assert result.allowed is True
    assert result.check_name == "output_guardrail"
