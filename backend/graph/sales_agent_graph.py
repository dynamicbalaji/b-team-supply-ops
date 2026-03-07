"""
graph/sales_agent_graph.py
───────────────────────────
Sales Agent as a single LangGraph subgraph.

Graph nodes (Round 3 — SLA negotiation):
  activate → query_contract → draft_amendment → generate → store → END

Public entry point (signature identical to agents/sales.py):
  run_sales_agent(run_id, scenario, run_context, start_time) -> dict
"""

from __future__ import annotations

import time
from typing import Any, Dict

from langgraph.graph import StateGraph, END

from models import AgentId, AgentStatus, ScenarioType
from scenarios import SCENARIO_DEFINITIONS
from tools.suppliers import query_contract_terms, draft_sla_amendment
from agents.base import (
    publish_state,
    publish_msg,
    publish_tool_result,
    stream_gemini,
    elapsed,
)
from graph.state import RunGraphState


# ── Agent-local state ─────────────────────────────────────────────────────

class SalesState(RunGraphState, total=False):
    """RunGraphState + Sales-private fields."""
    agent_id: AgentId
    sales_output: Dict[str, Any] | None


# ── Persona + prompt builder ──────────────────────────────────────────────

_PERSONA = """You are the Sales Agent in a real-time supply chain crisis resolution system.
You are part of a 5-agent team negotiating the fastest, safest resolution to a P0 crisis.

Your personality:
- You own the customer relationship. You protect it above everything else.
- Confident and reassuring. You know your customer and what they'll accept.
- You negotiate SLA amendments in real time and confirm results immediately.
- You report facts: extension hours, penalty status, allocation benefit.
- No more than 3 sentences. No bullets. Chat message style.
- When the customer confirms, you close immediately. Speak with certainty.
"""


def _build_prompt(sc, contract: dict, hybrid_hours: int, hybrid_cost: int) -> str:
    ext_hours  = contract.get("extension_hours", 36)
    ext_ok     = contract.get("extension_accepted", True)
    pen_waived = contract.get("penalty_waived", True)
    q3         = contract.get("q3_priority_benefit", "")
    notes      = contract.get("notes", "")
    status = (
        f"{sc.customer} confirmed {ext_hours}h extension. Penalty {'waived' if pen_waived else 'AT RISK'}."
        if ext_ok else
        f"{sc.customer} has NOT confirmed extension. Penalty risk remains."
    )
    return f"""{_PERSONA}

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


# ── Nodes ─────────────────────────────────────────────────────────────────

async def _node_activate(state: SalesState) -> SalesState:
    await publish_state(
        state["run_id"], AgentId.SALES, AgentStatus.ACTIVATING,
        tool="📡 broadcast_received()", pulsing=True,
    )
    return state


async def _node_query_contract(state: SalesState) -> SalesState:
    run_id   = state["run_id"]
    scenario = state["scenario"]

    await publish_state(run_id, AgentId.SALES, AgentStatus.NEGOTIATING,
                        tool="📋 query_contract_terms()", pulsing=True)
    contract = await query_contract_terms(scenario)
    await publish_tool_result(run_id, AgentId.SALES, "query_contract_terms", contract)

    rc = dict(state.get("run_context") or {})
    rc["_sales_contract"] = contract
    return {**state, "run_context": rc}


async def _node_draft_amendment(state: SalesState) -> SalesState:
    run_id   = state["run_id"]
    scenario = state["scenario"]

    rc           = state["run_context"]
    contract     = rc["_sales_contract"]
    logistics    = rc.get("logistics", {})
    hybrid_cost  = logistics.get("cost_usd", 253_000)
    hybrid_hours = logistics.get("transit_hours", 36)

    amendment = await draft_sla_amendment(
        scenario=scenario,
        extension_hours=contract.get("extension_hours", 36),
        new_delivery_plan=f"Hybrid 60/40 route — {hybrid_hours}h ETA, ${hybrid_cost // 1000}K",
    )
    await publish_tool_result(run_id, AgentId.SALES, "draft_sla_amendment", amendment)

    rc = dict(rc)
    rc["_sales_amendment"] = amendment
    return {**state, "run_context": rc}


async def _node_generate(state: SalesState) -> SalesState:
    run_id     = state["run_id"]
    scenario   = state["scenario"]
    started_at = state.get("started_at") or time.time()
    sc         = SCENARIO_DEFINITIONS[scenario]

    rc           = state["run_context"]
    contract     = rc["_sales_contract"]
    logistics    = rc.get("logistics", {})
    hybrid_cost  = logistics.get("cost_usd", 253_000)
    hybrid_hours = logistics.get("transit_hours", 36)

    response_text = await stream_gemini(
        run_id, AgentId.SALES,
        _build_prompt(sc, contract, hybrid_hours, hybrid_cost),
        emit_tokens=True,
    )
    await publish_msg(
        run_id, AgentId.SALES,
        from_label="SALES", to_label="→ ALL",
        timestamp=elapsed(started_at), css_class="as_",
        text=response_text,
        tools=["📋 query_contract_terms()", "📝 draft_sla_amendment()"],
    )
    await publish_state(
        run_id, AgentId.SALES, AgentStatus.CONSENSUS,
        tool="✅ sla_confirmed()", confidence=0.97, pulsing=False,
    )

    rc = dict(rc)
    rc["_sales_response_text"] = response_text
    return {**state, "run_context": rc}


async def _node_store(state: SalesState) -> SalesState:
    rc            = dict(state["run_context"])
    contract      = rc.pop("_sales_contract", {})
    amendment     = rc.pop("_sales_amendment", {})
    response_text = rc.pop("_sales_response_text", "")
    scenario      = state["scenario"]
    sc            = SCENARIO_DEFINITIONS[scenario]

    output = {
        "contract":        contract,
        "amendment":       amendment,
        "customer":        sc.customer,
        "extension_hours": contract.get("extension_hours", 36),
        "penalty_waived":  contract.get("penalty_waived", True),
        "response_text":   response_text,
        "consensus":       True,
    }
    rc["sales"] = output
    return {**state, "run_context": rc, "sales_output": output}


# ── Graph assembly ────────────────────────────────────────────────────────

def _build_graph():
    g = StateGraph(SalesState)
    g.add_node("activate",        _node_activate)
    g.add_node("query_contract",  _node_query_contract)
    g.add_node("draft_amendment", _node_draft_amendment)
    g.add_node("generate",        _node_generate)
    g.add_node("store",           _node_store)
    g.set_entry_point("activate")
    g.add_edge("activate",        "query_contract")
    g.add_edge("query_contract",  "draft_amendment")
    g.add_edge("draft_amendment", "generate")
    g.add_edge("generate",        "store")
    g.add_edge("store",           END)
    return g.compile()


_GRAPH = _build_graph()


# ── Public entry point ────────────────────────────────────────────────────

async def run_sales_agent(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
) -> dict:
    """Round-3 SLA negotiation. Mutates run_context in-place and returns it."""
    initial: SalesState = {
        "run_id":       run_id,
        "scenario":     scenario,
        "run_context":  dict(run_context),
        "started_at":   start_time,
        "agent_id":     AgentId.SALES,
        "sales_output": None,
    }
    final = await _GRAPH.ainvoke(initial)
    run_context.update(final["run_context"])
    return run_context
