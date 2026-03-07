"""
graph/orchestrator_graph.py
───────────────────────────

Phase 1 LangGraph migration: a minimal orchestrator graph that wraps the
existing live Gemini orchestrator.

For now this graph has a single node which calls
agents.orchestrator_live.run_live_scenario(). This lets us introduce
LangGraph into the codebase without changing any external behaviour:

  - FastAPI routes in main.py still call orchestrator.run_scenario().
  - orchestrator.run_scenario() still invokes run_live_scenario() (we
    will switch it to this graph in a later phase).
  - Redis SSE events and Turso writes are still produced by the
    existing orchestrator + agents.

Later phases will replace this "single node wrapper" with a richer
StateGraph that encodes all phases and agent rounds explicitly.
"""

from __future__ import annotations

import time
from typing import Any

from langgraph.graph import StateGraph

from models import RunStatus, ScenarioType
from orchestrator import get_run, set_run_status
from agents.orchestrator_live import run_live_scenario
from .state import RunGraphState


async def _run_live_scenario_node(state: RunGraphState) -> RunGraphState:
    """
    Graph node that delegates to the existing live orchestrator.

    It:
      - Sets the run status to RUNNING (defensive; orchestrator.run_scenario
        already does this in normal flows).
      - Calls agents.orchestrator_live.run_live_scenario(), which:
          * drives all multi-agent behaviour,
          * emits SSE events via Redis,
          * persists run state / memories via Turso.
      - Reads back the final status from orchestrator.get_run() so the
        graph state reflects where the run ended up.
    """
    run_id = state.get("run_id")
    scenario = state.get("scenario")

    if not run_id or scenario is None:
        # This should not happen if run_scenario_graph() is used correctly.
        return state

    # Ensure the high-level status is marked as running.
    set_run_status(run_id, RunStatus.RUNNING)

    # Delegate to the existing live orchestrator.
    await run_live_scenario(run_id, scenario, set_run_status)

    # Read back the final status from the in-memory run registry, if present.
    run = get_run(run_id)
    if run and "status" in run:
        state["status"] = run["status"]
    else:
        # Fallback: if we cannot see a run record, assume it failed.
        state["status"] = RunStatus.FAILED

    # NOTE: The current live orchestrator keeps run_context internal and only
    # stores a safe summary in Redis/Turso. In later phases we will plumb the
    # full context into the LangGraph state; for now we leave run_context as-is.
    return state


def _build_orchestrator_graph() -> Any:
    """
    Construct and compile the minimal orchestrator StateGraph.

    The graph has a single node:
      entry → "run_live_scenario" → end
    """
    graph = StateGraph(RunGraphState)
    graph.add_node("run_live_scenario", _run_live_scenario_node)
    graph.set_entry_point("run_live_scenario")
    # With a single node graph the entry point is also the terminal node.
    compiled = graph.compile()
    return compiled


_GRAPH_APP = _build_orchestrator_graph()


async def run_scenario_graph(
    run_id: str,
    scenario: ScenarioType,
) -> RunGraphState:
    """
    Public entry point for running a scenario via LangGraph.

    This function is intentionally not wired into orchestrator.run_scenario()
    yet. It can be used in parallel with the existing orchestrator for
    experimentation, and will become the primary code path in a later phase.
    """
    initial_state: RunGraphState = {
        "run_id": run_id,
        "scenario": scenario,
        "status": RunStatus.PENDING,
        "run_context": {},
        "started_at": time.time(),
    }
    final_state: RunGraphState = await _GRAPH_APP.ainvoke(initial_state)
    return final_state


__all__ = ["run_scenario_graph", "RunGraphState"]

