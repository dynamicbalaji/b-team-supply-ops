"""
agents/procurement.py  — Phase 3 updated
─────────────────────
Procurement Agent — runs parallel to Logistics in Round 1.

Phase 3: query_suppliers() result appears as formatted supplier table bubble.
"""

from models import AgentId, AgentStatus, ScenarioType
from scenarios import SCENARIO_DEFINITIONS
from tools.suppliers import query_suppliers
from agents.base import (
    publish_state, publish_msg, publish_tool_result,
    stream_gemini, elapsed,
)


PERSONA = """You are the Procurement Agent in a real-time supply chain crisis resolution system.
You are part of a 5-agent team negotiating the fastest, safest resolution to a P0 crisis.

Your personality:
- You know the supplier market cold. Cost, availability, and quantity — facts only.
- Honest about limitations. If a supplier covers only 80%, say so upfront.
- Practical and efficient. State the facts, move on.
- Flag risks around certification times and quantity gaps.
- 3 sentences max. No bullets. No headers. Chat message format.
"""


def _build_prompt(sc, suppliers):
    lines = "\n".join(
        f"  {s['name']} ({s['location']}): "
        f"${s['total_cost_usd'] // 1000 if s['total_cost_usd'] else 0}K / "
        f"{s['transit_hours']}h / {s['stock_quantity_pct']}% qty / "
        f"{s['cert_hours']}h cert / {s['risk_level']} risk. {s['notes']}"
        for s in suppliers if s["total_cost_usd"] > 0
    ) or "  No spot buy suppliers available."

    return f"""{PERSONA}

CRISIS: {sc.description}
CUSTOMER: {sc.customer}
BUDGET CAP: ${sc.budget_cap_usd // 1000}K

SUPPLIER QUERY RESULTS:
{lines}

Write your message to the Orchestrator.
Report the best spot buy option: cost, transit, quantity percentage, cert time.
Flag if quantity < 100% and what it means operationally.
Keep it to 2-3 sentences."""


async def run(run_id, scenario, run_context, start_time):
    sc = SCENARIO_DEFINITIONS[scenario]

    # 1. Activate
    await publish_state(run_id, AgentId.PROCUREMENT, AgentStatus.ACTIVATING,
                        tool="📡 broadcast_received()", pulsing=True)

    # 2. Query suppliers — emits supplier table bubble
    await publish_state(run_id, AgentId.PROCUREMENT, AgentStatus.QUERYING,
                        tool='🏭 query_suppliers("dallas")', pulsing=True)
    suppliers = await query_suppliers(scenario, location_hint="dallas")
    await publish_tool_result(run_id, AgentId.PROCUREMENT, "query_suppliers", suppliers)

    # 3. Stream Gemini
    response_text = await stream_gemini(
        run_id, AgentId.PROCUREMENT,
        _build_prompt(sc, suppliers), emit_tokens=True,
    )
    await publish_msg(run_id, AgentId.PROCUREMENT,
                      from_label="PROCUREMENT", to_label="→ ORCH",
                      timestamp=elapsed(start_time), css_class="ap",
                      text=response_text,
                      tools=['🏭 query_suppliers("dallas")'])

    # 4. Store
    primary = next((s for s in suppliers if s["total_cost_usd"] > 0), {})
    output = {
        "suppliers":     suppliers,
        "primary_option": primary,
        "cost_usd":      primary.get("total_cost_usd", 380_000),
        "quantity_pct":  primary.get("stock_quantity_pct", 80),
        "cert_hours":    primary.get("cert_hours", 4),
        "response_text": response_text,
        "consensus":     False,
    }
    run_context["procurement"] = output
    return output


async def acknowledge(run_id, run_context, start_time):
    await publish_state(run_id, AgentId.PROCUREMENT, AgentStatus.DONE,
                        tool="✅ acknowledged()", confidence=0.71, pulsing=False)
    run_context["procurement"]["consensus"] = True
