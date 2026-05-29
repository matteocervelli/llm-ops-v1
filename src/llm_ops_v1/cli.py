import argparse
import asyncio
import sys

from llm_ops_v1.agents.base_agent import SupportTriageDependencies, run_support_triage_agent
from llm_ops_v1.agents.triage_contracts import (
    TriageSummary,
    estimate_triage_cost,
    parse_triage_output,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llm-ops")
    subparsers = parser.add_subparsers(dest="command", required=True)

    triage = subparsers.add_parser("triage", help="Run the support triage scenario.")
    triage.add_argument("ticket_text")
    triage.add_argument("--ticket-id", default="ticket-cli-001")
    triage.add_argument("--customer-tier", default="standard")
    triage.add_argument("--ticket-priority", default="normal")
    triage.add_argument("--policy", action="append", default=[])
    triage.set_defaults(handler=run_triage_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


def run_triage_command(args: argparse.Namespace) -> int:
    try:
        output = asyncio.run(
            run_triage(
                ticket_text=args.ticket_text,
                ticket_id=args.ticket_id,
                customer_tier=args.customer_tier,
                ticket_priority=args.ticket_priority,
                policy_snippets=args.policy,
            )
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(output)
    return 0


async def run_triage(
    ticket_text: str,
    ticket_id: str,
    customer_tier: str,
    ticket_priority: str,
    policy_snippets: list[str],
) -> str:
    deps = SupportTriageDependencies(
        ticket_id=ticket_id,
        customer_tier=customer_tier,
        ticket_priority=ticket_priority,
        policy_snippets=policy_snippets,
    )
    output = await run_support_triage_agent(ticket_text, deps)
    summary = parse_triage_output(output)
    estimated_cost_usd = estimate_triage_cost(ticket_text, output, policy_snippets)
    return format_triage_summary(summary, estimated_cost_usd)


def format_triage_summary(summary: TriageSummary, estimated_cost_usd: float) -> str:
    return "\n".join(
        [
            f"Category: {summary.category}",
            f"Reply draft: {summary.reply_draft}",
            f"Decision: {summary.decision}",
            f"Estimated cost: ${estimated_cost_usd:.4f}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
