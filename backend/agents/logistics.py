"""
agents/logistics.py
───────────────────
Thin shim — all logic lives in graph/logistics_agent_graph.py.

Public API (run, revise) is preserved so orchestrator_graph.py and any
other callers require zero modification.
"""

from core.models import AgentId, AgentStatus
from graph.logistics_agent_graph import run_logistics_agent, revise_logistics_agent


async def run(run_id, scenario, run_context, start_time):
    """Delegate to the LangGraph run subgraph."""
    await run_logistics_agent(run_id, scenario, run_context, start_time)
    return run_context.get("logistics", {})


async def revise(run_id, scenario, run_context, start_time, challenge, customs_surcharge):
    """Delegate to the LangGraph revise subgraph."""
    await revise_logistics_agent(
        run_id, scenario, run_context, start_time, challenge, customs_surcharge
    )
    return run_context.get("logistics", {})
