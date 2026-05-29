from llm_ops_v1.agents import router


def test_simple_ticket_routes_to_haiku_direct() -> None:
    form = router.decide_form("Where is my package? The tracking page has not updated.")

    assert form.model == router.HAIKU_MODEL
    assert form.path == "haiku_direct"
    assert form.guardrail == "standard_support_policy"
    assert form.confidence == 0.9
    assert form.uses_tools is False


def test_complex_ticket_routes_to_sonnet_with_tools() -> None:
    form = router.decide_form(
        "Enterprise customer needs a billing refund and the app outage fixed urgently."
    )

    assert form.model == router.SONNET_MODEL
    assert form.path == "sonnet_with_tools"
    assert form.guardrail == "tool_use_required"
    assert form.confidence == 0.85
    assert form.uses_tools is True


def test_ambiguous_ticket_escalates_below_confidence_threshold() -> None:
    form = router.decide_form("Help.")

    assert form.model == router.ESCALATION_MODEL
    assert form.path == "escalate"
    assert form.guardrail == "human_review"
    assert form.confidence < 0.7
    assert form.uses_tools is False


def test_same_ticket_returns_same_form() -> None:
    ticket = "I was charged twice for my monthly subscription."

    first = router.decide_form(ticket)
    second = router.decide_form(ticket)

    assert first == second


def test_demo_prints_three_different_paths(capsys) -> None:
    exit_code = router.main(["--demo"])

    lines = capsys.readouterr().out.splitlines()
    assert exit_code == 0
    assert len(lines) == 3
    assert len(set(lines)) == 3
    assert all(line.startswith("PATH: INPUT -> ") for line in lines)


def test_route_trace_formats_path() -> None:
    form = router.decide_form("Where is my package?")

    trace = router.route_trace(form)
    assert trace.startswith(f"PATH: INPUT -> {form.model} -> OUTPUT -> {form.guardrail}")
