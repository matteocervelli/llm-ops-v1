import asyncio
import os
import time
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from llm_ops_v1.agents.base_agent import (
    SupportTriageDependencies,
    run_triage_with_usage,
)
from llm_ops_v1.agents.dispatch import DispatchResult, available_models, dispatch
from llm_ops_v1.dashboard.demo_runner import DEMO_SCENARIOS, build_live_record
from llm_ops_v1.dashboard.models import DashboardRecord
from llm_ops_v1.dashboard.store import DashboardStore
from llm_ops_v1.evals.drift import compute_drift
from llm_ops_v1.monitoring.alerts import AlertEngine, AlertThresholds

DEFAULT_STORAGE_PATH = Path(".runtime/dashboard-records.json")


@dataclass(frozen=True)
class DashboardSummary:
    run_volume: int
    avg_latency_ms: float
    total_cost_usd: float
    avg_cost_usd: float
    avg_eval_score: float
    escalation_rate: float
    cache_hit_ratio: float


@dataclass(frozen=True)
class LiveRunResult:
    output: str
    record: DashboardRecord
    steps: list[dict[str, object]]


def build_summary(records: list[DashboardRecord]) -> DashboardSummary:
    run_volume = len(records)
    if run_volume == 0:
        return DashboardSummary(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    total_cost_usd = sum(record.cost_usd for record in records)
    escalation_count = sum(1 for record in records if record.action == "escalate")
    cache_hit_count = sum(1 for record in records if record.cache_hit)
    return DashboardSummary(
        run_volume=run_volume,
        avg_latency_ms=sum(record.latency_ms for record in records) / run_volume,
        total_cost_usd=total_cost_usd,
        avg_cost_usd=total_cost_usd / run_volume,
        avg_eval_score=sum(record.eval_score for record in records) / run_volume,
        escalation_rate=escalation_count / run_volume,
        cache_hit_ratio=cache_hit_count / run_volume,
    )


def build_table_rows(records: list[DashboardRecord]) -> list[dict[str, object]]:
    return [record.table_row() for record in records]


def build_action_counts(records: list[DashboardRecord]) -> list[dict[str, object]]:
    actions = ["reply", "ask_clarification", "escalate"]
    return [
        {"action": action, "count": sum(1 for record in records if record.action == action)}
        for action in actions
    ]


def build_trend_rows(records: list[DashboardRecord]) -> list[dict[str, object]]:
    chronological_records = sorted(records, key=lambda record: record.timestamp)
    return [
        {
            "timestamp": record.timestamp.strftime("%H:%M:%S"),
            "latency_ms": round(record.latency_ms),
            "cost_usd": record.cost_usd,
        }
        for record in chronological_records
    ]


def dashboard_storage_path() -> Path:
    return Path(os.getenv("LLM_OPS_DASHBOARD_STORE", str(DEFAULT_STORAGE_PATH)))


def normalize_prompt(text: str) -> str:
    return " ".join(text.lower().split())


def infer_cache_hit(records: list[DashboardRecord], ticket_text: str) -> bool:
    normalized = normalize_prompt(ticket_text)
    return any(normalize_prompt(record.prompt_preview) == normalized for record in records)


def ensure_store() -> DashboardStore:
    if "dashboard_store" not in st.session_state:
        st.session_state["dashboard_store"] = DashboardStore.from_file(
            dashboard_storage_path(),
            [],
        )
    return st.session_state["dashboard_store"]


def reset_store() -> None:
    st.session_state["dashboard_store"] = DashboardStore.from_file(
        dashboard_storage_path(),
        [],
    )
    st.session_state["dashboard_store"].replace([])
    st.session_state.pop("latest_output", None)
    st.session_state.pop("latest_run_steps", None)


def run_live_triage(
    ticket_text: str,
    ticket_id: str,
    customer_tier: str,
    ticket_priority: str,
    policy_snippets: list[str],
    store: DashboardStore,
    source: str = "live",
    model_id: str | None = None,
) -> LiveRunResult:
    deps = _triage_deps(ticket_id, customer_tier, ticket_priority, policy_snippets)
    steps = [_step_dependencies(ticket_id, customer_tier, ticket_priority)]
    started_at = time.perf_counter()
    cache_hit = infer_cache_hit(store.snapshot(), ticket_text)

    dispatch_result: DispatchResult | None = None
    if model_id:
        _dr: DispatchResult = asyncio.run(dispatch(ticket_text, model_id))
        dispatch_result = _dr
        output = _dr.text
    else:
        _tr = asyncio.run(run_triage_with_usage(ticket_text, deps))
        output = _tr.output
        if not _tr.estimated and _tr.input_tokens > 0:
            from llm_ops_v1.economics.commercial_models import get_pricing
            from llm_ops_v1.economics.cost_calculator import estimate_token_cost

            try:
                pricing = get_pricing("anthropic:claude-sonnet-4-6")
                real_cost = estimate_token_cost(
                    pricing, _tr.input_tokens, _tr.output_tokens
                ).total_cost_usd
                dispatch_result = DispatchResult(
                    text=output,
                    model_id="anthropic:claude-sonnet-4-6",
                    input_tokens=_tr.input_tokens,
                    output_tokens=_tr.output_tokens,
                    cost_usd=real_cost,
                    estimated=False,
                )
            except (KeyError, ValueError):
                dispatch_result = None

    latency_ms = (time.perf_counter() - started_at) * 1000
    steps.append(_step_agent(latency_ms))

    if dispatch_result is not None:
        record = build_live_record(
            ticket_text,
            output,
            latency_ms,
            cache_hit=cache_hit,
            cost_usd=dispatch_result.cost_usd,
            is_estimated=False,
        )
        record.source = source
        if source == "scenario":
            record.run_id = ticket_id
    else:
        record = _build_record(ticket_text, output, latency_ms, cache_hit, source, ticket_id)

    steps.append(_step_metrics(record))
    store.append(record)
    steps.append(_step_persisted())
    return LiveRunResult(output=output, record=record, steps=steps)


def _triage_deps(
    ticket_id: str,
    customer_tier: str,
    ticket_priority: str,
    policy_snippets: list[str],
) -> SupportTriageDependencies:
    return SupportTriageDependencies(
        ticket_id=ticket_id,
        customer_tier=customer_tier,
        ticket_priority=ticket_priority,
        policy_snippets=policy_snippets,
    )


def _step_dependencies(
    ticket_id: str,
    customer_tier: str,
    ticket_priority: str,
) -> dict[str, object]:
    return {
        "fase": "1. Dipendenze",
        "cosa_succede": "Il form diventa SupportTriageDependencies.",
        "evidenza": f"ticket={ticket_id}, tier={customer_tier}, priority={ticket_priority}",
    }


def _step_agent(latency_ms: float) -> dict[str, object]:
    return {
        "fase": "2. Agente",
        "cosa_succede": "Il ticket viene passato al support triage agent.",
        "evidenza": f"latenza reale misurata: {latency_ms:.0f} ms",
    }


def _build_record(
    ticket_text: str,
    output: str,
    latency_ms: float,
    cache_hit: bool,
    source: str,
    ticket_id: str,
) -> DashboardRecord:
    record = build_live_record(ticket_text, output, latency_ms, cache_hit=cache_hit)
    record.source = source
    if source == "scenario":
        record.run_id = ticket_id
    elif source != "live":
        record.run_id = f"{source}-{ticket_id}"
    return record


def _step_metrics(record: DashboardRecord) -> dict[str, object]:
    return {
        "fase": "3. Metriche demo",
        "cosa_succede": (
            "Output, costo stimato, score e cache applicativa diventano DashboardRecord."
        ),
        "evidenza": (
            f"action={record.action}, score={record.eval_score:.1f}, "
            f"cost=${record.cost_usd:.4f}, cache_hit={record.cache_hit}"
        ),
    }


def _step_persisted() -> dict[str, object]:
    return {
        "fase": "4. Persistenza",
        "cosa_succede": "Il record viene salvato su file e resta dopo refresh/riapertura.",
        "evidenza": str(dashboard_storage_path()),
    }


def run_demo_suite(store: DashboardStore, model_id: str | None = None) -> list[LiveRunResult]:
    results = []
    for scenario in DEMO_SCENARIOS:
        results.append(
            run_live_triage(
                ticket_text=scenario.ticket_text,
                ticket_id=scenario.ticket_id,
                customer_tier=scenario.deps.customer_tier,
                ticket_priority=scenario.deps.ticket_priority,
                policy_snippets=scenario.deps.policy_snippets,
                store=store,
                source="scenario",
                model_id=model_id,
            )
        )
    return results


def _render_metric_cards(summary: DashboardSummary) -> None:
    first_row = st.columns(4)
    first_row[0].metric("Run totali", f"{summary.run_volume}")
    first_row[1].metric("Latenza media", f"{round(summary.avg_latency_ms)} ms")
    first_row[2].metric("Costo totale", f"${summary.total_cost_usd:.4f}")
    first_row[3].metric("Costo medio / run", f"${summary.avg_cost_usd:.4f}")

    second_row = st.columns(3)
    second_row[0].metric("Eval score medio", f"{summary.avg_eval_score:.1f}/10")
    second_row[1].metric("Tasso escalation", f"{summary.escalation_rate:.0%}")
    second_row[2].metric("Cache hit applicativa", f"{summary.cache_hit_ratio:.0%}")


def _split_policy_snippets(policy_text: str) -> list[str]:
    return [line.strip() for line in policy_text.splitlines() if line.strip()]


def _render_page_style() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1480px;
            padding-top: 1.5rem;
        }
        div[data-testid="stMetric"] {
            background: #111827;
            border: 1px solid #263244;
            border-radius: 8px;
            padding: 14px 16px;
        }
        div[data-testid="stMetricLabel"] p {
            color: #9ca3af;
            font-size: 0.82rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
        }
        .llmops-panel {
            border: 1px solid #263244;
            border-radius: 8px;
            padding: 16px 18px;
            background: #0f172a;
            margin-bottom: 18px;
        }
        .llmops-muted {
            color: #9ca3af;
            font-size: 0.92rem;
            margin: 0;
        }
        .llmops-title {
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_demo_explanation(records: list[DashboardRecord]) -> None:
    scenario_count = sum(1 for record in records if record.source == "scenario")
    live_count = sum(1 for record in records if record.source == "live")

    st.markdown(
        """
        <div class="llmops-panel">
            <div class="llmops-title">Dashboard operativa locale</div>
            <p class="llmops-muted">
            Qui non ci sono dati precaricati finti. Parti da storico vuoto, lanci scenari
            dal codice o ticket manuali dal form, poi studi le run salvate.
            Streamlit mostra KPI aggregati e dettaglio run; Langfuse serve dopo per trace tecniche.
            Qui cache hit significa: stesso prompt gia' visto nello store locale,
            non somiglianza generica.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    columns = st.columns(3)
    columns[0].metric("Scenari demo lanciati", scenario_count)
    columns[1].metric("Ticket manuali", live_count)
    columns[2].metric("Store locale", str(dashboard_storage_path()))


def _model_options() -> list[str]:
    """Return selector options: auto first, then live models."""
    live = available_models()
    return ["auto (decide_form)"] + live


def _resolve_model_id(selected: str) -> str | None:
    return None if selected.startswith("auto") else selected


def _render_scenario_launcher(store: DashboardStore) -> None:
    with st.container(border=True):
        st.subheader("Suite scenari")
        st.write(
            "Lancia quattro ticket diversi attraverso il codice: spedizione, billing, reso "
            "e problema tecnico enterprise. Ogni run viene valutata, stimata e salvata."
        )
        model_sel = st.selectbox(
            "Modello",
            options=_model_options(),
            key="suite_model",
            help="auto = routing cost-aware decide_form; oppure forza un modello specifico",
        )
        if st.button("Esegui suite scenari", type="primary"):
            mid = _resolve_model_id(model_sel)
            results = run_demo_suite(store, model_id=mid)
            st.session_state["latest_output"] = results[-1].output
            st.session_state["latest_run_steps"] = results[-1].steps
            st.rerun()


def _render_triage_form(store: DashboardStore) -> None:
    with st.form("support_triage_form", border=True):
        st.subheader("Ticket manuale")
        ticket_text = st.text_area(
            "Testo ticket",
            value="Il mio ordine e' in ritardo e mi serve un aggiornamento oggi.",
        )
        col_a, col_b = st.columns(2)
        ticket_id = col_a.text_input("Ticket ID", value="ticket-live-001")
        model_sel_form = col_b.selectbox(
            "Modello",
            options=_model_options(),
            help="auto = routing cost-aware",
        )
        customer_tier = st.selectbox(
            "Tier cliente",
            options=["standard", "priority", "enterprise"],
        )
        ticket_priority = st.selectbox(
            "Priorita' ticket",
            options=["low", "normal", "high", "urgent"],
            index=1,
        )
        policy_text = st.text_area(
            "Policy snippets",
            value="SLA standard: rispondere entro 4 ore ai ticket priority.",
        )
        submitted = st.form_submit_button("Esegui triage")

    if not submitted:
        return

    try:
        result = run_live_triage(
            ticket_text=ticket_text,
            ticket_id=ticket_id,
            customer_tier=customer_tier,
            ticket_priority=ticket_priority,
            policy_snippets=_split_policy_snippets(policy_text),
            store=store,
            model_id=_resolve_model_id(model_sel_form),
        )
        st.session_state["latest_output"] = result.output
        st.session_state["latest_run_steps"] = result.steps
        st.rerun()
    except Exception:
        st.error("Triage run failed. Check service logs for details.")


def _render_latest_output() -> None:
    latest_run_steps = st.session_state.get("latest_run_steps")
    if latest_run_steps:
        with st.expander("Cosa e' successo nell'ultima run", expanded=True):
            try:
                st.dataframe(latest_run_steps, hide_index=True, width="stretch")
            except TypeError:
                st.dataframe(latest_run_steps, hide_index=True, use_container_width=True)

    latest_output = st.session_state.get("latest_output")
    if latest_output:
        with st.expander("Ultimo output agente", expanded=True):
            st.write(latest_output)


def _render_recent_runs_table(records: list[DashboardRecord]) -> None:
    if not records:
        st.info("Nessuna run ancora. Usa la tab Esegui per lanciare scenari o ticket manuali.")
        return
    rows = build_table_rows(records)
    try:
        st.dataframe(rows, hide_index=True, width="stretch")
    except TypeError:
        st.dataframe(rows, hide_index=True, use_container_width=True)


def _render_run_detail(records: list[DashboardRecord]) -> None:
    if not records:
        st.info("Nessuna run ancora. Esegui la suite scenari o lancia un ticket manuale.")
        return

    options = [record.run_id for record in records]
    selected_run_id = st.selectbox("Apri run", options=options)
    selected = next(record for record in records if record.run_id == selected_run_id)

    with st.container(border=True):
        st.subheader(f"Dettaglio {selected.run_id}")
        first_row = st.columns(3)
        first_row[0].metric("Source", selected.source)
        first_row[1].metric("Action", selected.action)
        first_row[2].metric("Cache hit", "si" if selected.cache_hit else "no")
        second_row = st.columns(3)
        cost_label = "Costo (stima)" if selected.estimated else "Costo"
        second_row[0].metric("Latenza", f"{round(selected.latency_ms)} ms")
        second_row[1].metric(cost_label, f"${selected.cost_usd:.4f}")
        second_row[2].metric("Score", f"{selected.eval_score:.1f}/10")
        st.text_area("Prompt", selected.prompt_preview, height=100, disabled=True)
        st.subheader("Output agente")
        with st.container(border=True):
            st.markdown(selected.output_preview)


def _render_analysis_tab(records: list[DashboardRecord]) -> None:
    left_column, right_column = st.columns(2)
    with left_column:
        st.subheader("Distribuzione azioni")
        if records:
            st.bar_chart(build_action_counts(records), x="action", y="count")
        else:
            st.caption("La distribuzione azioni comparira' dopo la prima run.")
    with right_column:
        st.subheader("Trend latenza / costo")
        if records:
            st.line_chart(
                build_trend_rows(records),
                x="timestamp",
                y=["latency_ms", "cost_usd"],
            )
        else:
            st.caption("Il trend comparira' dopo la prima run.")


def _render_drift_tab(records: list[DashboardRecord]) -> None:
    st.subheader("Drift & Alert")
    if len(records) < 10:
        st.info("Servono almeno 10 run per calcolare il drift. Esegui prima la suite scenari.")
        return

    half = len(records) // 2
    baseline = records[half:]  # older half
    current = records[:half]  # newer half

    report = compute_drift(baseline, current)
    engine = AlertEngine(AlertThresholds())
    alerts = engine.evaluate(records, report)

    left, right = st.columns(2)
    with left:
        st.metric(
            "PSI lunghezza prompt",
            f"{report.psi_prompt_length.psi:.4f}",
            delta=None,
            help="< 0.1 stabile | 0.1–0.2 attenzione | ≥ 0.2 drift",
        )
        st.metric(
            "PSI distribuzione azioni",
            f"{report.psi_action.psi:.4f}",
            help="Misura quanto è cambiato il mix reply/escalate/ask_clarification",
        )
    with right:
        st.metric(
            "Score medio baseline",
            f"{report.score_drift.baseline_avg:.2f}",
        )
        st.metric(
            "Score medio corrente",
            f"{report.score_drift.current_avg:.2f}",
            delta=f"{report.score_drift.delta:+.2f}",
            delta_color="inverse",
        )

    if alerts:
        st.warning(f"⚠ {len(alerts)} alert attivi")
        for alert in alerts:
            st.write(
                f"**[{alert.level}]** `{alert.metric}` = "
                f"{alert.value:.4f} (soglia {alert.threshold})"
            )
    else:
        st.success("Nessun alert attivo — distribuzione stabile.")


_LOAD_TICKETS = [
    "Il mio pacco non è ancora arrivato, il tracking non si aggiorna da 3 giorni.",
    "Ho ricevuto un addebito doppio in fattura questo mese.",
    "L'app si blocca ogni volta che provo ad accedere alla sezione pagamenti.",
    "Voglio disdire il mio abbonamento annuale e avere il rimborso pro-rata.",
    "Non riesco a fare il login dopo l'aggiornamento di ieri.",
    "Enterprise: sistema di autenticazione SSO non funzionante per tutta l'azienda.",
    "Dove posso trovare la ricevuta fiscale del mio ultimo acquisto?",
    "Il rimborso che mi era stato promesso 10 giorni fa non è ancora arrivato.",
    "Vorrei aggiornare l'indirizzo di spedizione per un ordine ancora in lavorazione.",
    "La notifica di spedizione dice consegnato ma non ho ricevuto nulla.",
    "Ho bisogno di una fattura con i dati della mia azienda, non i miei dati personali.",
    "L'assistente virtuale mi ha dato informazioni sbagliate sul mio ordine.",
    "Voglio fare un reso ma il link nella mail non funziona.",
    "Account bloccato dopo troppi tentativi di accesso. Come sblocco?",
    "Offerta applicata nel carrello ma non in fattura finale.",
    "Il prodotto ricevuto è diverso da quello ordinato.",
    "Non riesco a scaricare le istruzioni dal mio account.",
    "Sito non disponibile da stamattina — stiamo perdendo lavoro.",
    "Codice promozionale non accettato al checkout.",
    "Help.",
]


def _render_load_test_tab(store: DashboardStore) -> None:
    st.subheader("Load test — esecuzione parallela")
    st.write(
        "Invia N ticket in parallelo usando `ThreadPoolExecutor`. "
        "Ogni ticket viene triaggiato, valutato e salvato nel dashboard."
    )

    col1, col2 = st.columns(2)
    n_tickets = col1.slider("Numero ticket", min_value=4, max_value=20, value=8, step=4)
    model_sel = col2.selectbox(
        "Modello",
        options=_model_options(),
        key="load_model",
        help="auto = decide_form per ogni ticket",
    )

    if not st.button("Lancia load test", type="primary"):
        return

    import concurrent.futures

    mid = _resolve_model_id(model_sel)
    tickets = _LOAD_TICKETS[:n_tickets]
    results_placeholder = st.empty()
    progress = st.progress(0)
    rows: list[dict[str, object]] = []

    def _run_one(ticket: str, idx: int) -> dict[str, object]:
        try:
            res = run_live_triage(
                ticket_text=ticket,
                ticket_id=f"load-{idx:02d}",
                customer_tier="standard",
                ticket_priority="normal",
                policy_snippets=[],
                store=store,
                source="load",
                model_id=mid,
            )
            return {
                "#": idx + 1,
                "ticket": ticket[:50],
                "action": res.record.action,
                "score": res.record.eval_score,
                "latenza ms": round(res.record.latency_ms),
                "costo": f"${res.record.cost_usd:.5f}",
                "stima": "stima" if res.record.estimated else "reale",
                "output": res.output[:120],
            }
        except Exception:
            return {
                "#": idx + 1,
                "ticket": ticket[:50],
                "action": "ERROR",
                "score": 0,
                "output": "Run failed.",
            }

    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(n_tickets, 8)) as pool:
        futures = {pool.submit(_run_one, t, i): i for i, t in enumerate(tickets)}
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result())
            completed += 1
            progress.progress(completed / n_tickets)
            results_placeholder.dataframe(
                sorted(rows, key=lambda r: r["#"]),  # type: ignore[arg-type]
                hide_index=True,
                use_container_width=True,
            )

    progress.empty()
    st.success(f"Load test completato — {completed} ticket processati.")


def _render_tabs(store: DashboardStore, records: list[DashboardRecord]) -> None:
    execute_tab, runs_tab, detail_tab, analysis_tab, drift_tab, load_tab, debug_tab = st.tabs(
        ["Esegui", "Run", "Dettaglio", "Analisi", "Drift & Alert", "Load Test", "Debug"]
    )
    with execute_tab:
        _render_scenario_launcher(store)
        _render_triage_form(store)
    with runs_tab:
        st.subheader("Run recenti")
        _render_recent_runs_table(records)
    with detail_tab:
        _render_run_detail(records)
    with analysis_tab:
        _render_analysis_tab(records)
    with drift_tab:
        _render_drift_tab(records)
    with load_tab:
        _render_load_test_tab(store)
    with debug_tab:
        _render_latest_output()


def main() -> None:
    st.set_page_config(page_title="LLM Ops Dashboard", layout="wide")
    _render_page_style()
    st.title("LLM Ops Dashboard")
    st.caption("Support triage operations - storico demo persistente, run live, KPI operativi")

    store = ensure_store()
    if st.button("Svuota storico"):
        reset_store()
        store = ensure_store()

    records = store.snapshot()
    _render_demo_explanation(records)
    _render_metric_cards(build_summary(records))
    _render_tabs(store, records)


if __name__ == "__main__":
    main()
