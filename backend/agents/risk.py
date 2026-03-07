"""
agents/risk.py
──────────────
Thin shim — all logic lives in graph/risk_agent_graph.py.

Public API (run) is preserved so orchestrator_graph.py and any other
callers require zero modification.
"""

from graph.risk_agent_graph import run_risk_agent


async def run(run_id, scenario, run_context, start_time):
    """Delegate to the LangGraph risk subgraph."""
    await run_risk_agent(run_id, scenario, run_context, start_time)
    return run_context.get("risk", {})
