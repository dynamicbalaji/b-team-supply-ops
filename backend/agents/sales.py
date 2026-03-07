"""
agents/sales.py
───────────────
Thin shim — all logic lives in graph/sales_agent_graph.py.

Public API (run) is preserved so orchestrator_graph.py and any other
callers require zero modification.
"""

from graph.sales_agent_graph import run_sales_agent


async def run(run_id, scenario, run_context, start_time):
    """Delegate to the LangGraph sales subgraph."""
    await run_sales_agent(run_id, scenario, run_context, start_time)
    return run_context.get("sales", {})
