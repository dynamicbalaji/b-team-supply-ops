"""
agents/sales.py  — Phase 3 updated
───────────────
Sales Agent — activates after Finance + Logistics consensus.

Phase 3: contract terms and SLA amendment appear as rich cards in chat.
"""

from models import AgentId, AgentStatus, ScenarioType
from scenarios import SCENARIO_DEFINITIONS
from tools.suppliers import query_contract_terms, draft_sla_amendment
from agents.base import (
    publish_state, publish_msg, publish_tool_result,
    stream_gemini, elapsed,
)


PERSONA = """You are the Sales Agent in a real-time supply chain crisis resolution system.
You are part of a 5-agent team negotiating the fastest, safest resolution to a P0 crisis.

Your personality:
- You own the customer relationship. You protect it above everything else.
- Confident and reassuring. You know your customer and what they'll accept.
- You negotiate SLA amendments in real time and confirm results immediately.
- You report facts: extension hours, penalty status, allocation benefit.
- No more than 3 sentences. No bullets. Chat message style.
- When the customer confirms, you close immediately. Speak with certainty.
"""


def _build_prompt(sc, contract, hybrid_hours, hybrid_cost):
    ext_hours  = contract.get("extension_hours", 36)
    ext_ok     = contract.get("extension_accepted", True)
    pen_waived = contract.get("penalty_waived", True)
    q3         = contract.get("q3_priority_benefit", "")
    notes      = contract.get("notes", "")
    status = (
        f"{sc.customer} confirmed {ext_hours}h extension. Penalty {'waived' if pen_waived else 'AT RISK'}."
        if ext_ok else f"{sc.customer} has NOT confirmed extension. Penalty risk remains."
    )
    return f"""{PERSONA}

CRISIS: {sc.description}
CUSTOMER: {sc.customer}

CONTRACT STATUS: {status}
Q3 ALLOCATION BENEFIT: {q3 or 'Not available.'}
PROPOSED DELIVERY: hybrid route — {hybrid_hours}h / ${hybrid_cost // 1000}K
CUSTOMER NOTES: {notes}

Write your message to ALL agents.
Confirm the customer's decision (extension hours, penalty status, Q3 benefit if applicable).
State that the hybrid {hybrid_hours}h timeline fits the amended SLA.
2-3 sentences. Speak as if you just got off the phone."""


async def run(run_id, scenario, run_context, start_time):
    sc = SCENARIO_DEFINITIONS[scenario]
    logistics    = run_context.get("logistics", {})
    hybrid_cost  = logistics.get("cost_usd", 253_000)
    hybrid_hours = logistics.get("transit_hours", 36)

    # 1. Activate
    await publish_state(run_id, AgentId.SALES, AgentStatus.ACTIVATING,
                        tool="📡 broadcast_received()", pulsing=True)

    # 2. Query contract terms — emits contract card bubble
    await publish_state(run_id, AgentId.SALES, AgentStatus.NEGOTIATING,
                        tool="📋 query_contract_terms()", pulsing=True)
    contract = await query_contract_terms(scenario)
    await publish_tool_result(run_id, AgentId.SALES, "query_contract_terms", contract)

    # 3. Draft SLA amendment — emits amendment card bubble
    amendment = await draft_sla_amendment(
        scenario=scenario,
        extension_hours=contract.get("extension_hours", 36),
        new_delivery_plan=f"Hybrid 60/40 route — {hybrid_hours}h ETA, ${hybrid_cost // 1000}K",
    )
    await publish_tool_result(run_id, AgentId.SALES, "draft_sla_amendment", amendment)

    # 4. Stream Gemini
    response_text = await stream_gemini(
        run_id, AgentId.SALES,
        _build_prompt(sc, contract, hybrid_hours, hybrid_cost),
        emit_tokens=True,
    )
    await publish_msg(run_id, AgentId.SALES,
                      from_label="SALES", to_label="→ ALL",
                      timestamp=elapsed(start_time), css_class="as_",
                      text=response_text,
                      tools=["📋 query_contract_terms()", "📝 draft_sla_amendment()"])

    # 5. Consensus
    await publish_state(run_id, AgentId.SALES, AgentStatus.CONSENSUS,
                        tool="✅ sla_confirmed()", confidence=0.97, pulsing=False)

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
