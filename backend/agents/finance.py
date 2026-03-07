"""
agents/finance.py
─────────────────
Thin shim — all logic lives in graph/finance_agent_graph.py.

Public API (run, propose_consensus) is preserved so orchestrator_graph.py
and any other callers require zero modification.
"""

from graph.finance_agent_graph import run_finance_agent, propose_consensus_finance_agent


async def run(run_id, scenario, run_context, start_time):
    """Delegate to the LangGraph run subgraph (Round-2 challenge flow)."""
    await run_finance_agent(run_id, scenario, run_context, start_time)
    return run_context.get("finance", {})


async def propose_consensus(run_id, scenario, run_context, start_time, reserve_usd=20_000):
    """Delegate to the LangGraph consensus subgraph (Round-5 authorisation)."""
    await propose_consensus_finance_agent(
        run_id, scenario, run_context, start_time, reserve_usd=reserve_usd
    )
    return run_context.get("finance", {})
