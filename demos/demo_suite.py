"""Demo suite — run the 4 triage scenarios from the command line."""

import asyncio
import sys

sys.path.insert(0, "src")

from llm_ops_v1.agents.base_agent import SupportTriageDependencies, run_triage_with_usage
from llm_ops_v1.dashboard.demo_runner import DEMO_SCENARIOS


async def main() -> None:
    for s in DEMO_SCENARIOS:
        deps = SupportTriageDependencies(
            ticket_id=s.ticket_id,
            customer_tier=s.deps.customer_tier,
            ticket_priority=s.deps.ticket_priority,
            policy_snippets=s.deps.policy_snippets,
        )
        r = await run_triage_with_usage(s.ticket_text, deps)
        est = "(stima)" if r.estimated else f"in={r.input_tokens} out={r.output_tokens}"
        print(f"  [{s.ticket_id}] {est}")
        print(f"  {r.output[:100]}")
        print()


asyncio.run(main())
