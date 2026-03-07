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

from models import (
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
        name="Customs Delay — Shanghai",
        description="Regulatory hold on component exports from Shenzhen to LAX.",
        crisis_title="$8M component shipment",
        crisis_detail="held · Customs — Shenzhen → LAX · Risk: $1.5M penalty + production halt",
        penalty_usd=1_500_000,
        deadline_hours=36,
        budget_cap_usd=400_000,
        shipment_value_usd=8_000_000,
        customer="Samsung Electronics",
    ),

    ScenarioType.SUPPLIER_BREACH: ScenarioDefinition(
        id=ScenarioType.SUPPLIER_BREACH,
        name="Supplier Bankruptcy — Taiwan",
        description="Primary Taiwan fab has filed for bankruptcy mid-order.",
        crisis_title="$20M Taiwan fab order",
        crisis_detail="cancelled · Supplier bankruptcy · Risk: $5M replacement cost + 90-day delay",
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
                text=(
                    f"Crisis P0: SC-2024-8891 blocked at Long Beach. "
                    f"Budget cap ${sc.budget_cap_usd // 1000}K. "
                    f"Deadline {sc.deadline_hours}h. Begin parallel evaluation."
                ),
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
                    "air_lax":    {"cost": 450_000, "hours": 24, "risk": "low"},
                    "spot_dallas":{"cost": 380_000, "hours": 12, "risk": "medium"},
                    "hybrid":     {"cost": 253_000, "hours": 36, "risk": "medium"},
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
                    "Option A: Air via LAX — $450K / 24h / Low risk.<br>"
                    "Recalled March 2024 LA strike — hybrid saved $180K then."
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

        # ── t=3000ms : Procurement spots Dallas option ────────────────────
        {
            "delay_ms": 3000,
            "event": AgentStateEvent(
                agent=AgentId.PROCUREMENT, status=AgentStatus.QUERYING,
                tool='🏭 query_suppliers("dallas")', pulsing=True,
            ).model_dump(),
        },
        {
            "delay_ms": 3050,
            "event": ToolEvent(
                agent=AgentId.PROCUREMENT,
                tool="query_suppliers",
                result={
                    "location": "Dallas TX",
                    "cost": 380_000,
                    "quantity_pct": 80,
                    "cert_hours": 4,
                    "risk": "medium",
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
                    "Option B: Spot buy Dallas — $380K / 12h / Med risk. "
                    "Only 80% quantity available. Cert: 4h."
                ),
                tools=['🏭 query_suppliers("dallas")'],
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
                    "LAX ground crew unconfirmed during active strike. "
                    "Single point of failure in Hybrid plan. "
                    "Recommend Hour-20 backup trigger to Tucson air route."
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
                    "⚠ Consensus challenge: LAX ground crew unconfirmed. "
                    "Single point of failure. Recommend Hour-20 backup trigger "
                    "to Tucson route."
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
                    "Risk acknowledged. Adding +$20K contingency for Tucson backup. "
                    "Final recommendation: Hybrid $280K + $20K reserve. 94% CI. "
                    "Proposing approval."
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
            "event": ApprovalRequiredEvent(
                option="hybrid",
                label="Hybrid Route — 60% Air / 40% Sea",
                cost_usd=280_000,
                reserve_usd=20_000,
                delivery_hours=36,
                confidence=0.94,
                detail="$280K + $20K reserve · 36h delivery · Backup trigger H20 · Apple: ✓ · Confidence: 94%",
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

def get_execution_steps() -> list[dict]:
    """
    Events emitted after the human clicks APPROVE.
    Delays are relative to the moment approve is called.
    """
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
                route="✈ Freight booked → Austin TX",
            ).model_dump(),
        },
        {
            "delay_ms": 200,
            "event": ExecutionEvent(
                agent=AgentId.LOGISTICS,
                from_label="✈ LOGISTICS", css_class="al",
                timestamp="04:32",
                text="Freight booked: LAX → Austin TX · FX-2024-8891 · ETA 36h",
            ).model_dump(),
        },
        {
            "delay_ms": 900,
            "event": ExecutionEvent(
                agent=AgentId.SALES,
                from_label="📧 SALES", css_class="as_",
                timestamp="04:33",
                text="Apple notified — 36h extension confirmed · Q3 priority allocation logged",
            ).model_dump(),
        },
        {
            "delay_ms": 1600,
            "event": ExecutionEvent(
                agent=AgentId.FINANCE,
                from_label="💰 FINANCE", css_class="af",
                timestamp="04:34",
                text="Budget released: $280K · Contingency $20K · PO #F-7741 issued",
            ).model_dump(),
        },
        {
            "delay_ms": 2300,
            "event": ExecutionEvent(
                agent=AgentId.PROCUREMENT,
                from_label="🚫 PROCUREMENT", css_class="ap",
                timestamp="04:35",
                text="Dallas spot order cancelled · Tucson backup scheduled for Hour 20",
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
                saved_usd=220_000,
                message_count=9,
            ).model_dump(),
        },
    ]
