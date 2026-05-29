# Default rubric strings for ClaudeJudge.
# A rubric tells the judge what "good" looks like for a specific scenario.
# Keep these concise — the judge LLM reads the full rubric on every call.

SUPPORT_TRIAGE_RUBRIC = (
    "The response must: (1) identify the issue category (billing/shipping/technical/account), "
    "(2) propose a concrete action (reply, escalate, or ask_clarification), "
    "(3) reference any relevant policy if provided, "
    "(4) be written in a professional tone appropriate for customer support. "
    "Score low if the action is missing, vague, or contradicts the stated policy."
)

ESCALATION_RUBRIC = (
    "The response must recognise the ambiguity and ask one focused clarifying question. "
    "Score low if it attempts to resolve without enough information or asks multiple questions."
)
