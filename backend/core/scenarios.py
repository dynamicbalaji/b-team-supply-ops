"""
scenarios.py
────────────
Two things live here:

1. SCENARIO_DEFINITIONS  — static metadata for the 3 selectable scenarios
2. get_hardcoded_steps() — the full ordered event sequence for Phase 1.
                           Phase 2 replaces this with live Gemini output.
                           Phase 1 streams these with realistic delays so
                           the frontend looks identical to the final build.

Each step is a dict:
  delay_ms : int   — milliseconds after scenario start to emit this event
  event    : dict  — the SSE event payload (matches models.py shapes)
"""

from core.models import (
    ScenarioType, ScenarioDefinition, AgentId, AgentStatus,
    PhaseEvent, AgentStateEvent, MessageEvent, ToolEvent,
    RiskActivatedEvent, ApprovalRequiredEvent, MapUpdateEvent,
    ExecutionEvent, CompleteEvent,
)


# ── 1. Scenario Definitions ──────────────────────────────────────────────

SCENARIO_DEFINITIONS: dict[ScenarioType, ScenarioDefinition] = {

    ScenarioType.PORT_STRIKE: ScenarioDefinition(
        id=ScenarioType.PORT_STRIKE,
        name="Port Strike — Long Beach",
        description="ILWU strike blocking all container movement at Port of Long Beach.",
        crisis_title="$12M semiconductor shipment",
        crisis_detail="blocked · Port of Long Beach · Risk: $2M penalty + $50M Apple contract",
        penalty_usd=2_000_000,
        deadline_hours=48,
        budget_cap_usd=500_000,
        shipment_value_usd=12_000_000,
        customer="Apple Inc.",
    ),

    ScenarioType.CUSTOMS_DELAY: ScenarioDefinition(
        id=ScenarioType.CUSTOMS_DELAY,
        name="Customs Delay — Shenzhen",
        description="GACC regulatory hold on component exports from Shenzhen — shipment cannot clear for LAX.",
        crisis_title="$8M component shipment",
        crisis_detail="held · Shenzhen Customs · Risk: $1.5M penalty + Samsung production halt",
        penalty_usd=1_500_000,
        deadline_hours=36,
        budget_cap_usd=400_000,
        shipment_value_usd=8_000_000,
        customer="Samsung Electronics",
    ),

    ScenarioType.SUPPLIER_BREACH: ScenarioDefinition(
        id=ScenarioType.SUPPLIER_BREACH,
        name="Supplier Bankruptcy — Taiwan",
        description="Primary Taiwan fab (ChipTech) has filed Chapter 11 mid-order. Replacement sourcing required.",
        crisis_title="$20M Taiwan fab order",
        crisis_detail="cancelled · ChipTech bankruptcy · Risk: $5M replacement cost + 90-day delay",
        penalty_usd=5_000_000,
        deadline_hours=72,
        budget_cap_usd=800_000,
        shipment_value_usd=20_000_000,
        customer="NVIDIA",
    ),
}


# ── 2. Hardcoded event steps (Phase 1) ───────────────────────────────────
#
# delay_ms values mirror the wireframe STEPS[] array exactly so the
# frontend animation timing feels the same whether running hardcoded
# (Phase 1) or live Gemini (Phase 2+).


# ── Scenario-specific message helpers ────────────────────────────────────

_SCENARIO_IDS = {
    ScenarioType.PORT_STRIKE:     "SC-2024-8891",
    ScenarioType.CUSTOMS_DELAY:   "SC-2024-4423",
    ScenarioType.SUPPLIER_BREACH: "SC-2024-7701",
}

_SCENARIO_LOCATIONS = {
    ScenarioType.PORT_STRIKE:     "Port of Long Beach (ILWU Strike)",
    ScenarioType.CUSTOMS_DELAY:   "Shenzhen Customs — GACC Hold",
    ScenarioType.SUPPLIER_BREACH: "Hsinchu Fab, Taiwan (ChipTech bankruptcy)",
}


def _orchestrator_broadcast(sc) -> str:
    sid = _SCENARIO_IDS.get(sc.id, "SC-2024-0000")
    loc = _SCENARIO_LOCATIONS.get(sc.id, "unknown location")
    return (
        f"Crisis P0: {sid} {sc.crisis_title} {sc.crisis_detail.split('·')[0].strip()}. "
        f"Budget cap ${sc.budget_cap_usd // 1000}K. "
        f"Deadline {sc.deadline_hours}h. Begin parallel evaluation."
    )


def _procurement_last_message(sc) -> str:
    """Scenario-specific final procurement execution message."""
    if sc.id == ScenarioType.PORT_STRIKE:
        return "Dallas spot buy cancelled (80% qty only) · Hybrid 60/40 air+sea confirmed · Long Beach diversion logged"
    elif sc.id == ScenarioType.CUSTOMS_DELAY:
        return "Shenzhen alternate broker engaged · Busan reroute confirmed · Samsung Dallas notified of ETA"
    else:  # SUPPLIER_BREACH
        return "ChipTech order formally cancelled · SK Hynix Suwon alt-source confirmed · NVIDIA spec certification in progress"


def _logistics_exec_message(sc) -> str:
    """Scenario-specific logistics execution confirmation."""
    if sc.id == ScenarioType.PORT_STRIKE:
        return "Hybrid route booked: 60% air via LAX + 40% sea via Oakland → Apple Cupertino · ETA 36h · Hour-20 Tucson backup armed"
    elif sc.id == ScenarioType.CUSTOMS_DELAY:
        return "Air freight rerouted: Shenzhen → Busan → LAX via expedited customs broker · Ground to Samsung Dallas · ETA 28h"
    else:  # SUPPLIER_BREACH
        return "SK Hynix alt-source confirmed: Suwon → ICN → LAX → NVIDIA Santa Clara · ETA 22h · Spec cert running parallel"


def _sales_exec_message(sc) -> str:
    """Scenario-specific sales notification message."""
    if sc.id == ScenarioType.PORT_STRIKE:
        return f"{sc.customer} (Cupertino) notified — 36h extension confirmed · Q3 priority allocation logged · Zero penalty"
    elif sc.id == ScenarioType.CUSTOMS_DELAY:
        return f"{sc.customer} (Dallas) notified — 28h revised ETA confirmed · Force majeure invoked · Penalty waived"
    else:  # SUPPLIER_BREACH
        return f"{sc.customer} (Santa Clara) notified — SK Hynix alt-source approved · Spec cert in 6h · SLA amendment issued"


def _finance_exec_message(sc, cost_usd: int = 280_000) -> str:
    """Scenario-specific finance budget release message."""
    if sc.id == ScenarioType.PORT_STRIKE:
        return f"Budget released: ${cost_usd // 1000}K · Contingency $20K · PO #F-7741 issued"
    elif sc.id == ScenarioType.CUSTOMS_DELAY:
        return f"Budget released: ${cost_usd // 1000}K · Broker fee $15K · PO #F-7742 issued"
    else:  # SUPPLIER_BREACH
        return f"Budget released: ${cost_usd // 1000}K · Premium surcharge $40K · PO #F-7743 issued"


def get_hardcoded_steps(scenario: ScenarioType) -> list[dict]:
    """
    Returns the ordered list of SSE events for a scenario.
    Each item: {"delay_ms": int, "event": dict}
    """

    sc = SCENARIO_DEFINITIONS[scenario]

    steps = [

        # ── t=0ms : Orchestrator broadcasts ─────────────────────────────
        {
            "delay_ms": 0,
            "event": PhaseEvent(phase=0, status="done").model_dump(),
        },
        {
            "delay_ms": 50,
            "event": PhaseEvent(phase=1, status="active").model_dump(),
        },
        {
            "delay_ms": 100,
            "event": AgentStateEvent(
                agent=AgentId.LOGISTICS, status=AgentStatus.ACTIVATING,
                tool="📡 broadcast_received()", pulsing=True,
            ).model_dump(),
        },
        {
            "delay_ms": 120,
            "event": AgentStateEvent(
                agent=AgentId.FINANCE, status=AgentStatus.ACTIVATING,
                tool="📡 broadcast_received()", pulsing=True,
            ).model_dump(),
        },
        {
            "delay_ms": 140,
            "event": AgentStateEvent(
                agent=AgentId.PROCUREMENT, status=AgentStatus.ACTIVATING,
                tool="📡 broadcast_received()", pulsing=True,
            ).model_dump(),
        },
        {
            "delay_ms": 160,
            "event": AgentStateEvent(
                agent=AgentId.SALES, status=AgentStatus.ACTIVATING,
                tool="📡 broadcast_received()", pulsing=True,
            ).model_dump(),
        },
        {
            "delay_ms": 200,
            "event": MessageEvent(
                agent=AgentId.ORCHESTRATOR,
                from_label="ORCHESTRATOR", to_label="→ ALL",
                timestamp="00:00", css_class="orc",
                text=_orchestrator_broadcast(sc),
                tools=[],
            ).model_dump(),
        },
        {
            "delay_ms": 250,
            "event": MapUpdateEvent(
                status="AGENTS ACTIVE", status_color="#ffb340",
                route="Evaluating routes",
            ).model_dump(),
        },

        # ── t=1500ms : Logistics proposes routes ─────────────────────────
        {
            "delay_ms": 1500,
            "event": PhaseEvent(phase=1, status="done").model_dump(),
        },
        {
            "delay_ms": 1520,
            "event": PhaseEvent(phase=2, status="active").model_dump(),
        },
        {
            "delay_ms": 1540,
            "event": AgentStateEvent(
                agent=AgentId.LOGISTICS, status=AgentStatus.PROPOSING,
                tool="📦 check_freight_rates()", pulsing=True,
            ).model_dump(),
        },
        {
            "delay_ms": 1560,
            "event": ToolEvent(
                agent=AgentId.LOGISTICS,
                tool="check_freight_rates",
                result={
                    "air_lax":     {"cost": 450_000, "hours": 24, "risk": "low",    "route": "Shanghai → LAX (100% air freight)"},
                    "sea_oakland": {"cost": 190_000, "hours": 72, "risk": "high",   "route": "Shanghai → Port of Oakland (sea, ILWU solidarity risk)"},
                    "hybrid":      {"cost": 253_000, "hours": 36, "risk": "medium", "route": "60% air via LAX + 40% sea via Oakland"},
                },
            ).model_dump(),
        },
        {
            "delay_ms": 1600,
            "event": ToolEvent(
                agent=AgentId.LOGISTICS,
                tool="memory_recall",
                result={
                    "match": "LA_port_strike_2024",
                    "outcome": "hybrid",
                    "saved_usd": 180_000,
                    "notes": "Hybrid 60/40 resolved in 38h during ILWU action Mar 2024",
                },
            ).model_dump(),
        },
        {
            "delay_ms": 1650,
            "event": MessageEvent(
                agent=AgentId.LOGISTICS,
                from_label="LOGISTICS", to_label="→ ORCH",
                timestamp="00:12", css_class="al",
                text=(
                    "Option A: 100% Air via LAX — $450K / 24h / Low risk.<br>"
                    "Option B: 100% Sea via Oakland — $190K / 72h / High risk (ILWU solidarity action).<br>"
                    "Recalled March 2024 LA strike — hybrid 60/40 saved $180K then. Recommending Option C."
                ),
                tools=["📦 check_freight_rates()", '📚 memory_recall("LA_2024")'],
            ).model_dump(),
        },
        {
            "delay_ms": 1700,
            "event": MapUpdateEvent(
                status="EVALUATING", status_color="#ffb340",
                route="✈ LAX route evaluated",
            ).model_dump(),
        },

        # ── t=3000ms : Procurement checks Dallas domestic supplier ────────────────────
        {
            "delay_ms": 3000,
            "event": AgentStateEvent(
                agent=AgentId.PROCUREMENT, status=AgentStatus.QUERYING,
                tool='🏭 query_suppliers("domestic_backup")', pulsing=True,
            ).model_dump(),
        },
        {
            "delay_ms": 3050,
            "event": ToolEvent(
                agent=AgentId.PROCUREMENT,
                tool="query_suppliers",
                result={
                    "supplier": "Texas Semiconductor Warehouse",
                    "location": "Dallas, TX (domestic backup)",
                    "cost": 380_000,
                    "quantity_pct": 80,
                    "cert_hours": 4,
                    "risk": "medium",
                    "note": "80% of required qty in stock — cannot fulfill full order",
                },
            ).model_dump(),
        },
        {
            "delay_ms": 3100,
            "event": MessageEvent(
                agent=AgentId.PROCUREMENT,
                from_label="PROCUREMENT", to_label="→ ORCH",
                timestamp="00:31", css_class="ap",
                text=(
                    "Option D: Domestic spot buy — Texas Semiconductor Warehouse, Dallas TX. "
                    "$380K / 12h lead time / 80% qty only. "
                    "Cannot fulfill full Apple order. Recommend routing solution instead."
                ),
                tools=['🏭 query_suppliers("domestic_backup")'],
            ).model_dump(),
        },

        # ── t=5000ms : Finance challenges Logistics assumption ────────────
        {
            "delay_ms": 5000,
            "event": AgentStateEvent(
                agent=AgentId.FINANCE, status=AgentStatus.CALCULATING,
                tool="📊 run_monte_carlo(100)", pulsing=True,
            ).model_dump(),
        },
        {
            "delay_ms": 5050,
            "event": ToolEvent(
                agent=AgentId.FINANCE,
                tool="run_monte_carlo",
                result={
                    "iterations": 100,
                    "mean": 280_000,
                    "p10": 241_000,
                    "p90": 318_000,
                    "confidence_interval": 0.94,
                    # 22 buckets for D3 chart — pre-computed bell curve
                    "distribution": [
                        3, 6, 10, 16, 26, 36, 50, 65, 77,
                        87, 92, 87, 80, 70, 58, 45, 33, 24,
                        16, 10, 6, 3,
                    ],
                },
            ).model_dump(),
        },
        {
            "delay_ms": 5100,
            "event": ToolEvent(
                agent=AgentId.FINANCE,
                tool="query_customs_rates",
                result={"expedited_strike_surcharge_usd": 50_000, "standard_usd": 12_000},
            ).model_dump(),
        },
        {
            "delay_ms": 5150,
            "event": MessageEvent(
                agent=AgentId.FINANCE,
                from_label="FINANCE", to_label="→ LOGISTICS",
                timestamp="01:04", css_class="af",
                text=(
                    "Your $450K — does that include expedited customs at LAX "
                    "during strike conditions? Challenging that assumption."
                ),
                tools=["📊 run_monte_carlo(100)", "💰 query_customs_rates()"],
            ).model_dump(),
        },

        # ── t=7000ms : Logistics revises, proposes Hybrid ─────────────────
        {
            "delay_ms": 7000,
            "event": AgentStateEvent(
                agent=AgentId.LOGISTICS, status=AgentStatus.REVISING,
                tool="📦 recalculate_route()", confidence=0.58, pulsing=True,
            ).model_dump(),
        },
        {
            "delay_ms": 7100,
            "event": MessageEvent(
                agent=AgentId.LOGISTICS,
                from_label="LOGISTICS", to_label="→ FINANCE",
                timestamp="01:18", css_class="al",
                text=(
                    "Confirmed. Customs +$50K. Total air: $500K — at budget limit. "
                    "Recommend Hybrid 60/40: $280K / 36h instead."
                ),
                tools=[],
            ).model_dump(),
        },

        # ── t=9000ms : Finance + Logistics reach consensus ────────────────
        {
            "delay_ms": 9000,
            "event": AgentStateEvent(
                agent=AgentId.FINANCE, status=AgentStatus.CONSENSUS,
                tool="✅ propose_consensus()", confidence=0.94, pulsing=False,
            ).model_dump(),
        },
        {
            "delay_ms": 9100,
            "event": AgentStateEvent(
                agent=AgentId.LOGISTICS, status=AgentStatus.CONSENSUS,
                tool="✅ hybrid_confirmed()", confidence=0.88, pulsing=False,
            ).model_dump(),
        },

        # ── t=10000ms : Sales negotiates Apple SLA ────────────────────────
        {
            "delay_ms": 10000,
            "event": AgentStateEvent(
                agent=AgentId.SALES, status=AgentStatus.NEGOTIATING,
                tool="📋 query_contract_terms()", pulsing=True,
            ).model_dump(),
        },
        {
            "delay_ms": 10050,
            "event": ToolEvent(
                agent=AgentId.SALES,
                tool="query_contract_terms",
                result={
                    "customer": "Apple Inc.",
                    "penalty_clause": "2M USD per 48h breach",
                    "extension_accepted": True,
                    "extension_hours": 36,
                    "q3_priority_available": True,
                },
            ).model_dump(),
        },
        {
            "delay_ms": 10100,
            "event": MessageEvent(
                agent=AgentId.SALES,
                from_label="SALES", to_label="→ ALL",
                timestamp="02:18", css_class="as_",
                text=(
                    "Apple accepts 36h delay + Q3 priority allocation. "
                    "Zero financial penalty confirmed. Hybrid timeline fits perfectly."
                ),
                tools=["📋 query_contract_terms()", "📝 draft_sla_amendment()"],
            ).model_dump(),
        },
        {
            "delay_ms": 10200,
            "event": AgentStateEvent(
                agent=AgentId.SALES, status=AgentStatus.CONSENSUS,
                tool="✅ sla_confirmed()", confidence=0.97, pulsing=False,
            ).model_dump(),
        },

        # ── t=12500ms : Risk Agent challenges consensus ───────────────────
        {
            "delay_ms": 12500,
            "event": RiskActivatedEvent(
                message=(
                    {
                        ScenarioType.PORT_STRIKE: (
                            "LAX ground crew availability unconfirmed during active ILWU strike. "
                            "Single point of failure if 60% air leg is grounded. "
                            "Recommend Hour-20 backup trigger to Tucson Air Hub as alternate."
                        ),
                        ScenarioType.CUSTOMS_DELAY: (
                            "LAX bonded warehouse capacity unconfirmed during peak clearance window. "
                            "Risk of 12h holding delay on arrival even after Busan reroute. "
                            "Recommend pre-booking alternate bonded facility at Ontario, CA."
                        ),
                        ScenarioType.SUPPLIER_BREACH: (
                            "SK Hynix NVIDIA spec certification timeline unconfirmed — 6h estimate may slip. "
                            "Single point of failure on Suwon → LAX route if cert fails. "
                            "Recommend parallel cert of Micron Japan (Hiroshima) as backup source."
                        ),
                    }[scenario]
                ),
            ).model_dump(),
        },
        {
            "delay_ms": 12550,
            "event": MessageEvent(
                agent=AgentId.RISK,
                from_label="RISK AGENT", to_label="→ ALL ⚠",
                timestamp="03:45", css_class="ar",
                text=(
                    {
                        ScenarioType.PORT_STRIKE: (
                            "⚠ Consensus challenge: LAX ground crew unconfirmed during strike. "
                            "Single point of failure on air leg. Recommend Hour-20 backup trigger "
                            "to Tucson Air Hub."
                        ),
                        ScenarioType.CUSTOMS_DELAY: (
                            "⚠ Consensus challenge: LAX bonded warehouse at peak capacity. "
                            "12h holding risk on arrival. Recommend pre-booking backup bonded "
                            "facility at Ontario, CA."
                        ),
                        ScenarioType.SUPPLIER_BREACH: (
                            "⚠ Consensus challenge: SK Hynix cert timeline unconfirmed — 6h may slip. "
                            "Recommend parallel certification of Micron Japan (Hiroshima) "
                            "as backup source for NVIDIA spec."
                        ),
                    }[scenario]
                ),
                tools=[],
            ).model_dump(),
        },
        {
            "delay_ms": 12600,
            "event": MapUpdateEvent(
                status="RISK FLAGGED", status_color="#ff3b5c",
            ).model_dump(),
        },

        # ── t=14500ms : Finance absorbs risk, final proposal ──────────────
        {
            "delay_ms": 14500,
            "event": AgentStateEvent(
                agent=AgentId.FINANCE, status=AgentStatus.FINALISING,
                tool="✅ propose_consensus()", pulsing=True,
            ).model_dump(),
        },
        {
            "delay_ms": 14600,
            "event": MessageEvent(
                agent=AgentId.FINANCE,
                from_label="FINANCE", to_label="→ ALL",
                timestamp="04:01", css_class="af",
                text=(
                    {
                        ScenarioType.PORT_STRIKE: (
                            "Risk acknowledged. Adding +$20K contingency for Tucson backup trigger. "
                            "Final: Hybrid $280K + $20K reserve · 36h delivery · 94% CI. Proposing approval."
                        ),
                        ScenarioType.CUSTOMS_DELAY: (
                            "Risk acknowledged. Adding +$15K contingency for Ontario CA bonded warehouse backup. "
                            "Final: Busan reroute $180K + $15K reserve · 28h delivery · 91% CI. Proposing approval."
                        ),
                        ScenarioType.SUPPLIER_BREACH: (
                            "Risk acknowledged. Adding +$40K contingency for Micron Japan parallel cert. "
                            "Final: SK Hynix alt-source $510K + $40K reserve · 22h delivery · 89% CI. Proposing approval."
                        ),
                    }[scenario]
                ),
                tools=["✅ propose_consensus()"],
            ).model_dump(),
        },
        {
            "delay_ms": 14700,
            "event": AgentStateEvent(
                agent=AgentId.PROCUREMENT, status=AgentStatus.DONE,
                tool="✅ acknowledged()", confidence=0.71, pulsing=False,
            ).model_dump(),
        },

        # ── t=16000ms : Approval required ────────────────────────────────
        {
            "delay_ms": 16000,
            "event": PhaseEvent(phase=2, status="done").model_dump(),
        },
        {
            "delay_ms": 16050,
            "event": PhaseEvent(phase=3, status="active").model_dump(),
        },
        {
            "delay_ms": 16100,
            "event": (
                {
                    ScenarioType.PORT_STRIKE: ApprovalRequiredEvent(
                        option="hybrid",
                        label="Hybrid Route — 60% Air LAX + 40% Sea Oakland",
                        cost_usd=280_000,
                        reserve_usd=20_000,
                        delivery_hours=36,
                        confidence=0.94,
                        detail="$280K + $20K reserve · 36h · Hour-20 Tucson backup · Apple Cupertino: ✓ · CI: 94%",
                    ),
                    ScenarioType.CUSTOMS_DELAY: ApprovalRequiredEvent(
                        option="air_busan",
                        label="Air Reroute — Shenzhen → Busan → LAX → Samsung Dallas",
                        cost_usd=180_000,
                        reserve_usd=15_000,
                        delivery_hours=28,
                        confidence=0.91,
                        detail="$180K + $15K reserve · 28h · Ontario CA bonded backup · Samsung Dallas: ✓ · CI: 91%",
                    ),
                    ScenarioType.SUPPLIER_BREACH: ApprovalRequiredEvent(
                        option="alt_supplier",
                        label="Alt-Source — SK Hynix Suwon → LAX → NVIDIA Santa Clara",
                        cost_usd=510_000,
                        reserve_usd=40_000,
                        delivery_hours=22,
                        confidence=0.89,
                        detail="$510K + $40K reserve · 22h · Micron Japan parallel cert · NVIDIA Santa Clara: ✓ · CI: 89%",
                    ),
                }[scenario]
            ).model_dump(),
        },
        {
            "delay_ms": 16150,
            "event": MapUpdateEvent(
                status="AWAITING APPROVAL", status_color="#ffb340",
            ).model_dump(),
        },
    ]

    return steps


# ── Execution cascade (fires after APPROVE button) ───────────────────────

def get_execution_steps(scenario: ScenarioType = ScenarioType.PORT_STRIKE) -> list[dict]:
    """
    Events emitted after the human clicks APPROVE.
    Delays are relative to the moment approve is called.
    Scenario-specific messages are derived from the passed scenario.
    """
    sc = SCENARIO_DEFINITIONS[scenario]
    _exec_route = {
        ScenarioType.PORT_STRIKE:     "✈ Hybrid booked · LAX + Oakland → Apple Cupertino",
        ScenarioType.CUSTOMS_DELAY:   "✈ Air rerouted · Busan → LAX → Samsung Dallas",
        ScenarioType.SUPPLIER_BREACH: "✈ SK Hynix confirmed · Suwon → LAX → NVIDIA Santa Clara",
    }[scenario]
    return [
        {
            "delay_ms": 0,
            "event": PhaseEvent(phase=3, status="done").model_dump(),
        },
        {
            "delay_ms": 50,
            "event": PhaseEvent(phase=4, status="active").model_dump(),
        },
        {
            "delay_ms": 100,
            "event": MapUpdateEvent(
                status="EXECUTING", status_color="#00e676",
                route=_exec_route,
            ).model_dump(),
        },
        {
            "delay_ms": 200,
            "event": ExecutionEvent(
                agent=AgentId.LOGISTICS,
                from_label="✈ LOGISTICS", css_class="al",
                timestamp="04:32",
                text=_logistics_exec_message(sc),
            ).model_dump(),
        },
        {
            "delay_ms": 900,
            "event": ExecutionEvent(
                agent=AgentId.SALES,
                from_label="📧 SALES", css_class="as_",
                timestamp="04:33",
                text=_sales_exec_message(sc),
            ).model_dump(),
        },
        {
            "delay_ms": 1600,
            "event": ExecutionEvent(
                agent=AgentId.FINANCE,
                from_label="💰 FINANCE", css_class="af",
                timestamp="04:34",
                text=_finance_exec_message(sc),
            ).model_dump(),
        },
        {
            "delay_ms": 2300,
            "event": ExecutionEvent(
                agent=AgentId.PROCUREMENT,
                from_label="🚫 PROCUREMENT", css_class="ap",
                timestamp="04:35",
                text=_procurement_last_message(sc),
            ).model_dump(),
        },
        {
            "delay_ms": 3200,
            "event": AgentStateEvent(
                agent=AgentId.LOGISTICS, status=AgentStatus.COMPLETE,
                tool="✅ done", confidence=0.88, pulsing=False,
            ).model_dump(),
        },
        {
            "delay_ms": 3250,
            "event": AgentStateEvent(
                agent=AgentId.FINANCE, status=AgentStatus.COMPLETE,
                tool="✅ done", confidence=0.94, pulsing=False,
            ).model_dump(),
        },
        {
            "delay_ms": 3300,
            "event": AgentStateEvent(
                agent=AgentId.PROCUREMENT, status=AgentStatus.COMPLETE,
                tool="✅ done", confidence=0.71, pulsing=False,
            ).model_dump(),
        },
        {
            "delay_ms": 3350,
            "event": AgentStateEvent(
                agent=AgentId.SALES, status=AgentStatus.COMPLETE,
                tool="✅ done", confidence=0.97, pulsing=False,
            ).model_dump(),
        },
        {
            "delay_ms": 3400,
            "event": PhaseEvent(phase=4, status="done").model_dump(),
        },
        {
            "delay_ms": 3420,
            "event": PhaseEvent(phase=5, status="active").model_dump(),
        },
        {
            "delay_ms": 3450,
            "event": MapUpdateEvent(
                status="DELIVERED ✅", status_color="#00e676",
            ).model_dump(),
        },
        {
            "delay_ms": 3500,
            "event": CompleteEvent(
                resolution_time="4m 32s",
                cost_usd=280_000,
                saved_usd=max(sc.penalty_usd - 280_000, 0),
                message_count=9,
            ).model_dump(),
        },
        {
            "delay_ms": 3600,
            "event": PhaseEvent(phase=5, status="done").model_dump(),
        },
    ]
