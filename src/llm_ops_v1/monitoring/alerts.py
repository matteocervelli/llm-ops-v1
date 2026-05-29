"""KPI threshold alerts — evaluates DashboardStore metrics against configured thresholds.

Emits structured WARN/CRITICAL log lines; optionally POSTs to a webhook URL.
This is intentionally simple: no Prometheus, no time-series DB.
The upgrade path to full metrics is documented in docs/04-monitoring-dashboard.md.
"""

from __future__ import annotations

import ipaddress
import logging
import os
import socket
import urllib.parse
from dataclasses import dataclass, field

from llm_ops_v1.dashboard.models import DashboardRecord
from llm_ops_v1.evals.drift import DriftReport

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AlertThresholds:
    max_p95_latency_ms: float = 5000.0
    max_avg_cost_usd: float = 0.01
    min_avg_score: float = 5.0
    max_psi: float = 0.2
    max_escalation_rate: float = 0.5


@dataclass(frozen=True)
class Alert:
    level: str  # WARN | CRITICAL
    metric: str
    value: float
    threshold: float
    message: str


@dataclass
class AlertEngine:
    thresholds: AlertThresholds = field(default_factory=AlertThresholds)
    webhook_url: str | None = field(default_factory=lambda: os.getenv("LLM_OPS_ALERT_WEBHOOK"))

    def evaluate(
        self,
        records: list[DashboardRecord],
        drift: DriftReport | None = None,
    ) -> list[Alert]:
        alerts: list[Alert] = []
        if not records:
            return alerts

        latencies = sorted(r.latency_ms for r in records)
        p95 = latencies[int(len(latencies) * 0.95)]
        avg_cost = sum(r.cost_usd for r in records) / len(records)
        avg_score = sum(r.eval_score for r in records) / len(records)
        escalations = sum(1 for r in records if r.action == "escalate")
        escalation_rate = escalations / len(records)

        t = self.thresholds
        checks = [
            ("p95_latency_ms", p95, t.max_p95_latency_ms, "WARN", "p95 latency above threshold"),
            ("avg_cost_usd", avg_cost, t.max_avg_cost_usd, "WARN", "average cost above threshold"),
            ("avg_score", avg_score, t.min_avg_score, "WARN", "average eval score below threshold"),
            (
                "escalation_rate",
                escalation_rate,
                t.max_escalation_rate,
                "WARN",
                "escalation rate above threshold",
            ),
        ]
        for metric, value, threshold, level, msg in checks:
            exceeded = value > threshold if metric != "avg_score" else value < threshold
            if exceeded:
                alert = Alert(
                    level=level,
                    metric=metric,
                    value=round(value, 4),
                    threshold=threshold,
                    message=msg,
                )
                alerts.append(alert)
                logger.warning(
                    "[%s] %s: value=%.4f threshold=%.4f", level, metric, value, threshold
                )

        if drift and drift.any_drift:
            for psi_result in (drift.psi_prompt_length, drift.psi_action):
                if psi_result.drift:
                    alert = Alert(
                        level="CRITICAL",
                        metric=f"psi_{psi_result.feature}",
                        value=psi_result.psi,
                        threshold=t.max_psi,
                        message=f"PSI drift detected on {psi_result.feature}",
                    )
                    alerts.append(alert)
                    logger.error(
                        "[CRITICAL] PSI drift: %s=%.4f", psi_result.feature, psi_result.psi
                    )

        if alerts and self.webhook_url:
            self._post_alerts(alerts)

        return alerts

    def _post_alerts(self, alerts: list[Alert]) -> None:
        import json
        import urllib.request

        if not _is_allowed_webhook_url(self.webhook_url):
            logger.warning("Alert webhook skipped: URL is not allowed.")
            return

        payload = json.dumps([a.__dict__ for a in alerts]).encode()
        try:
            req = urllib.request.Request(
                self.webhook_url or "",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as response:  # nosec B310
                response.read(1)
        except Exception:
            logger.warning("Alert webhook failed.")


def _is_allowed_webhook_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    try:
        port = parsed.port or 443
    except ValueError:
        return False
    try:
        addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
    except OSError:
        return False
    for result in addresses:
        sockaddr = result[4]
        if not sockaddr or not isinstance(sockaddr[0], str):
            return False
        if not _is_public_ip(sockaddr[0]):
            return False
    return True


def _is_public_ip(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    blocked = (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )
    return not blocked
