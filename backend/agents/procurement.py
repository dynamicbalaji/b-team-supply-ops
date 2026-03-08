"""
agents/procurement.py
─────────────────────
Procurement Agent — runs parallel to Logistics in Round 1.

This module is now a thin shim.  All logic lives in
graph/procurement_agent_graph.py as a LangGraph subgraph.

The public API (run, acknowledge) is preserved unchanged so
orchestrator_graph.py and any other callers require zero modification.
"""

from core.models import AgentId, AgentStatus
from agents.base import publish_state
from graph.procurement_agent_graph import run_procurement_agent


async def run(run_id, scenario, run_context, start_time):
    """
    Delegate entirely to the LangGraph subgraph.

    Returns the procurement output dict — identical shape to the previous
    implementation so orchestrator_graph continues to work without changes.
    """
    await run_procurement_agent(run_id, scenario, run_context, start_time)
    return run_context.get("procurement", {})


async def acknowledge(run_id, run_context, start_time):
    await publish_state(run_id, AgentId.PROCUREMENT, AgentStatus.DONE,
                        tool="✅ acknowledged()", confidence=0.71, pulsing=False)
    run_context["procurement"]["consensus"] = True
