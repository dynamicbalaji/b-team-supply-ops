"""
routes_decision_audit.py
────────────────────────
New FastAPI route handlers for the Decision Matrix and Audit Trail pages.

HOW TO INTEGRATE
────────────────
1.  In main.py, import and include this router:

        from routes_decision_audit import router as decision_audit_router
        app.include_router(decision_audit_router, prefix="/api")

2.  In models.py, add AuditEvent (see models_additions.py).

3.  In agents/orchestrator_live.py  AND  graph/orchestrator_graph.py,
    call publish_audit_event() after each significant agent step.
    See audit_helpers.py for the helper and example call sites.

New endpoints
─────────────
GET /api/runs/{run_id}/decision-matrix
    Returns the live decision matrix options derived from run_context:
    - logistics freight options (air / sea / hybrid) with cost, time, risk, ESG
    - finance Monte Carlo stats (mean, p10, p90, CI, histogram distribution)
    - the recommended option from the approval event

GET /api/runs/{run_id}/audit-trail
    Returns the ordered list of audit events accumulated during the run.
    Falls back to a scenario-appropriate generated summary when the run
    used the hardcoded replay path (no live agents).

Both endpoints:
    - Try Redis (fast, live) → in-memory _runs dict → TursoDB (persistent)
    - Return a stable shape the frontend can consume immediately
    - Never raise 500; degrade gracefully to empty / default values
"""

from __future__ import annotations

import io
import math
import time as _time
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

import db.redis_client as redis_client
import api.orchestrator as orchestrator
from core.models import ScenarioType
from core.scenarios import SCENARIO_DEFINITIONS
from audit.audit_pdf import generate_audit_pdf

log = logging.getLogger("resolveiq.routes.decision_audit")

router = APIRouter(tags=["Decision & Audit"])


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _risk_score_from_level(level: str) -> int:
    """Map 'low'/'medium'/'high' → numeric score used by the frontend riskBar."""
    return {"low": 2, "medium": 5, "high": 8}.get(str(level).lower(), 5)


def _esg_from_risk(score: int) -> str:
    if score <= 3:
        return "low"
    if score <= 6:
        return "medium"
    return "high"


def _format_cost(cost_usd: int) -> str:
    if cost_usd >= 1_000_000:
        return f"${cost_usd / 1_000_000:.1f}M"
    if cost_usd >= 1_000:
        return f"${cost_usd // 1_000}K"
    return f"${cost_usd}"


def _customer_impact(option_key: str, scenario: str) -> str:
    """Return the customer-facing impact string for a given option."""
    IMPACTS: dict[str, dict[str, str]] = {
        "port_strike": {
            "air":    "None",
            "sea":    "20% short",
            "hybrid": "Minor",
        },
        "customs_delay": {
            "air":    "None",
            "sea":    "72h delay",
            "hybrid": "Minor",
        },
        "supplier_breach": {
            "air":    "None",
            "sea":    "Production halt",
            "hybrid": "Minor delay",
        },
    }
    key = "hybrid" if "hybrid" in option_key.lower() else (
        "sea" if "sea" in option_key.lower() or "direct" in option_key.lower() else "air"
    )
    return IMPACTS.get(scenario, {}).get(key, "—")


def _build_options_from_context(run_context: dict, scenario_str: str) -> list[dict]:
    """
    Derive the 3-option decision matrix rows from live run_context.

    Falls back to freight catalog defaults when context is incomplete
    (e.g. early in the run, before all agents have written their outputs).
    """
    from tools.freight import _FREIGHT_CATALOG, check_freight_rates
    from core.models import ScenarioType

    try:
        sc_type = ScenarioType(scenario_str)
    except ValueError:
        sc_type = ScenarioType.PORT_STRIKE

    # Pull live freight rates out of run_context["logistics"] when available
    logistics = run_context.get("logistics", {})
    finance   = run_context.get("finance", {})

    # Live freight options written by the logistics agent subgraph
    live_options_raw: list[dict] = logistics.get("freight_options", [])

    # Fall back to the static catalog when agent hasn't run yet
    catalog = _FREIGHT_CATALOG.get(sc_type, {})

    rows: list[dict] = []

    if live_options_raw:
        # Agent-populated path — transform to display shape
        recommended_option = finance.get("recommended_option", "hybrid")
        for opt in live_options_raw:
            risk_score = _risk_score_from_level(opt.get("risk_level", "medium"))
            key_hint   = str(opt.get("option_key", opt.get("carrier", ""))).lower()
            rows.append({
                "name":            opt.get("label", opt.get("carrier", "Option")),
                "option_key":      key_hint,
                "cost":            opt.get("cost_usd", opt.get("base_cost_usd", 0)),
                "time":            f"{opt.get('transit_hours', '?')}h",
                "risk":            risk_score,
                "esg":             _esg_from_risk(risk_score),
                "customer":        _customer_impact(key_hint, scenario_str),
                "recommended":     recommended_option.lower() in key_hint,
            })
    else:
        # Static catalog fallback — still better than hardcoded JSX
        option_order = list(catalog.keys())
        for i, (key, item) in enumerate(catalog.items()):
            risk_score = _risk_score_from_level(item.get("risk_level", "medium"))
            rows.append({
                "name":       item.get("carrier", key),
                "option_key": key,
                "cost":       item.get("base_cost_usd", 0),
                "time":       f"{item.get('transit_hours', 36)}h",
                "risk":       risk_score,
                "esg":        _esg_from_risk(risk_score),
                "customer":   _customer_impact(key, scenario_str),
                "recommended": "hybrid" in key.lower(),
            })

    return rows


def _build_mc_stats(run_context: dict) -> dict:
    """Extract Monte Carlo stats from finance agent output."""
    mc = run_context.get("finance", {}).get("mc_result", {})
    if not mc:
        # Sensible defaults while agents are still running
        return {
            "mean": 280_000, "p10": 241_000, "p90": 318_000,
            "ci": 0.94, "distribution": [],
        }
    return {
        "mean":         mc.get("mean_usd",            280_000),
        "p10":          mc.get("p10_usd",             241_000),
        "p90":          mc.get("p90_usd",             318_000),
        "ci":           mc.get("confidence_interval", 0.94),
        "distribution": mc.get("distribution",        []),
        "saved_vs_air": mc.get("saved_vs_air_usd",    220_000),
    }


# ─────────────────────────────────────────────────────────────────────────
# Hardcoded-mode audit event generator
# ─────────────────────────────────────────────────────────────────────────

_HARDCODED_AUDIT_BY_SCENARIO: dict[str, list[dict]] = {
    "port_strike": [
        {
            "time_label": "00:00 — Crisis Detected",
            "agent_color": "#ff3b5c",
            "agent_label": "🔴 System Monitor",
            "description": "Strike detected. SC-2024-8891 BLOCKED at Long Beach. P0 broadcast to all agents.",
            "data": "penalty_risk: $2M · deadline: 48h · contract: Apple",
            "memory_note": None,
        },
        {
            "time_label": "00:12 — Route Options",
            "agent_color": "#00d4ff",
            "agent_label": "🔵 Logistics Agent",
            "description": "3 options generated. Memory recalled March 2024 LA port strike — hybrid saved $180K.",
            "data": "check_freight_rates() · memory_recall('LA_strike_2024')",
            "memory_note": "📚 Historical: LA Strike Mar 2024 — hybrid saved $180K",
        },
        {
            "time_label": "01:04 — Monte Carlo",
            "agent_color": "#00e676",
            "agent_label": "🟢 Finance Agent",
            "description": "100-iteration simulation run. Challenged customs assumption — Air revised $450K → $500K.",
            "data": "run_monte_carlo(100) · query_customs_rates()",
            "memory_note": None,
        },
        {
            "time_label": "02:18 — SLA Confirmed",
            "agent_color": "#9b5de5",
            "agent_label": "🟣 Sales Agent",
            "description": "Apple 36h extension negotiated. Reputational risk only — zero financial penalty.",
            "data": "query_contract_terms() · draft_sla_amendment()",
            "memory_note": None,
        },
        {
            "time_label": "03:45 — Risk Flagged",
            "agent_color": "#ff3b5c",
            "agent_label": "🔴 Risk Agent (Devil's Advocate)",
            "description": "LAX ground crew unconfirmed during strike. Single point of failure. Hour-20 backup trigger added. Finance +$20K reserve.",
            "data": "risk: operational · severity: medium · mitigation: tucson_backup_H20",
            "memory_note": None,
        },
        {
            "time_label": "04:32 — Approved & Executed",
            "agent_color": "#00e676",
            "agent_label": "✅ VP Operations",
            "description": "Hybrid route approved. Cascade: freight booked, Apple notified, budget released, spot order cancelled.",
            "data": "option: hybrid · cost: $280K · savings: $220K · CI: 94%",
            "memory_note": None,
        },
    ],
    "customs_delay": [
        {
            "time_label": "00:00 — Crisis Detected",
            "agent_color": "#ff3b5c",
            "agent_label": "🔴 System Monitor",
            "description": "Regulatory hold detected. SC-2024-4423 BLOCKED at Shenzhen customs. P0 broadcast.",
            "data": "penalty_risk: $1.5M · deadline: 36h · contract: Samsung",
            "memory_note": None,
        },
        {
            "time_label": "00:09 — Route Options",
            "agent_color": "#00d4ff",
            "agent_label": "🔵 Logistics Agent",
            "description": "3 alternatives found. Memory recalled Shanghai SAMR hold Sep 2023 — Busan reroute saved $145K.",
            "data": "check_freight_rates() · memory_recall('Shanghai_customs_2023')",
            "memory_note": "📚 Historical: Shanghai SAMR Hold Sep 2023 — Busan reroute saved $145K",
        },
        {
            "time_label": "00:58 — Monte Carlo",
            "agent_color": "#00e676",
            "agent_label": "🟢 Finance Agent",
            "description": "100-iteration simulation. ATA carnet pre-clearance confirmed as viable — adds 6h, saves 40h processing.",
            "data": "run_monte_carlo(100) · query_customs_rates(ATA_carnet)",
            "memory_note": None,
        },
        {
            "time_label": "02:05 — Force Majeure",
            "agent_color": "#9b5de5",
            "agent_label": "🟣 Sales Agent",
            "description": "Force majeure clause invoked. Samsung waiving $1.5M penalty. ETA update requested by EOD.",
            "data": "query_contract_terms() · draft_sla_amendment(force_majeure)",
            "memory_note": None,
        },
        {
            "time_label": "03:12 — Risk Flagged",
            "agent_color": "#ff3b5c",
            "agent_label": "🔴 Risk Agent (Devil's Advocate)",
            "description": "Busan ATA carnet single point of failure. If carnet rejected, 48h secondary delay. Recommend dual-channel submission.",
            "data": "risk: regulatory · severity: medium · mitigation: dual_carnet_submission",
            "memory_note": None,
        },
        {
            "time_label": "04:01 — Approved & Executed",
            "agent_color": "#00e676",
            "agent_label": "✅ VP Operations",
            "description": "Hybrid Busan route approved. ATA carnet filed, Samsung notified, sea leg rerouted.",
            "data": "option: hybrid · cost: $200K · savings: $145K · CI: 89%",
            "memory_note": None,
        },
    ],
    "supplier_breach": [
        {
            "time_label": "00:00 — Crisis Detected",
            "agent_color": "#ff3b5c",
            "agent_label": "🔴 System Monitor",
            "description": "Supplier bankruptcy filed. SC-2024-7701 — Taiwan fab halted. $20M order at risk. P0 broadcast.",
            "data": "penalty_risk: $5M · deadline: 72h · contract: NVIDIA",
            "memory_note": None,
        },
        {
            "time_label": "00:14 — Alt Sources",
            "agent_color": "#ffb340",
            "agent_label": "🟠 Procurement Agent",
            "description": "2 alternative suppliers identified. SK Hynix 65% qty. Micron Japan 45% qty. Dual-source required.",
            "data": "query_suppliers(supplier_breach) · evaluate_spot_buy()",
            "memory_note": "📚 Historical: Taiwan Drought Jul 2022 — dual-source Samsung+MediaTek zero stockout",
        },
        {
            "time_label": "01:10 — Monte Carlo",
            "agent_color": "#00e676",
            "agent_label": "🟢 Finance Agent",
            "description": "100-iteration simulation on blended supplier cost. P90: $540K. Certification window 6h.",
            "data": "run_monte_carlo(100) · blended_cost(SK_Hynix+Micron)",
            "memory_note": None,
        },
        {
            "time_label": "02:30 — Spec Review",
            "agent_color": "#9b5de5",
            "agent_label": "🟣 Sales Agent",
            "description": "NVIDIA requires spec certification before substitution acceptance. 6h cert window offered. No extension granted.",
            "data": "query_contract_terms() · spec_cert_window: 6h",
            "memory_note": None,
        },
        {
            "time_label": "03:55 — Risk Flagged",
            "agent_color": "#ff3b5c",
            "agent_label": "🔴 Risk Agent (Devil's Advocate)",
            "description": "NVIDIA Friday 4pm cert cutoff window. If cert misses Friday, next slot is Monday — 72h slip. Trigger cert process immediately.",
            "data": "risk: certification-deadline · severity: high · mitigation: immediate_cert_trigger",
            "memory_note": None,
        },
        {
            "time_label": "04:45 — Approved & Executed",
            "agent_color": "#00e676",
            "agent_label": "✅ VP Operations",
            "description": "Dual-source plan approved. SK Hynix primary, Micron bridge. NVIDIA cert triggered. $20K contingency reserve added.",
            "data": "option: dual_source · cost: $510K · savings: $420K · CI: 87%",
            "memory_note": None,
        },
    ],
}


def _get_hardcoded_audit(scenario_str: str) -> list[dict]:
    """Return scenario-appropriate hardcoded audit trail (better than a single static list)."""
    return _HARDCODED_AUDIT_BY_SCENARIO.get(scenario_str, _HARDCODED_AUDIT_BY_SCENARIO["port_strike"])


# ─────────────────────────────────────────────────────────────────────────
# Route: GET /api/runs/{run_id}/decision-matrix
# ─────────────────────────────────────────────────────────────────────────

@router.get("/runs/{run_id}/decision-matrix")
async def get_decision_matrix(run_id: str):
    """
    Return the live decision matrix for a run.

    Data source priority:
      1. Redis run state (fastest, live during an active run)
      2. In-memory orchestrator._runs (same process, instant)
      3. TursoDB runs.context_json (persisted, survives restarts)
      4. Graceful empty defaults (run not yet started / too early)

    Response shape
    ──────────────
    {
      "run_id": "...",
      "scenario": "port_strike",
      "recommended": "hybrid",
      "options": [
        {
          "name": "Air Freight",
          "option_key": "air_lax",
          "cost": 500000,
          "time": "24h",
          "risk": 2,
          "esg": "high",
          "customer": "None",
          "recommended": false
        },
        ...
      ],
      "mc_stats": {
        "mean": 280000, "p10": 241000, "p90": 318000,
        "ci": 0.94, "distribution": [...], "saved_vs_air": 220000
      },
      "approval": {
        "option": "hybrid",
        "label": "Hybrid Route — 60% Air / 40% Sea",
        "cost_usd": 280000,
        "reserve_usd": 20000,
        "delivery_hours": 36,
        "confidence": 0.94
      }
    }
    """
    run = orchestrator.get_run(run_id)
    if not run:
        run = await redis_client.get_run_state(run_id)
    if not run:
        try:
            import db.turso_client as turso_client
            if turso_client.is_configured():
                run = await turso_client.get_run(run_id)
        except Exception:
            pass
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    scenario_str = str(run.get("scenario", "port_strike"))
    # Normalize ScenarioType enum values
    if hasattr(scenario_str, "value"):
        scenario_str = scenario_str.value

    run_context: dict = run.get("context", {}) or {}

    # Build options from live context
    options = _build_options_from_context(run_context, scenario_str)

    # Monte Carlo stats
    mc_stats = _build_mc_stats(run_context)

    # Approval data (may not exist yet if run hasn't reached that phase)
    approval = run.get("approval_data") or {}

    # Recommended option — prefer what the orchestrator decided
    recommended = (
        approval.get("option")
        or run_context.get("finance", {}).get("recommended_option")
        or "hybrid"
    )

    return {
        "run_id":      run_id,
        "scenario":    scenario_str,
        "recommended": recommended,
        "options":     options,
        "mc_stats":    mc_stats,
        "approval":    approval,
    }


# ─────────────────────────────────────────────────────────────────────────
# Route: GET /api/runs/{run_id}/audit-trail
# ─────────────────────────────────────────────────────────────────────────

@router.get("/runs/{run_id}/audit-trail")
async def get_audit_trail(run_id: str):
    """
    Return the ordered audit trail for a run.

    In live-agent mode: returns AuditEvents published to Redis during the run.
    In hardcoded-replay mode: returns a scenario-appropriate generated audit trail
    (better than the single static port-strike list the frontend used to show).

    Response shape
    ──────────────
    {
      "run_id": "...",
      "scenario": "port_strike",
      "mode": "live" | "hardcoded",
      "items": [
        {
          "time_label":  "00:12 — Route Options",
          "agent_color": "#00d4ff",
          "agent_label": "🔵 Logistics Agent",
          "description": "3 options generated...",
          "data":        "check_freight_rates() · ...",
          "memory_note": "📚 Historical: ..."   // or null
        },
        ...
      ]
    }
    """
    run = orchestrator.get_run(run_id)
    if not run:
        run = await redis_client.get_run_state(run_id)
    if not run:
        try:
            import db.turso_client as turso_client
            if turso_client.is_configured():
                run = await turso_client.get_run(run_id)
        except Exception:
            pass
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    scenario_str = str(run.get("scenario", "port_strike"))
    if hasattr(scenario_str, "value"):
        scenario_str = scenario_str.value

    mode = run.get("mode", "hardcoded")

    # Live audit events are accumulated in run["audit_trail"] by publish_audit_event()
    live_items: list[dict] = run.get("audit_trail", [])

    if live_items:
        items = live_items
    else:
        # Fallback: scenario-specific generated trail (better than single static list)
        items = _get_hardcoded_audit(scenario_str)

    return {
        "run_id":   run_id,
        "scenario": scenario_str,
        "mode":     mode,
        "items":    items,
    }



# ── PDF export: GET /api/runs/{run_id}/audit-trail/pdf ────────────────────

@router.get("/runs/{run_id}/audit-trail/pdf", tags=["Audit"])
async def export_audit_trail_pdf(run_id: str):
    """Generate and stream a branded PDF of the audit trail."""
    run = orchestrator.get_run(run_id)
    if not run:
        run = await redis_client.get_run_state(run_id)
    if not run:
        try:
            import db.turso_client as turso_client
            if turso_client.is_configured():
                run = await turso_client.get_run(run_id)
        except Exception:
            pass
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    scenario_str = str(run.get("scenario", "port_strike"))
    if hasattr(scenario_str, "value"):
        scenario_str = scenario_str.value

    live_items: list[dict] = run.get("audit_trail", [])
    items = live_items if live_items else _get_hardcoded_audit(scenario_str)

    # ── Pull metrics — flat keys written by exec_complete take priority ──────
    # Fallback chain: flat run keys → nested context → scenario defaults
    ctx     = run.get("context", {}) or {}
    fin_ctx = ctx.get("finance", {}) or {}
    mc      = fin_ctx.get("mc_result", {}) or {}
    log_ctx = ctx.get("logistics", {}) or {}

    cost_usd  = (run.get("cost_usd")
                 or fin_ctx.get("hybrid_cost")
                 or log_ctx.get("cost_usd"))

    saved_usd = (run.get("saved_usd")
                 or run.get("saved"))

    # If still missing, derive saved from scenario penalty
    if not saved_usd and cost_usd:
        try:
            sc_key_tmp = ScenarioType(scenario_str)
            sc_tmp     = SCENARIO_DEFINITIONS.get(sc_key_tmp)
            if sc_tmp:
                saved_usd = max(sc_tmp.penalty_usd - cost_usd, 0)
        except Exception:
            pass

    confidence = (run.get("confidence")
                  or mc.get("confidence_interval")
                  or fin_ctx.get("confidence"))

    resolution_time = run.get("resolution_time")

    try:
        sc_key = ScenarioType(scenario_str)
        sc_def = SCENARIO_DEFINITIONS.get(sc_key)
        customer = sc_def.customer if sc_def else ""
    except Exception:
        customer = ""

    # Last-resort: fill from scenario definition so PDF never shows all dashes
    if not cost_usd or not saved_usd or not confidence:
        try:
            sc_key2 = ScenarioType(scenario_str)
            sc2     = SCENARIO_DEFINITIONS.get(sc_key2)
            if sc2:
                cost_usd      = cost_usd      or 280_000
                saved_usd     = saved_usd     or max(sc2.penalty_usd - (cost_usd or 280_000), 0)
                confidence    = confidence    or 0.94
                resolution_time = resolution_time or "~4m 00s"
        except Exception:
            pass

    run_meta = {
        "customer":        customer,
        "cost_usd":        cost_usd,
        "saved_usd":       saved_usd,
        "resolution_time": resolution_time,
        "confidence":      confidence,
    }

    pdf_bytes = generate_audit_pdf(run_id, scenario_str, items, run_meta)
    filename  = f"chainguardai-audit-{run_id[:8]}-{scenario_str}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


# ── Episodic Memory endpoint ───────────────────────────────────────────────

@router.get("/memory", tags=["Memory"])
async def list_episodic_memory(
    sort_by: str = "date_label",
    order: str = "desc",
):
    """
    GET /api/memory

    Returns all rows from the episodic_memory table, newest first by default.

    Query params
    ────────────
    sort_by : memory_key | scenario_type | date_label | cost_usd |
              saved_usd  | confidence          (default: date_label)
    order   : asc | desc                       (default: desc)

    Falls back to in-memory seed data when TursoDB is not configured.
    """
    import db.turso_client as turso_client
    memories = await turso_client.list_all_memories(sort_by=sort_by, order=order)
    return {
        "total":    len(memories),
        "sort_by":  sort_by,
        "order":    order,
        "memories": memories,
    }
