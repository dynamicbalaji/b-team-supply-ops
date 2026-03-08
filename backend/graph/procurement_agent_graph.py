"""
graph/procurement_agent_graph.py
─────────────────────────────────
Procurement Agent as a standalone LangGraph subgraph.

This module re-implements the behaviour from agents/procurement.py as a
LangGraph StateGraph while keeping every SSE event shape and tool-result
format byte-for-byte identical to the original.  The public entry point
run_procurement_agent() matches the signature of the old agents/procurement.run()
so the orchestrator_graph can call either without modification.

Graph nodes
───────────
  activate      — publish ACTIVATING state (broadcast_received pill)
  query         — publish QUERYING state + call query_suppliers() + publish_tool_result()
  generate      — stream Gemini tokens + publish final MessageEvent
  store         — write structured output into run_context["procurement"]

State
─────
  ProcurementState extends RunGraphState with two agent-local fields:
    • agent_id         : always AgentId.PROCUREMENT (frozen on entry)
    • procurement_output: dict | None  (populated by the store node)

Reusable pattern
────────────────
  To convert another agent to a LangGraph subgraph:
    1. Define an AgentState TypedDict that extends RunGraphState.
    2. Create one node per logical step (activate → query/calculate → generate → store).
    3. Wire them with add_edge() — no conditional branching needed for single-path agents.
    4. Expose async run_<agent>_agent(run_id, scenario, run_context, start_time) -> dict
       that builds initial state, calls graph.arun(), and returns run_context.
    5. Replace the body of agents/<agent>.py::run() with a one-liner delegation.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from langgraph.graph import StateGraph, END

from core.models import AgentId, AgentStatus, ScenarioType
from core.scenarios import SCENARIO_DEFINITIONS
from tools.suppliers import query_suppliers
from agents.base import (
    publish_state,
    publish_msg,
    publish_tool_result,
    stream_gemini,
    elapsed,
)
from graph.state import RunGraphState


# ── Agent-local state ─────────────────────────────────────────────────────

class ProcurementState(RunGraphState, total=False):
    """
    RunGraphState + fields private to the Procurement subgraph.

    agent_id is pinned to AgentId.PROCUREMENT at graph entry and never
    mutated; it is stored here so every node can read it without importing
    AgentId directly.

    procurement_output is None until the store node writes it.
    """
    agent_id: AgentId
    procurement_output: Dict[str, Any] | None


# ── Prompt builder (unchanged from original) ─────────────────────────────

_PERSONA = """You are the Procurement Agent in a real-time supply chain crisis resolution system.
You are part of a 5-agent team negotiating the fastest, safest resolution to a P0 crisis.

Your personality:
- You know the supplier market cold. Cost, availability, and quantity — facts only.
- Honest about limitations. If a supplier covers only 80%, say so upfront.
- Practical and efficient. State the facts, move on.
- Flag risks around certification times and quantity gaps.
- 3 sentences max. No bullets. No headers. Chat message format.
"""


def _build_prompt(sc, suppliers: list[dict]) -> str:
    lines = "\n".join(
        f"  {s['name']} ({s['location']}): "
        f"${s['total_cost_usd'] // 1000 if s['total_cost_usd'] else 0}K / "
        f"{s['transit_hours']}h / {s['stock_quantity_pct']}% qty / "
        f"{s['cert_hours']}h cert / {s['risk_level']} risk. {s['notes']}"
        for s in suppliers if s["total_cost_usd"] > 0
    ) or "  No spot buy suppliers available."

    return f"""{_PERSONA}

CRISIS: {sc.description}
CUSTOMER: {sc.customer}
BUDGET CAP: ${sc.budget_cap_usd // 1000}K

SUPPLIER QUERY RESULTS:
{lines}

Write your message to the Orchestrator.
Report the best spot buy option: cost, transit, quantity percentage, cert time.
Flag if quantity < 100% and what it means operationally.
Keep it to 2-3 sentences."""


# ── Graph nodes ───────────────────────────────────────────────────────────

async def _node_activate(state: ProcurementState) -> ProcurementState:
    """
    Node: activate
    Publishes the ACTIVATING state so the agent card starts pulsing.
    Identical to step 1 of the original run().
    """
    await publish_state(
        state["run_id"],
        AgentId.PROCUREMENT,
        AgentStatus.ACTIVATING,
        tool="📡 broadcast_received()",
        pulsing=True,
    )
    return state


async def _node_query(state: ProcurementState) -> ProcurementState:
    """
    Node: query
    Publishes the QUERYING state, calls query_suppliers(), then publishes
    the rich tool-result bubble via publish_tool_result().

    The supplier list is stored in state so downstream nodes can read it
    without re-querying.
    """
    run_id = state["run_id"]
    scenario = state["scenario"]

    await publish_state(
        run_id,
        AgentId.PROCUREMENT,
        AgentStatus.QUERYING,
        tool='🏭 query_suppliers("dallas")',
        pulsing=True,
    )

    suppliers = await query_suppliers(scenario, location_hint="dallas")
    await publish_tool_result(run_id, AgentId.PROCUREMENT, "query_suppliers", suppliers)

    # Stash suppliers in run_context so _node_generate and _node_store can read them
    # without touching module-level state (keeps the graph re-entrant).
    run_context = dict(state.get("run_context") or {})
    run_context["_procurement_suppliers"] = suppliers

    return {**state, "run_context": run_context}


async def _node_generate(state: ProcurementState) -> ProcurementState:
    """
    Node: generate
    Streams Gemini tokens via stream_gemini() (emits TokenEvent per chunk)
    then publishes the final MessageEvent for the Procurement chat bubble.
    """
    run_id = state["run_id"]
    scenario = state["scenario"]
    started_at = state.get("started_at") or time.time()

    sc = SCENARIO_DEFINITIONS[scenario]
    suppliers: list[dict] = state["run_context"].get("_procurement_suppliers", [])

    response_text = await stream_gemini(
        run_id,
        AgentId.PROCUREMENT,
        _build_prompt(sc, suppliers),
        emit_tokens=True,
    )

    await publish_msg(
        run_id,
        AgentId.PROCUREMENT,
        from_label="PROCUREMENT",
        to_label="→ ORCH",
        timestamp=elapsed(started_at),
        css_class="ap",
        text=response_text,
        tools=['🏭 query_suppliers("dallas")'],
    )

    run_context = dict(state["run_context"])
    run_context["_procurement_response_text"] = response_text

    return {**state, "run_context": run_context}


async def _node_store(state: ProcurementState) -> ProcurementState:
    """
    Node: store
    Builds the structured procurement output dict and writes it to
    run_context["procurement"] — exactly matching what the original run()
    returned so every downstream consumer (orchestrator_graph, approval
    logic, etc.) continues to work unchanged.

    Also cleans the private _procurement_* staging keys from run_context.
    """
    run_context = dict(state["run_context"])

    suppliers: list[dict] = run_context.pop("_procurement_suppliers", [])
    response_text: str = run_context.pop("_procurement_response_text", "")

    primary = next((s for s in suppliers if s["total_cost_usd"] > 0), {})

    output: dict[str, Any] = {
        "suppliers":      suppliers,
        "primary_option": primary,
        "cost_usd":       primary.get("total_cost_usd", 380_000),
        "quantity_pct":   primary.get("stock_quantity_pct", 80),
        "cert_hours":     primary.get("cert_hours", 4),
        "response_text":  response_text,
        "consensus":      False,
    }

    run_context["procurement"] = output

    return {**state, "run_context": run_context, "procurement_output": output}


# ── Graph assembly ────────────────────────────────────────────────────────

def _build_graph() -> Any:
    """
    Constructs and compiles the Procurement StateGraph.

    The linear node chain mirrors the original procedural flow:
      activate → query → generate → store → END

    No conditional edges are needed for a single-path agent.
    Compile once at import time and reuse across all runs (thread-safe
    because LangGraph compiled graphs are stateless).
    """
    g: StateGraph = StateGraph(ProcurementState)

    g.add_node("activate", _node_activate)
    g.add_node("query",    _node_query)
    g.add_node("generate", _node_generate)
    g.add_node("store",    _node_store)

    g.set_entry_point("activate")
    g.add_edge("activate", "query")
    g.add_edge("query",    "generate")
    g.add_edge("generate", "store")
    g.add_edge("store",    END)

    return g.compile()


_GRAPH = _build_graph()


# ── Public entry point ────────────────────────────────────────────────────

async def run_procurement_agent(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
) -> dict:
    """
    Build an initial ProcurementState, run the compiled graph, and return
    the updated run_context.

    Signature is intentionally identical to the old agents/procurement.run()
    minus the self/module prefix so orchestrator_graph.py calls it the same way.

    Returns:
        The updated run_context dict (with run_context["procurement"] populated).
    """
    initial_state: ProcurementState = {
        "run_id":              run_id,
        "scenario":            scenario,
        "run_context":         dict(run_context),   # defensive copy; we return the final one
        "started_at":          start_time,
        "agent_id":            AgentId.PROCUREMENT,
        "procurement_output":  None,
    }

    final_state: ProcurementState = await _GRAPH.ainvoke(initial_state)

    # Propagate all changes the graph made back into the caller's run_context
    run_context.update(final_state["run_context"])

    return run_context
