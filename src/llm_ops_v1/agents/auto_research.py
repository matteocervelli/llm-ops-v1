from collections.abc import Callable
from dataclasses import dataclass, field

SearchFn = Callable[[str], list[str]]
SummarizeFn = Callable[[str, list[str]], str]


@dataclass
class ResearchIteration:
    gap: str
    queries: list[str]
    findings: list[str]
    summary: str


@dataclass
class AutoResearchAgent:
    search_fn: SearchFn
    summarize_fn: SummarizeFn
    history: list[ResearchIteration] = field(default_factory=list)

    def run_cycle(self, gap: str) -> ResearchIteration:
        queries = [
            f"{gap} production patterns",
            f"{gap} failure modes",
            f"{gap} benchmarking checklist",
        ]
        findings = [item for query in queries for item in self.search_fn(query)]
        summary = self.summarize_fn(gap, findings)
        iteration = ResearchIteration(gap=gap, queries=queries, findings=findings, summary=summary)
        self.history.append(iteration)
        return iteration
