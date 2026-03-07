"""
agents/sales.py
───────────────
Sales Agent — activates after Finance + Logistics reach rough consensus.

Flow:
  1. Query contract terms for the customer
  2. Draft SLA amendment
  3. Stream Gemini negotiation message
  4. Publish CONSENSUS → 97% confidence (customer confirmed)
"""

from models import AgentId, AgentStatus, ScenarioType
from scenarios import SCENARIO_DEFINITIONS
from tools.suppliers import query_contract_terms, draft_sla_amendment
from agents.base import (
    publish_state, publish_msg, publish_tool,
    stream_gemini, elapsed,
)


PERSONA = """You are the Sales Agent in a real-time supply chain crisis resolution system.
You are part of a 5-agent team negotiating the fastest, safest resolution to a P0 crisis.

Your personality:
- You own the customer relationship. You protect it above everything else.
- You are confident and reassuring — you know your customer and you know what they'll accept.
- You negotiate SLA amendments in real time and confirm results immediately.
- You report facts: extension hours, penalty status, allocation benefits.
- No more than 3 sentences. No bullets. Chat message style.
- When the customer confirms, you close immediately. Speak with certainty.
"""


def _build_prompt(
    scenario_desc: str,
    customer: str,
    contract: dict,
    hybrid_hours: int,
    hybrid_cost: int,
) -> str:
    ext_accepted = contract.get("extension_accepted", True)
    ext_hours = contract.get("extension_hours", 36)
    penalty_waived = contract.get("penalty_waived", True)
    q3_benefit = contract.get("q3_priority_benefit", "")
    notes = contract.get("notes", "")

    status = (
        f"{customer} confirmed {ext_hours}h extension. Penalty waived."
        if ext_accepted and penalty_waived
        else f"{customer} has not confirmed extension. Penalty risk remains."
    )

    return f"""{PERSONA}

CRISIS: {scenario_desc}
CUSTOMER: {customer}

CONTRACT STATUS: {status}
Q3 ALLOCATION: {q3_benefit or 'Not available.'}
PROPOSED DELIVERY: {hybrid_hours}h hybrid route at ${hybrid_cost // 1000}K
CUSTOMER NOTES: {notes}

Write your message addressed to ALL agents.
Confirm the customer's decision (extension hours, penalty status).
State that the hybrid timeline fits the new SLA.
Keep it to 2-3 sentences. Speak as if you just got off the phone with the customer."""


async def run(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
) -> dict:
    """
    Executes the Sales agent.
    Called after Finance + Logistics reach consensus on cost.
    """
    sc = SCENARIO_DEFINITIONS[scenario]
    logistics = run_context.get("logistics", {})
    hybrid_cost = logistics.get("cost_usd", 253_000)
    hybrid_hours = logistics.get("transit_hours", 36)

    # ── 1. Activate ──────────────────────────────────────────────────────
    await publish_state(
        run_id, AgentId.SALES, AgentStatus.ACTIVATING,
        tool="📡 broadcast_received()", pulsing=True,
    )

    # ── 2. Query contract terms ───────────────────────────────────────────
    await publish_state(
        run_id, AgentId.SALES, AgentStatus.NEGOTIATING,
        tool="📋 query_contract_terms()", pulsing=True,
    )

    contract = await query_contract_terms(scenario)
    await publish_tool(run_id, AgentId.SALES, "query_contract_terms", contract)

    # ── 3. Draft amendment ────────────────────────────────────────────────
    amendment = await draft_sla_amendment(
        scenario=scenario,
        extension_hours=contract.get("extension_hours", 36),
        new_delivery_plan=f"Hybrid 60/40 route — {hybrid_hours}h delivery, ${hybrid_cost // 1000}K",
    )
    await publish_tool(run_id, AgentId.SALES, "draft_sla_amendment", amendment)

    # ── 4. Stream negotiation message ─────────────────────────────────────
    prompt = _build_prompt(
        scenario_desc=sc.description,
        customer=sc.customer,
        contract=contract,
        hybrid_hours=hybrid_hours,
        hybrid_cost=hybrid_cost,
    )

    response_text = await stream_gemini(
        run_id, AgentId.SALES, prompt, emit_tokens=True
    )

    await publish_msg(
        run_id, AgentId.SALES,
        from_label="SALES",
        to_label="→ ALL",
        timestamp=elapsed(start_time),
        css_class="as_",
        text=response_text,
        tools=["📋 query_contract_terms()", "📝 draft_sla_amendment()"],
    )

    # ── 5. Confirm consensus ──────────────────────────────────────────────
    await publish_state(
        run_id, AgentId.SALES, AgentStatus.CONSENSUS,
        tool="✅ sla_confirmed()",
        confidence=0.97,
        pulsing=False,
    )

    output = {
        "contract":       contract,
        "amendment":      amendment,
        "customer":       sc.customer,
        "extension_hours": contract.get("extension_hours", 36),
        "penalty_waived": contract.get("penalty_waived", True),
        "response_text":  response_text,
        "consensus":      True,
    }
    run_context["sales"] = output
    return output
