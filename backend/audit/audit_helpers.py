"""
audit_helpers.py
─────────────────
Helper functions for emitting AuditEvent SSE events and accumulating
the audit trail in the in-memory run registry.

HOW TO INTEGRATE
────────────────
Call publish_audit_event() inside each LangGraph node (or the
orchestrator_live.py handlers) at the point where a meaningful
decision step completes.

The function does two things in parallel:
  1. Publishes an AuditEvent to Redis so the SSE stream delivers it
     to the browser in real time → AuditTab shows a live-updating timeline
  2. Appends a plain dict to orchestrator._runs[run_id]["audit_trail"]
     so GET /api/runs/{run_id}/audit-trail can serve it later without
     reading Redis

EXAMPLE CALL SITES
──────────────────
In graph/logistics_agent_graph.py, after the agent produces its route options:

    from audit.audit_helpers import publish_audit_event

    await publish_audit_event(
        run_id      = run_id,
        started_at  = state["started_at"],
        agent_color = "#00d4ff",
        agent_label = "🔵 Logistics Agent",
        step_name   = "Route Options",
        description = f"3 freight options evaluated. Hybrid 60/40 costs ${hybrid_k}K over 36h.",
        data        = "check_freight_rates() · memory_recall('LA_strike_2024')",
        memory_note = memory_text,   # or None
    )

In graph/finance_agent_graph.py, after Monte Carlo:

    await publish_audit_event(
        run_id, started_at,
        agent_color = "#00e676",
        agent_label = "🟢 Finance Agent",
        step_name   = "Monte Carlo",
        description = f"100 iterations. Mean ${mean_k}K · P10 ${p10_k}K · P90 ${p90_k}K · CI {ci_pct}%.",
        data        = "run_monte_carlo(100) · query_customs_rates()",
    )

In graph/orchestrator_graph.py, _awaiting_approval node:

    await publish_audit_event(
        run_id, started_at,
        agent_color = "#00e676",
        agent_label = "✅ VP Operations",
        step_name   = "Approved & Executed",
        description = f"Hybrid route approved. Cost ${cost_k}K · Savings ${saved_k}K · CI {ci_pct}%.",
        data        = f"option: hybrid · cost: ${cost_k}K · savings: ${saved_k}K · CI: {ci_pct}%",
    )
"""

from __future__ import annotations

import logging
import math
import time as _time

import db.redis_client as redis_client
import api.orchestrator as orchestrator

log = logging.getLogger("resolveiq.audit")


def _elapsed_label(started_at: float) -> str:
    """Return 'MM:SS' string for elapsed seconds since started_at."""
    elapsed = int(_time.time() - started_at)
    m = elapsed // 60
    s = elapsed % 60
    return f"{m:02d}:{s:02d}"


async def publish_audit_event(
    run_id:      str,
    started_at:  float,
    agent_color: str,
    agent_label: str,
    step_name:   str,
    description: str,
    data:        str  = "",
    memory_note: str | None = None,
) -> None:
    """
    Emit one AuditEvent SSE message AND persist it to the in-memory run registry.

    Args:
        run_id       : Active run identifier
        started_at   : Unix timestamp when the run began (from LangGraph state)
        agent_color  : Hex colour for this agent's dot / label
        agent_label  : Display name, e.g. "🔵 Logistics Agent"
        step_name    : Short phase name, e.g. "Route Options"
        description  : One-sentence summary of what the agent decided
        data         : Raw tool calls / key-value facts (monospace in UI)
        memory_note  : Optional episodic memory recall note (shown as a badge)
    """
    elapsed_s = int(_time.time() - started_at)
    time_label = f"{_elapsed_label(started_at)} — {step_name}"

    event_dict = {
        "type":        "audit",
        "time_label":  time_label,
        "agent_color": agent_color,
        "agent_label": agent_label,
        "description": description,
        "data":        data,
        "memory_note": memory_note,
        "elapsed_s":   elapsed_s,
    }

    # 1. Publish to Redis → SSE stream → browser AuditTab (real-time)
    try:
        await redis_client.publish(run_id, event_dict)
    except Exception as exc:
        log.warning("publish_audit_event: Redis publish failed: %s", exc)

    # 2. Persist in in-memory registry → GET /api/runs/{run_id}/audit-trail
    try:
        run = orchestrator.get_run(run_id)
        if run is not None:
            if "audit_trail" not in run:
                run["audit_trail"] = []
            run["audit_trail"].append({
                "time_label":  time_label,
                "agent_color": agent_color,
                "agent_label": agent_label,
                "description": description,
                "data":        data,
                "memory_note": memory_note,
                "elapsed_s":   elapsed_s,
            })
    except Exception as exc:
        log.warning("publish_audit_event: in-memory persist failed: %s", exc)
