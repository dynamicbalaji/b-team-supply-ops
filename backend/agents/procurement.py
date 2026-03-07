"""
agents/procurement.py
─────────────────────
Procurement Agent — runs parallel with Logistics in the first round.

Flow:
  1. Activate → query_suppliers() tool
  2. Stream Gemini proposal (spot buy option with quantity caveat)
  3. After consensus reached: DONE state + acknowledge
"""

from models import AgentId, AgentStatus, ScenarioType
from scenarios import SCENARIO_DEFINITIONS
from tools.suppliers import query_suppliers
from agents.base import (
    publish_state, publish_msg, publish_tool,
    stream_gemini, elapsed,
)


PERSONA = """You are the Procurement Agent in a real-time supply chain crisis resolution system.
You are part of a 5-agent team negotiating the fastest, safest resolution to a P0 crisis.

Your personality:
- You know the supplier market cold. You give cost, availability, and quantity facts.
- You are honest about limitations — if a supplier can only cover 80%, you say so upfront.
- You are practical and efficient. You don't editorialize; you state the facts and move on.
- You flag risks around supplier certifications and quantity gaps.
- 3 sentences max. No bullets. No headers. Chat message format.
"""


def _build_prompt(
    scenario_desc: str,
    customer: str,
    budget_cap: int,
    suppliers: list[dict],
) -> str:
    sup_lines = "\n".join(
        f"  {s['name']} ({s['location']}): "
        f"${s['total_cost_usd'] // 1000 if s['total_cost_usd'] else 0}K / "
        f"{s['transit_hours']}h / {s['stock_quantity_pct']}% qty / "
        f"{s['risk_level']} risk. {s['notes']}"
        for s in suppliers if s["total_cost_usd"] > 0
    )

    if not sup_lines:
        sup_lines = "  No spot buy suppliers available for this scenario."

    return f"""{PERSONA}

CRISIS: {scenario_desc}
CUSTOMER: {customer}
BUDGET CAP: ${budget_cap // 1000}K

SUPPLIER QUERY RESULTS:
{sup_lines}

Write your message to the Orchestrator.
Report the best spot buy option with its cost, transit time, quantity constraint, and certification time.
Flag if quantity is below 100% and what it means for the order.
Keep it to 2-3 sentences."""


async def run(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
) -> dict:
    """
    Executes the Procurement agent. Runs parallel to Logistics.
    """
    sc = SCENARIO_DEFINITIONS[scenario]

    # ── 1. Activate ──────────────────────────────────────────────────────
    await publish_state(
        run_id, AgentId.PROCUREMENT, AgentStatus.ACTIVATING,
        tool="📡 broadcast_received()", pulsing=True,
    )

    # ── 2. Query suppliers ────────────────────────────────────────────────
    await publish_state(
        run_id, AgentId.PROCUREMENT, AgentStatus.QUERYING,
        tool='🏭 query_suppliers("dallas")', pulsing=True,
    )

    suppliers = await query_suppliers(scenario, location_hint="dallas")
    await publish_tool(run_id, AgentId.PROCUREMENT, "query_suppliers", suppliers)

    # ── 3. Build prompt and stream ────────────────────────────────────────
    prompt = _build_prompt(
        scenario_desc=sc.description,
        customer=sc.customer,
        budget_cap=sc.budget_cap_usd,
        suppliers=suppliers,
    )

    response_text = await stream_gemini(
        run_id, AgentId.PROCUREMENT, prompt, emit_tokens=True
    )

    await publish_msg(
        run_id, AgentId.PROCUREMENT,
        from_label="PROCUREMENT",
        to_label="→ ORCH",
        timestamp=elapsed(start_time),
        css_class="ap",
        text=response_text,
        tools=['🏭 query_suppliers("dallas")'],
    )

    # ── 4. Store output ───────────────────────────────────────────────────
    primary = next((s for s in suppliers if s["total_cost_usd"] > 0), {})
    output = {
        "suppliers":       suppliers,
        "primary_option":  primary,
        "cost_usd":        primary.get("total_cost_usd", 380_000),
        "quantity_pct":    primary.get("stock_quantity_pct", 80),
        "cert_hours":      primary.get("cert_hours", 4),
        "response_text":   response_text,
        "consensus":       False,
    }
    run_context["procurement"] = output
    return output


async def acknowledge(
    run_id: str,
    run_context: dict,
    start_time: float,
) -> None:
    """
    Called when the hybrid consensus is reached.
    Procurement acknowledges it can cancel the spot buy and arm the backup.
    """
    await publish_state(
        run_id, AgentId.PROCUREMENT, AgentStatus.DONE,
        tool="✅ acknowledged()",
        confidence=0.71,
        pulsing=False,
    )
    run_context["procurement"]["consensus"] = True
